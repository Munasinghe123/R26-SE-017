import json
import re

from services.llm.llm import llm


QUESTION_GENERATION_PROMPT = """
You generate targeted business clarification questions
for a software requirements review.

The client has already reviewed the requirements.

Another component has already analyzed the client's changes
and identified the specific issues that require clarification.

Your job is to generate concise business questions that
resolve those identified issues.

RULES:

1. Questions must be understandable by a non-technical
   business client.

2. Do not use technical implementation terminology.

3. Do not ask about programming languages, databases,
   APIs, frameworks, architecture, or implementation.

4. Only ask questions directly related to the provided
   change and its identified issues.

5. Do not ask for information that is already explicitly
   provided.

6. Do not invent new features or assumptions.

7. For deleted requirements with issues, ask only what is
   necessary to determine the client's intended behavior.

8. For edited requirements with issues, ask only what is
   necessary to remove the identified ambiguity or
   unspecified behavior.

9. For newly added requirements with issues, ask only what
   is necessary to define the missing business behavior or
   resolve the identified conflict.

10. Do not question changes that are not present in the input.

11. Generate only the minimum number of questions necessary
    to resolve the identified issues.

12. Generate between 1 and 2 questions for each change that
    requires clarification.

13. Each question must directly address one or more of the
    provided issues.

14. Preserve the requirement identifier exactly as provided.

15. Use "id" as the only identifier field.

16. Do not use "id".

17. Return ONLY valid JSON.

OUTPUT:

{
    "questions": [
        {
            "id": "Q-1",
            "requirement_id": "FR-8",
            "question": "Business-oriented question",
            "reason": "Why this information is needed"
        }
    ]
}
"""


def parse_json_response(content: str):

    content = content.strip()

    # Remove markdown JSON fences if the LLM adds them
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
        raise ValueError(
            "LLM did not return a JSON object."
        )

    return json.loads(
        content[start:end + 1]
    )


def validate_questions(
    data,
    clarification_changes
):

    if not isinstance(data, dict):
        raise ValueError(
            "Question response must be a JSON object."
        )

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise ValueError(
            "Question response must contain a 'questions' list."
        )

    # ---------------------------------------------------------
    # Collect IDs that actually require clarification
    # ---------------------------------------------------------

    expected_ids = set()

    for change_type in (
        "edited",
        "deleted",
        "added"
    ):

        for change in clarification_changes.get(
            change_type,
            []
        ):

            expected_ids.add(
                change["id"]
            )

    # ---------------------------------------------------------
    # Validate questions
    # ---------------------------------------------------------

    question_ids = set()

    for question in questions:

        if not isinstance(question, dict):
            raise ValueError(
                "Each question must be an object."
            )

        question_id = question.get("id")
        requirement_id = question.get(
            "requirement_id"
        )
        text = question.get("question")
        reason = question.get("reason")

        if not isinstance(question_id, str):
            raise ValueError(
                "Each question must contain a string 'id'."
            )

        if not isinstance(
            requirement_id,
            str
        ):
            raise ValueError(
                "Each question must contain a string "
                "'requirement_id'."
            )

        if requirement_id not in expected_ids:
            raise ValueError(
                f"Question references requirement "
                f"'{requirement_id}', which does not "
                f"require clarification."
            )

        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                f"Invalid question for {requirement_id}."
            )

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"Invalid reason for {requirement_id}."
            )

        if question_id in question_ids:
            raise ValueError(
                f"Duplicate question ID: {question_id}"
            )

        question_ids.add(question_id)

    # ---------------------------------------------------------
    # Every clarification change must receive a question
    # ---------------------------------------------------------

    questioned_ids = {
        question["requirement_id"]
        for question in questions
    }

    missing_ids = expected_ids - questioned_ids

    if missing_ids:
        raise ValueError(
            f"No questions generated for clarification "
            f"changes: {sorted(missing_ids)}"
        )

    return True


def generate_targeted_questions(
    clarification_changes
):

    print(
        "\n========== GENERATING TARGETED QUESTIONS =========="
    )

    # ---------------------------------------------------------
    # Nothing requires clarification
    # ---------------------------------------------------------

    total_changes = sum(
        len(
            clarification_changes.get(
                change_type,
                []
            )
        )
        for change_type in (
            "edited",
            "deleted",
            "added"
        )
    )

    if total_changes == 0:

        print(
            "No changes require clarification."
        )

        return {
            "questions": []
        }

    # ---------------------------------------------------------
    # LLM receives ONLY problematic changes
    # ---------------------------------------------------------

    prompt = f"""
{QUESTION_GENERATION_PROMPT}

CHANGES REQUIRING CLARIFICATION:

{json.dumps(
    clarification_changes,
    indent=4,
    ensure_ascii=False
)}
"""

    print(
        f"Generating questions for "
        f"{total_changes} changes..."
    )

    print(
        "\n========== CALLING LLM FOR QUESTIONS =========="
    )

    response = llm.invoke(prompt)

    content = response.content.strip()

    print(
        "\n========== RAW QUESTION RESPONSE =========="
    )

    print(content)

    print(
        "============================================"
    )

    # ---------------------------------------------------------
    # Parse
    # ---------------------------------------------------------

    try:

        data = parse_json_response(
            content
        )

        print(
            "Question JSON parsing: SUCCESS"
        )

    except Exception as e:

        print(
            "Question JSON parsing: FAILED"
        )

        print(
            "Error:",
            e
        )

        raise ValueError(
            "LLM returned invalid JSON "
            "for targeted questions."
        )

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    print(
        "\n========== VALIDATING QUESTIONS =========="
    )

    validate_questions(
        data,
        clarification_changes
    )

    print(
        "Question validation: SUCCESS"
    )

    return data