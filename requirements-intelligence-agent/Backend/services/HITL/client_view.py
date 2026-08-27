import json
import re

from services.llm.llm import llm


CLIENT_VIEW_PROMPT = """
You convert software requirements into client-friendly statements.

You will receive multiple software requirements.

For EACH requirement:

1. Use ONLY the information contained in that requirement.
2. Do NOT use information from any other requirement.
3. Do NOT add examples, context, products, users, roles, features,
   permissions, or behavior that is not explicitly stated.
4. Preserve the exact meaning of the requirement.
5. You may simplify technical wording into natural business language.
6. Do NOT use:
   - Functional Requirement
   - Non-Functional Requirement
   - FR
   - NFR
   - SRS
   - "The system shall"
7. Do not merge requirements.
8. Do not split requirements.
9. Preserve the provided requirement ID exactly.
10. Return exactly one client-friendly statement for each input requirement.
11. Return ONLY valid JSON.

OUTPUT FORMAT:

{
    "items": [
        {
            "requirement_id": "FR-1",
            "text": "Client-friendly requirement statement"
        }
    ]
}
"""


def parse_json_response(content: str):
    """
    Parse JSON returned by the LLM.

    Handles cases where the model wraps the JSON
    inside a markdown code fence.
    """

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

    json_content = content[start:end + 1]

    return json.loads(json_content)


def validate_client_view(data, requirements):
    """
    Ensure that the LLM returned exactly one client-view
    item for every requirement supplied to it.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Client view response must be a JSON object."
        )

    items = data.get("items")

    if not isinstance(items, list):
        raise ValueError(
            "Client view response must contain an 'items' list."
        )

    expected_ids = {
        requirement["id"]
        for requirement in requirements
    }

    returned_ids = [
        item.get("requirement_id")
        for item in items
    ]

    # ---------------------------------------------------------
    # Check for missing IDs
    # ---------------------------------------------------------

    missing_ids = expected_ids - set(returned_ids)

    if missing_ids:
        raise ValueError(
            f"Missing requirements in client view: "
            f"{sorted(missing_ids)}"
        )

    # ---------------------------------------------------------
    # Check for unexpected IDs
    # ---------------------------------------------------------

    unexpected_ids = set(returned_ids) - expected_ids

    if unexpected_ids:
        raise ValueError(
            f"Unexpected requirement IDs in client view: "
            f"{sorted(unexpected_ids)}"
        )

    # ---------------------------------------------------------
    # Check for duplicates
    # ---------------------------------------------------------

    if len(returned_ids) != len(set(returned_ids)):
        raise ValueError(
            "Duplicate requirement IDs in client view."
        )

    # ---------------------------------------------------------
    # Validate item structure
    # ---------------------------------------------------------

    for item in items:

        if not isinstance(item, dict):
            raise ValueError(
                "Each client view item must be an object."
            )

        requirement_id = item.get("requirement_id")
        text = item.get("text")

        if not isinstance(requirement_id, str):
            raise ValueError(
                "Each item must contain a string "
                "'requirement_id'."
            )

        if not isinstance(text, str):
            raise ValueError(
                f"Invalid text for requirement "
                f"{requirement_id}."
            )

        if not text.strip():
            raise ValueError(
                f"Empty client view text for "
                f"{requirement_id}."
            )

    return True


def build_client_view(requirements):

    print("\n========== BUILDING CLIENT VIEW ==========")

    specified_requirements = requirements.get(
        "specified_requirements",
        {}
    )

    functional = specified_requirements.get(
        "functional",
        []
    )

    non_functional = specified_requirements.get(
        "non_functional",
        []
    )

    # Combine all requirements into one list
    all_requirements = (
        functional +
        non_functional
    )

    if not all_requirements:

        print("No requirements found.")

        return {
            "sections": []
        }

    print(
        f"Preparing {len(all_requirements)} "
        f"requirements for one LLM call..."
    )

    # ---------------------------------------------------------
    # Only send the information the LLM needs.
    # The original requirement ID is preserved.
    # ---------------------------------------------------------

    requirements_for_llm = [
        {
            "id": requirement["id"],
            "description": requirement["description"]
        }
        for requirement in all_requirements
    ]

    prompt = f"""
{CLIENT_VIEW_PROMPT}

REQUIREMENTS:

{json.dumps(
    requirements_for_llm,
    indent=2,
    ensure_ascii=False
)}
"""

    print(
        "\n========== CALLING LLM FOR CLIENT VIEW =========="
    )

    response = llm.invoke(prompt)

    content = response.content.strip()

    print(
        "\n========== RAW CLIENT VIEW RESPONSE =========="
    )

    print(content)

    print(
        "==============================================="
    )

    # ---------------------------------------------------------
    # Parse LLM response
    # ---------------------------------------------------------

    try:

        data = parse_json_response(content)

        print(
            "Client view JSON parsing: SUCCESS"
        )

    except json.JSONDecodeError as e:

        print(
            "Client view JSON parsing: FAILED"
        )

        print(
            "Error:",
            e
        )

        raise ValueError(
            "LLM returned invalid JSON "
            "for client view."
        )

    # ---------------------------------------------------------
    # Validate LLM response
    # ---------------------------------------------------------

    print(
        "\n========== VALIDATING CLIENT VIEW =========="
    )

    validate_client_view(
        data,
        all_requirements
    )

    print(
        "Client view validation: SUCCESS"
    )

    # ---------------------------------------------------------
    # Build application client_view
    #
    # IMPORTANT:
    # There is NO item-* ID anymore.
    #
    # The requirement ID itself is used everywhere.
    # ---------------------------------------------------------

    items = []

    for item in data["items"]:

        items.append({
            "id": item["requirement_id"],
            "text": item["text"].strip()
        })

    client_view = {
        "sections": [
            {
                "title": "Requirements",
                "items": items
            }
        ]
    }

    print(
        "\n========== CLIENT VIEW CREATED =========="
    )

    print(
        json.dumps(
            client_view,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "=========================================="
    )

    return client_view