import json
import re

from services.llm.llm import llm


QUESTION_GENERATION_PROMPT = """
You generate targeted business clarification questions
for a software requirements review.

The client has already reviewed the requirements and explicitly
requested changes.

Another component has analyzed the client's changes and identified
specific issues that may require clarification.

Your job is to generate only the minimum necessary questions needed
to resolve genuine ambiguity, conflict, or missing business behavior.

The questions are shown directly to a non-technical business client.

RULES:

1. Questions must be understandable by a non-technical business client.

2. Use natural business language.

3. Do not use technical implementation terminology.

4. Do not ask about programming languages, databases, APIs,
   frameworks, architecture, implementation, or technical design.

5. Do not ask for information that is already explicitly provided
   by the client.

6. Do not invent new features, requirements, assumptions, or
   business rules.

7. A client explicitly requesting a change is evidence of their
   intended behavior. Do not ask whether they want a change that
   they have already explicitly requested.

8. Do not create questions merely because two requirements are
    related or mention similar users, roles, or functionality.

9. Only treat two requirements as overlapping when their intended
    business responsibilities genuinely conflict or cannot
    reasonably coexist.

10. For edited requirements, ask only what is necessary to resolve
    the specific ambiguity or missing business behavior identified
    in the input.

11. For deleted requirements, ask only what is necessary to
    determine whether the functionality should actually be removed
    or retained.

12. For newly added requirements, ask only what is necessary to
    define genuinely missing business behavior.

13. Do not ask a question when the client's requested behavior is
    already sufficiently clear from the client change and project
    context.

14. Generate the minimum number of questions necessary.

15. Generate between 1 and 2 questions only when clarification is
    genuinely necessary for a specific change.

16. Every question must directly address a specific unresolved
    business issue provided in the input.

17. Requirement identifiers are internal metadata only.

18. NEVER mention internal requirement identifiers such as FR-1,
    FR-14, FR-21, NFR-1, NFR-2, Q-1, or generated IDs inside the
    client-facing question or reason.

19. The requirement identifier must appear only in the structured
    `requirement_id` field.

20. Do not mention that a question is being asked because of an
    internal requirement, change analysis, classifier, agent,
    system, or workflow.

21. The `question` and `reason` fields must be written entirely
    for the business client.

22. Return ONLY valid JSON.

OUTPUT:

{
    "questions": [
        {
            "id": "Q-1",
            "requirement_id": "FR-8",
            "question": "Business-oriented question",
            "reason": "Business-oriented explanation of why this clarification is needed"
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