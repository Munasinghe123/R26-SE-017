import json
import re

from services.llm import llm


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

14. Generate the minimum number of questions necessary (MAXIMUM of 3 questions in total).

15. Prioritize the highest-impact ambiguities (such as contradictions, security/access bounds, or undefined outputs) over minor phrasing issues.

16. Every question must directly address a specific unresolved business issue provided in the input.

17. For EACH question, provide 2 to 4 concrete `suggested_options` (e.g., specific formats, roles, or policies) so the client can easily choose an option or use it as a reference.

18. NEVER mention internal requirement identifiers such as FR-1, FR-14, FR-21, NFR-1, NFR-2, Q-1, or generated IDs inside the client-facing `question` or `reason`.
    Refer instead to the feature or phrasing (e.g. "Regarding the export feature you edited..." or "In the newly added login requirement...").

19. The requirement identifier must appear only in the structured `requirement_id` field.

20. Do not mention that a question is being asked because of an internal requirement, change analysis, classifier, agent, system, or workflow.

21. The `question` and `reason` fields must be written entirely in clear, friendly business language.

22. Return ONLY valid JSON.

OUTPUT:

{
    "questions": [
        {
            "id": "Q-1",
            "requirement_id": "FR-8",
            "question": "Which export formats should the system support?",
            "suggested_options": [
                "CSV only",
                "CSV and Excel (.xlsx)",
                "PDF and Excel",
                "Other (specify below)"
            ],
            "reason": "Clarification needed because the edited requirement mentions exporting logs without specifying the file format."
        }
    ]
}
"""


def parse_json_response(content: str):

    content = content.strip()

    try:
        import json_repair
        data = json_repair.loads(content)
        if isinstance(data, (dict, list)):
            return data
    except Exception:
        pass

    # Extract JSON inside markdown code fences if present
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Remove markdown code fences
    cleaned = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*", "", cleaned)

    start = cleaned.find("{")
    if start == -1:
        raise ValueError("LLM did not return a JSON object.")

    # Try raw_decode from first brace to parse exact JSON object (ignoring trailing notes)
    try:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(cleaned[start:])
        return obj
    except Exception:
        pass

    end = cleaned.rfind("}")
    if end != -1 and end > start:
        return json.loads(cleaned[start:end + 1])

    raise ValueError("LLM did not return a valid JSON object.")


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
        "added",
        "contradictions"
    ):

        for change in clarification_changes.get(
            change_type,
            []
        ):

            expected_ids.add(
                change["id"]
            )
            if change.get("conflicts_with"):
                expected_ids.add(change["conflicts_with"])

    # ---------------------------------------------------------
    # Validate questions
    # ---------------------------------------------------------

    valid_questions = []
    question_ids = set()

    for question in questions:

        if not isinstance(question, dict):
            continue

        question_id = question.get("id")
        requirement_id = question.get("requirement_id")
        text = question.get("question")
        reason = question.get("reason")

        if not isinstance(question_id, str) or not isinstance(requirement_id, str):
            continue

        if requirement_id not in expected_ids:
            print(f"[generate_targeted_questions] Dropping question referencing non-clarification ID: '{requirement_id}'")
            continue

        if not isinstance(text, str) or not text.strip():
            continue

        if not isinstance(reason, str) or not reason.strip():
            reason = "Clarification required to ensure accurate requirement implementation."

        options = question.get("suggested_options", [])
        if not isinstance(options, list):
            options = []
        question["suggested_options"] = [str(o).strip() for o in options if str(o).strip()]

        # Scrub any accidental technical IDs from question and reason
        question["question"] = re.sub(r"\b(FR|NFR|RC|Q)-\d+\b", "this requirement", text, flags=re.IGNORECASE).strip()
        question["reason"] = re.sub(r"\b(FR|NFR|RC|Q)-\d+\b", "this requirement", reason, flags=re.IGNORECASE).strip()

        if question_id in question_ids:
            question_id = f"Q-{len(valid_questions) + 1}"
            question["id"] = question_id

        question_ids.add(question_id)
        valid_questions.append(question)

    # ---------------------------------------------------------
    # Attach requirement context for UI clarity
    # ---------------------------------------------------------

    changes_by_id = {}
    for change_type in ("edited", "deleted", "added"):
        for c in clarification_changes.get(change_type, []):
            cid = c.get("id")
            if cid:
                changes_by_id[cid] = {
                    "action": change_type,
                    "text": c.get("new_text") or c.get("text", "") or c.get("old_text", "")
                }

    for q in valid_questions:
        c_info = changes_by_id.get(q.get("requirement_id"), {})
        q["requirement_text"] = c_info.get("text", "")
        q["client_action"] = c_info.get("action", "change")

    # Cap to maximum 3 questions to prevent client fatigue
    if len(valid_questions) > 3:
        valid_questions = valid_questions[:3]

    data["questions"] = valid_questions
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

    contradictions = clarification_changes.get("contradictions", [])
    other_changes_count = sum(
        len(clarification_changes.get(change_type, []))
        for change_type in ("edited", "deleted", "added")
    )
    total_changes = other_changes_count + len(contradictions)

    if total_changes == 0:
        print("No changes require clarification.")
        return {"questions": []}

    # ---------------------------------------------------------
    # 1. Direct multiple-choice resolution for contradictions
    # ---------------------------------------------------------
    contradiction_questions = []
    for idx, c in enumerate(contradictions):
        r1_id = c.get("id")
        r2_id = c.get("conflicts_with")
        r1_text = c.get("r1_text", "")
        r2_text = c.get("r2_text", "")

        contradiction_questions.append({
            "id": f"Q-CONFLICT-{idx + 1}",
            "requirement_id": r1_id,
            "conflicts_with": r2_id,
            "question": "Which of these two conflicting policies should the platform follow?",
            "suggested_options": [
                f"Keep: \"{r1_text}\" (Removes opposing rule)",
                f"Keep: \"{r2_text}\" (Removes opposing rule)"
            ],
            "reason": f"Direct conflict: {c.get('reason', 'Both policies cannot coexist.')}",
            "requirement_text": f"Conflicting rules: \"{r1_text}\" vs \"{r2_text}\"",
            "client_action": "conflict"
        })

    # If only contradictions exist or cap reached, return directly
    if other_changes_count == 0 or len(contradiction_questions) >= 3:
        capped = contradiction_questions[:3]
        print(f"Generated {len(capped)} direct contradiction resolution questions.")
        return {"questions": capped}

    # ---------------------------------------------------------
    # 2. LLM generates questions for remaining changes
    # ---------------------------------------------------------
    non_contradiction_changes = {
        "edited": clarification_changes.get("edited", []),
        "deleted": clarification_changes.get("deleted", []),
        "added": clarification_changes.get("added", [])
    }

    prompt = f"""
{QUESTION_GENERATION_PROMPT}

CHANGES REQUIRING CLARIFICATION:

{json.dumps(
    non_contradiction_changes,
    indent=4,
    ensure_ascii=False
)}
"""

    print(
        f"Generating questions for {other_changes_count} other changes..."
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
        non_contradiction_changes
    )

    print(
        "Question validation: SUCCESS"
    )

    merged = contradiction_questions + data.get("questions", [])
    if len(merged) > 3:
        merged = merged[:3]

    data["questions"] = merged
    return data
