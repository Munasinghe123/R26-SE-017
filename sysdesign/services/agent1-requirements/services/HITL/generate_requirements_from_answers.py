import json
import re

from services.llm import llm


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

10. Do not generate requirement IDs.

11. Do not classify requirements as functional or non-functional.

12. Do not merge answers.

13. Do not split answers.

14. Every generated requirement must contain the question_id of the
    clarification answer it belongs to.

15. Do not include requirement_id in the generated output.

16. Do not include questions, explanations, reasoning, or analysis.

17. Return ONLY valid JSON.

OUTPUT FORMAT:

{
    "requirements": [
        {
            "question_id": "Q-1",
            "text": "Staff can create appointments on behalf of customers."
        }
    ]
}
"""


def parse_json_response(content: str):

    content = content.strip()

    # 1. Search for markdown code block containing requirements
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            import json_repair
            data = json_repair.loads(match.group(1))
            if isinstance(data, dict) and "requirements" in data:
                return data
        except Exception:
            pass

    # 2. If content contains "requirements", find the enclosing JSON object
    if '"requirements"' in content:
        idx = content.rfind('"requirements"')
        req_start = content.rfind("{", 0, idx)
        if req_start != -1:
            try:
                import json_repair
                data = json_repair.loads(content[req_start:])
                if isinstance(data, dict) and "requirements" in data:
                    return data
            except Exception:
                pass

    # 3. Try json_repair on the whole string
    try:
        import json_repair
        data = json_repair.loads(content)
        if isinstance(data, dict):
            if "requirements" in data:
                return data
            if "question_id" in data or "id" in data:
                return {"requirements": [data]}
        elif isinstance(data, list):
            return {"requirements": data}
    except Exception:
        pass

    raise ValueError("LLM did not return a valid requirements object.")


def validate_generated_requirements(
    data,
    client_answers
):

    if not isinstance(data, dict):
        raise ValueError(
            "Generated requirements must be a JSON object."
        )

    requirements = data.get(
        "requirements"
    )

    if not isinstance(requirements, list):
        raise ValueError(
            "Response must contain a 'requirements' list."
        )

    # ---------------------------------------------------------
    # Expected question IDs
    # ---------------------------------------------------------

    expected_question_ids = {
        (answer.get("question_id") or answer.get("id"))
        for answer in client_answers
    }

    returned_question_ids = [
        requirement.get("question_id")
        for requirement in requirements
    ]

    # ---------------------------------------------------------
    # Returned question IDs must belong to client answers.
    # Not every answer needs to produce a requirement.
    # ---------------------------------------------------------

    unexpected_question_ids = (
        set(returned_question_ids)
        - expected_question_ids
    )

    if unexpected_question_ids:
        raise ValueError(
            f"Unexpected question IDs generated: "
            f"{sorted(unexpected_question_ids)}"
        )

    # ---------------------------------------------------------
    # Check duplicate question IDs
    #
    # One answer -> at most one requirement.
    # ---------------------------------------------------------

    if len(returned_question_ids) != len(
        set(returned_question_ids)
    ):
        raise ValueError(
            "Multiple requirements generated "
            "for the same client answer."
        )

    # ---------------------------------------------------------
    # Validate individual requirements
    # ---------------------------------------------------------

    for requirement in requirements:

        if not isinstance(requirement, dict):
            raise ValueError(
                "Each generated requirement must be an object."
            )

        question_id = requirement.get(
            "question_id"
        )

        text = requirement.get(
            "text"
        )

        if not isinstance(question_id, str):
            raise ValueError(
                "Generated requirement 'question_id' "
                "must be a string."
            )

        if not isinstance(text, str):
            raise ValueError(
                f"Generated requirement text must be a string "
                f"for {question_id}."
            )

        if not text.strip():
            raise ValueError(
                f"Generated requirement text cannot be empty "
                f"for {question_id}."
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

    if not client_answers:
        print("[generate_requirements_from_answers] No client answers to process (0 clarification answers).")
        return {"requirements": []}

    # ---------------------------------------------------------
    # Prepare questions
    # ---------------------------------------------------------

    questions = clarification_questions.get(
        "questions",
        []
    ) if isinstance(clarification_questions, dict) else (clarification_questions or [])

    question_map = {
        (question.get("id") or question.get("question_id")): question
        for question in questions
    }

    # ---------------------------------------------------------
    # Prepare input for LLM
    # ---------------------------------------------------------

    answer_inputs = []

    for answer in (client_answers or []):

        question_id = answer.get("question_id") or answer.get("id")
        requirement_id = answer.get("requirement_id") or answer.get("id")

        question = question_map.get(
            question_id
        )

        if not question:
            raise ValueError(
                f"Question {question_id} "
                f"was not found in {list(question_map.keys())}."
            )

        answer_inputs.append({
            "question_id": question_id,
            "requirement_id": requirement_id,
            "question": question.get("question", ""),
            "answer": answer.get("answer", "")
        })

    # ---------------------------------------------------------
    # Build prompt
    # ---------------------------------------------------------

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
        "\n========== CALLING LLM FOR ANSWER -> REQUIREMENTS =========="
    )

    response = llm.invoke(
        prompt
    )

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
        ) from e

    # ---------------------------------------------------------
    # Validate LLM output
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

    # ---------------------------------------------------------
    # Build requirement ID lookup
    #
    # IMPORTANT:
    # The ID comes from our application data,
    # NOT from the LLM.
    # ---------------------------------------------------------

    answer_id_map = {
        (answer.get("question_id") or answer.get("id")):
            (answer.get("requirement_id") or answer.get("id"))
        for answer in client_answers
    }

    # ---------------------------------------------------------
    # Attach original requirement IDs
    # ---------------------------------------------------------

    final_requirements = []

    for requirement in data["requirements"]:

        question_id = requirement[
            "question_id"
        ]

        requirement_id = answer_id_map.get(
            question_id
        )

        if requirement_id is None:
            raise ValueError(
                f"No requirement ID found for "
                f"question {question_id}."
            )

        final_requirements.append({
            "id": requirement_id,
            "text": requirement["text"]
        })

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    final_data = {
        "requirements": final_requirements
    }

    print(
        "\n========== ANSWER-GENERATED REQUIREMENTS =========="
    )

    print(
        json.dumps(
            final_data,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "======================================================"
    )

    return final_data