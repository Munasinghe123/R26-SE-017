import json
import re

from services.llm.llm import llm


CLASSIFICATION_PROMPT = """
You are a senior software requirements analyst.

Classify each supplied software requirement as either:

- functional
- non_functional

FUNCTIONAL REQUIREMENTS:

Functional requirements describe what the software must do.

A functional requirement describes:
- a system behavior
- a system capability
- an operation the system performs
- an interaction between a user and the system

NON-FUNCTIONAL REQUIREMENTS:

Non-functional requirements describe how the software system
should perform or constraints imposed on the software system.

Examples include:

- performance
- security
- reliability
- availability
- usability
- scalability
- maintainability
- portability
- response time
- resource limitations
- software-specific operational constraints

IMPORTANT:

1. Classify based only on the requirement text.

2. Do not change the requirement text.

3. Preserve the requirement ID exactly.

4. Do not create IDs.

5. Do not use "new_id".

6. Every supplied requirement must receive exactly one classification.

7. Do not add explanations.

8. Return ONLY valid JSON.

OUTPUT FORMAT:

{
    "requirements": [
        {
            "id": "new-1",
            "text": "Original requirement text",
            "type": "functional"
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


def validate_classification(
    data,
    source_requirements
):

    if not isinstance(data, dict):
        raise ValueError(
            "Classification response must be an object."
        )

    requirements = data.get(
        "requirements"
    )

    if not isinstance(requirements, list):
        raise ValueError(
            "Classification response must contain "
            "a requirements list."
        )

    expected_ids = {
        requirement["id"]
        for requirement in source_requirements
    }

    returned_ids = [
        requirement.get("id")
        for requirement in requirements
    ]

    # Every requirement must be classified
    if len(requirements) != len(source_requirements):
        raise ValueError(
            "Every new requirement must be classified."
        )

    # No missing IDs
    missing_ids = (
        expected_ids -
        set(returned_ids)
    )

    if missing_ids:
        raise ValueError(
            f"Missing classified requirements: "
            f"{sorted(missing_ids)}"
        )

    # No unexpected IDs
    unexpected_ids = (
        set(returned_ids) -
        expected_ids
    )

    if unexpected_ids:
        raise ValueError(
            f"Unexpected requirement IDs: "
            f"{sorted(unexpected_ids)}"
        )

    # No duplicate IDs
    if len(returned_ids) != len(set(returned_ids)):
        raise ValueError(
            "Duplicate requirement IDs."
        )

    valid_types = {
        "functional",
        "non_functional"
    }

    for requirement in requirements:

        requirement_id = requirement.get("id")
        text = requirement.get("text")
        requirement_type = requirement.get("type")

        if not isinstance(text, str):
            raise ValueError(
                f"Invalid text for {requirement_id}."
            )

        if requirement_type not in valid_types:
            raise ValueError(
                f"Invalid requirement type for "
                f"{requirement_id}: "
                f"{requirement_type}"
            )

    return True


def classify_new_requirements(
    requirements: list
):

    print(
        "\n========== CLASSIFYING NEW REQUIREMENTS =========="
    )

    prompt = f"""
{CLASSIFICATION_PROMPT}

REQUIREMENTS TO CLASSIFY:

{json.dumps(
    requirements,
    indent=2,
    ensure_ascii=False
)}
"""

    response = llm.invoke(prompt)

    content = response.content.strip()

    print(
        "\n========== RAW CLASSIFICATION =========="
    )

    print(content)

    print(
        "========================================="
    )

    try:

        data = parse_json_response(
            content
        )

    except json.JSONDecodeError as e:

        raise ValueError(
            "LLM returned invalid JSON "
            "for requirement classification."
        ) from e

    validate_classification(
        data,
        requirements
    )

    print(
        "\n========== CLASSIFICATION SUCCESS =========="
    )

    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "============================================="
    )

    return data["requirements"]