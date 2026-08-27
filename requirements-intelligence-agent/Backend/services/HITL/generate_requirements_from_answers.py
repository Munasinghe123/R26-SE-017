import json
import re

from services.llm.llm import llm


GENERATE_REQUIREMENTS_PROMPT = """
You are a senior requirements analyst.

The client has reviewed software requirements and some changes created
ambiguities or conflicts.

The client was asked clarification questions and has now provided answers.

Your task is to convert the client's answers into precise software
requirements.

IMPORTANT:

1. Generate requirements from the CLIENT'S ANSWERS.

2. The answer is the source of truth for resolving the corresponding
   clarification.

3. Do not merely repeat the client's answer if it is conversational.
   Convert its meaning into a clear, concise software requirement.

4. Preserve the meaning of the client's answer.

5. Do not invent business rules, features, behavior, roles, constraints,
   or implementation details.

6. Only generate requirements related to the supplied clarification.

7. Each client answer may produce ZERO or ONE requirement.

8. If the client answer confirms that an existing requirement already
   covers the requested clarification, DO NOT generate a requirement.

9. If the client answer introduces or confirms new business behavior,
   generate exactly ONE requirement for that answer.

10. Preserve the requirement ID provided with the answer.

11. Existing requirements keep their original ID:
    - FR-1
    - FR-8
    - FR-20
    - NFR-1
    etc.

12. Newly added requirements keep their temporary ID:
    - new-1
    - new-2
    etc.

13. Never convert a temporary ID into an FR or NFR ID.

14. Never create a new ID.

15. Never use "new_id".

16. Do not classify requirements as FR or NFR.

17. Do not merge answers.

18. Do not split answers.

19. Do not include questions, explanations, reasoning, or analysis.

20. Return ONLY valid JSON.

OUTPUT FORMAT:

{
    "requirements": [
        {
            "id": "new-1",
            "text": "Customers receive WhatsApp notifications when their appointments are cancelled or rescheduled."
        }
    ]
}
"""


def parse_json_response(content: str):

    content = content.strip()

    content = re.sub(
        r"```json\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"```\s*",
        "",
        content
    )

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise json.JSONDecodeError(
            "No JSON object found",
            content,
            0
        )

    return json.loads(
        content[start:end + 1]
    )


def validate_generated_requirements(
    data,
    client_answers
):

    if not isinstance(data, dict):
        raise ValueError(
            "Generated requirements must be a JSON object."
        )

    requirements = data.get("requirements")

    if not isinstance(requirements, list):
        raise ValueError(
            "Response must contain a 'requirements' list."
        )

    expected_ids = {
        answer["requirement_id"]
        for answer in client_answers
    }

    returned_ids = [
        requirement.get("id")
        for requirement in requirements
    ]

    # ---------------------------------------------------------
    # Returned IDs must belong to the client answers.
    # But not every answer needs to produce a requirement.
    # ---------------------------------------------------------

    unexpected_ids = (
        set(returned_ids) - expected_ids
    )

    if unexpected_ids:
        raise ValueError(
            f"Unexpected generated requirement IDs: "
            f"{sorted(unexpected_ids)}"
        )

    # ---------------------------------------------------------
    # Check duplicates
    # ---------------------------------------------------------

    if len(returned_ids) != len(set(returned_ids)):
        raise ValueError(
            "Duplicate requirement IDs generated."
        )

    # ---------------------------------------------------------
    # Validate individual requirements
    # ---------------------------------------------------------

    for requirement in requirements:

        if not isinstance(requirement, dict):
            raise ValueError(
                "Each generated requirement must be an object."
            )

        requirement_id = requirement.get("id")
        text = requirement.get("text")

        if not isinstance(requirement_id, str):
            raise ValueError(
                "Generated requirement 'id' must be a string."
            )

        if not isinstance(text, str):
            raise ValueError(
                f"Generated requirement text must be a string "
                f"for {requirement_id}."
            )

        if not text.strip():
            raise ValueError(
                f"Generated requirement text cannot be empty "
                f"for {requirement_id}."
            )

    return True


def generate_requirements_from_answers(
    clarification_questions,
    client_answers,
    clarification_changes
):

    print(
        "\n========== GENERATING REQUIREMENTS FROM CLIENT ANSWERS =========="
    )

    # ---------------------------------------------------------
    # Prepare questions
    # ---------------------------------------------------------

    questions = clarification_questions.get(
        "questions",
        []
    )

    question_map = {
        question["id"]: question
        for question in questions
    }

    # ---------------------------------------------------------
    # Prepare input for LLM
    # ---------------------------------------------------------

    answer_inputs = []

    for answer in client_answers:

        question_id = answer["question_id"]
        requirement_id = answer["requirement_id"]

        question = question_map.get(
            question_id
        )

        if not question:
            raise ValueError(
                f"Question {question_id} "
                f"was not found."
            )

        answer_inputs.append({
            "question_id": question_id,
            "requirement_id": requirement_id,
            "question": question["question"],
            "answer": answer["answer"]
        })

    prompt = f"""
{GENERATE_REQUIREMENTS_PROMPT}

CLARIFICATION CHANGES:

{json.dumps(
    clarification_changes,
    indent=2,
    ensure_ascii=False
)}

CLIENT ANSWERS:

{json.dumps(
    answer_inputs,
    indent=2,
    ensure_ascii=False
)}
"""

    print(
        "\n========== CALLING LLM FOR ANSWER → REQUIREMENTS =========="
    )

    response = llm.invoke(prompt)

    content = response.content.strip()

    print(
        "\n========== RAW GENERATED REQUIREMENTS =========="
    )

    print(content)

    print(
        "================================================="
    )

    # ---------------------------------------------------------
    # Parse
    # ---------------------------------------------------------

    try:

        data = parse_json_response(
            content
        )

        print(
            "Generated requirements JSON parsing: SUCCESS"
        )

    except json.JSONDecodeError as e:

        print(
            "Generated requirements JSON parsing: FAILED"
        )

        print(
            "Error:",
            e
        )

        raise ValueError(
            "LLM returned invalid JSON "
            "for answer-generated requirements."
        )

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    print(
        "\n========== VALIDATING GENERATED REQUIREMENTS =========="
    )

    validate_generated_requirements(
        data,
        client_answers
    )

    print(
        "Generated requirements validation: SUCCESS"
    )

    print(
        "\n========== ANSWER-GENERATED REQUIREMENTS =========="
    )

    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "======================================================"
    )

    return data