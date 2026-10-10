import json
import re

from services.llm import llm


ANALYZE_CLIENT_CHANGES_PROMPT = """
You are a senior requirements analyst reviewing changes made by a client
to a software requirements set.

Your task is to analyze EVERY client change and identify only genuine
requirements problems caused by that change.

You will receive:

1. The original requirements.
2. The project purpose.
3. The project scope.
4. The project constraints.
5. Client changes:
   - added
   - edited
   - deleted

IMPORTANT RULES:

1. Analyze EVERY added, edited, and deleted change.
2. Do NOT modify the requirements.
3. Do NOT generate questions.
4. Do NOT propose solutions.
5. Do NOT rewrite requirements.
6. Do NOT invent information.
7. Only report an issue when it is supported by the provided information.
8. If a change is valid and creates no identifiable problem, return:
   "issues": []
9. Do not treat a normal change as a problem simply because the wording
   is different.
10. Do not use general software-development assumptions unless they are
    directly relevant to the supplied requirements, purpose, scope,
    or constraints.
11. Do not analyze unrelated requirements unless the client change can
    reasonably affect them.
12. Preserve the provided identifier exactly.

IDENTIFIER RULES:

For existing requirements:

- Use "id".
- The value MUST be the original requirement ID.
- Examples: "FR-8", "FR-15", "NFR-2".
- Never create a new ID for an existing requirement.

For newly added client requirements:

- Use "id".
- Preserve the provided temporary new ID exactly.
- Example: "new-1".
- Do NOT convert it into an FR or NFR ID.
- Final FR/NFR classification and permanent ID assignment happen later.

CHANGE-SPECIFIC ANALYSIS:

FOR EDITED REQUIREMENTS:

Compare the original requirement with the client's new version.

Look for:

- ambiguity introduced by the edit
- missing information introduced by the edit
- unspecified behavior
- contradiction with another requirement
- conflict with project scope
- conflict with stated constraints
- unintended removal of important behavior
- meaningful change that creates uncertainty elsewhere

Do NOT report an issue merely because the wording changed.

FOR DELETED REQUIREMENTS:

Determine whether removing the requirement causes a meaningful problem
for the remaining requirements.

Look for:

- dependency impact
- missing behavior
- broken business logic
- contradiction or inconsistency
- functionality that is referenced elsewhere but is no longer defined
- important behavior becoming unspecified

If deleting the requirement has no identifiable consequence,
return an empty issues array.

FOR ADDED REQUIREMENTS:

Compare the new requirement against:

- project purpose
- project scope
- existing requirements
- stated constraints

Look for:

- scope conflict
- contradiction with existing requirements
- duplication or significant overlap
- unspecified behavior
- incompleteness
- constraint conflict

Do NOT reject an added requirement merely because it is new.

ISSUE TYPES:

Use only one of these issue types:

- ambiguity
- incompleteness
- unspecified_behavior
- dependency_impact
- conflict
- scope_conflict
- constraint_conflict
- duplicate_or_overlap

OUTPUT:

Return ONLY valid JSON.

For every change:

{
    "changes": [
        {
            "id": "FR-8",
            "change_type": "edited",
            "issues": [
                {
                    "type": "ambiguity",
                    "description": "..."
                }
            ]
        }
    ]
}

For a newly added requirement:

{
    "changes": [
        {
            "id": "new-1",
            "change_type": "added",
            "issues": [
                {
                    "type": "scope_conflict",
                    "description": "..."
                }
            ]
        }
    ]
}

Every client change supplied in the input MUST appear exactly once
in the output.

A change with no genuine issue MUST have:

"issues": []

Do not include any fields other than:

- id
- change_type
- issues

Do not include:

- severity
- clarification_required
- recommendations
- questions
- resolutions
- source_id
- source_ids
- new_id
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

    # Remove markdown JSON fences
    cleaned = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*", "", cleaned)

    start = cleaned.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found", content, 0)

    try:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(cleaned[start:])
        return obj
    except Exception:
        pass

    end = cleaned.rfind("}")
    if end != -1 and end > start:
        return json.loads(cleaned[start:end + 1])

    raise json.JSONDecodeError("No valid JSON object found", content, 0)


def validate_analysis(data, change_set):
    """
    Validate that:

    1. Every client change was analyzed.
    2. No client change was analyzed more than once.
    3. Existing requirements use "id".
    4. New requirements use "id".
    5. Only allowed issue types are returned.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Change analysis response must be a JSON object."
        )

    changes = data.get("changes")

    if not isinstance(changes, list):
        raise ValueError(
            "Change analysis response must contain "
            "a 'changes' list."
        )

    # ---------------------------------------------------------
    # Build expected changes
    # ---------------------------------------------------------

    expected_changes = []

    # Existing edited requirements
    for change in change_set.get("edited", []):

        expected_changes.append({
            "identifier": change.get("id"),
            "identifier_type": "id",
            "change_type": "edited"
        })

    # Existing deleted requirements
    for change in change_set.get("deleted", []):

        expected_changes.append({
            "identifier": change.get("id"),
            "identifier_type": "id",
            "change_type": "deleted"
        })

    # New client requirements
    for change in change_set.get("added", []):

        expected_changes.append({
            "identifier": change.get("id"),
            "identifier_type": "id",
            "change_type": "added"
        })

    expected_pairs = {
        (
            change["identifier"],
            change["identifier_type"],
            change["change_type"]
        )
        for change in expected_changes
    }

    returned_pairs = []

    # ---------------------------------------------------------
    # Allowed issue types
    # ---------------------------------------------------------

    allowed_issue_types = {
        "ambiguity",
        "incompleteness",
        "unspecified_behavior",
        "dependency_impact",
        "conflict",
        "scope_conflict",
        "constraint_conflict",
        "duplicate_or_overlap"
    }

    # ---------------------------------------------------------
    # Validate every LLM result
    # ---------------------------------------------------------

    for change in changes:

        if not isinstance(change, dict):
            raise ValueError(
                "Each analyzed change must be an object."
            )

        change_type = change.get("change_type")
        issues = change.get("issues")

        # -----------------------------------------------------
        # Validate change type
        # -----------------------------------------------------

        if change_type not in [
            "edited",
            "deleted",
            "added"
        ]:
            raise ValueError(
                f"Invalid change_type: {change_type}"
            )

        # -----------------------------------------------------
        # Validate identifier
        # -----------------------------------------------------

        if "id" not in change:
            raise ValueError(
                f"{change_type} change must contain 'id'."
            )

        identifier = change.get("id")
        identifier_type = "id"

        if not isinstance(identifier, str):
            raise ValueError(
                f"Invalid identifier for {change_type} change."
            )

        if not identifier.strip():
            raise ValueError(
                f"Empty identifier for {change_type} change."
            )

        # -----------------------------------------------------
        # Validate issues
        # -----------------------------------------------------

        if not isinstance(issues, list):
            raise ValueError(
                f"'issues' must be a list for {identifier}."
            )

        # -----------------------------------------------------
        # Track returned change
        # -----------------------------------------------------

        returned_pairs.append(
            (
                identifier,
                identifier_type,
                change_type
            )
        )

        # -----------------------------------------------------
        # Validate each issue
        # -----------------------------------------------------

        for issue in issues:

            if not isinstance(issue, dict):
                raise ValueError(
                    f"Invalid issue structure for {identifier}."
                )

            issue_type = issue.get("type")
            description = issue.get("description")

            if issue_type not in allowed_issue_types:
                raise ValueError(
                    f"Invalid issue type '{issue_type}' "
                    f"for {identifier}."
                )

            if not isinstance(description, str):
                raise ValueError(
                    f"Issue description must be a string "
                    f"for {identifier}."
                )

            if not description.strip():
                raise ValueError(
                    f"Issue description cannot be empty "
                    f"for {identifier}."
                )

    # ---------------------------------------------------------
    # Clean unexpected changes and fill missing
    # ---------------------------------------------------------

    valid_changes = []
    seen = set()
    for change in changes:
        pair = (change.get("id"), "id", change.get("change_type"))
        if pair in expected_pairs and pair not in seen:
            valid_changes.append(change)
            seen.add(pair)

    missing = expected_pairs - seen
    if missing:
        for identifier, _, change_type in missing:
            valid_changes.append({
                "id": identifier,
                "change_type": change_type,
                "issues": []
            })

    data["changes"] = valid_changes
    return True


def analyze_client_changes(
    requirements,
    change_set
):

    print(
        "\n========== ANALYZING CLIENT CHANGES =========="
    )

    specified_requirements = requirements.get(
        "specified_requirements",
        {}
    )

    purpose = requirements.get(
        "purpose",
        ""
    )

    scope = requirements.get(
        "scope",
        ""
    )

    constraints = requirements.get(
        "constraints",
        requirements.get(
            "design_constraints",
            []
        )
    )

    # ---------------------------------------------------------
    # Prepare information for the LLM
    # ---------------------------------------------------------

    analysis_input = {
        "purpose": purpose,
        "scope": scope,
        "constraints": constraints,
        "original_requirements": specified_requirements,
        "client_changes": {
            "edited": change_set.get(
                "edited",
                []
            ),
            "deleted": change_set.get(
                "deleted",
                []
            ),
            "added": change_set.get(
                "added",
                []
            )
        }
    }

    total_changes = sum(
        len(change_set.get(change_type, []))
        for change_type in [
            "edited",
            "deleted",
            "added"
        ]
    )

    if total_changes == 0:
        print("\n[analyze_client_changes] No edits, deletes, or adds to analyze (all requirements kept).")
        return {"changes": []}

    print(
        f"Analyzing {total_changes} "
        f"client changes..."
    )

    # ---------------------------------------------------------
    # Build prompt
    # ---------------------------------------------------------

    prompt = f"""
{ANALYZE_CLIENT_CHANGES_PROMPT}

PROJECT CONTEXT:

{json.dumps(
    analysis_input,
    indent=2,
    ensure_ascii=False
)}
"""

    print(
        "\n========== CALLING LLM FOR CHANGE ANALYSIS =========="
    )

    response = llm.invoke(prompt)

    content = response.content.strip()

    print(
        "\n========== RAW CHANGE ANALYSIS RESPONSE =========="
    )

    print(content)

    print(
        "===================================================="
    )

    # ---------------------------------------------------------
    # Parse JSON
    # ---------------------------------------------------------

    try:

        data = parse_json_response(
            content
        )

        print(
            "Change analysis JSON parsing: SUCCESS"
        )

    except json.JSONDecodeError as e:

        print(
            "Change analysis JSON parsing: FAILED"
        )

        print(
            "Error:",
            e
        )

        raise ValueError(
            "LLM returned invalid JSON "
            "for client change analysis."
        )

    # ---------------------------------------------------------
    # Validate response
    # ---------------------------------------------------------

    print(
        "\n========== VALIDATING CHANGE ANALYSIS =========="
    )

    validate_analysis(
        data,
        change_set
    )

    print(
        "Change analysis validation: SUCCESS"
    )

    return data
