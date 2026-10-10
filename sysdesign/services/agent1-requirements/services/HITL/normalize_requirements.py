import json
import re

from services.llm import llm


NORMALIZE_PROMPT = """
You are a senior software requirements analyst.

Rewrite the supplied software requirements so that they follow
the required IEEE-style requirement wording.

Every requirement MUST begin exactly with:

"The system shall"

FUNCTIONAL REQUIREMENTS:

The requirement must describe a behavior or capability that
the system provides.

Example:

"The system shall allow staff to update appointment statuses."

NON-FUNCTIONAL REQUIREMENTS:

The requirement must describe a quality attribute, performance
characteristic, constraint, or other property of the software system.

Example:

"The system shall respond to normal user actions within two seconds
under normal business load."

IMPORTANT:

1. Rewrite ONLY the wording.

2. Preserve the original meaning.

3. Do not introduce new functionality.

4. Do not remove existing behavior.

5. Preserve the requirement ID exactly.

6. Preserve the requirement classification exactly.

7. Every rewritten requirement must begin with:
   "The system shall"

8. Do not create IDs.

9. Do not use "new_id".

10. Return ONLY valid JSON.

OUTPUT FORMAT:

{
    "requirements": [
        {
            "id": "new-1",
            "text": "The system shall ...",
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


def validate_normalized_requirements(
    data,
    source_requirements
):

    if not isinstance(data, dict):
        raise ValueError(
            "Normalization response must be an object."
        )

    requirements = data.get(
        "requirements"
    )

    if not isinstance(requirements, list):
        raise ValueError(
            "Normalization response must contain "
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

    if len(requirements) != len(
        source_requirements
    ):
        raise ValueError(
            "Every requirement sent for rewriting "
            "must be returned."
        )

    if set(returned_ids) != expected_ids:
        raise ValueError(
            "Normalized requirement IDs do not "
            "match the input IDs."
        )

    if len(returned_ids) != len(
        set(returned_ids)
    ):
        raise ValueError(
            "Duplicate requirement IDs."
        )

    for requirement in requirements:

        requirement_id = requirement["id"]
        text = requirement.get("text")
        requirement_type = requirement.get("type")

        if not isinstance(text, str):
            raise ValueError(
                f"Invalid text for {requirement_id}."
            )

        if not text.startswith(
            "The system shall"
        ):
            raise ValueError(
                f"{requirement_id} was not rewritten "
                f"into the required format."
            )

        if requirement_type not in {
            "functional",
            "non_functional"
        }:
            raise ValueError(
                f"Invalid classification for "
                f"{requirement_id}."
            )

    return True


def normalize_requirements(
    requirements_to_rewrite: list[dict]
):

    if not requirements_to_rewrite:
        return []

    print(
        "\n========== REWRITING REQUIREMENTS =========="
    )

    prompt = f"""
{NORMALIZE_PROMPT}

REQUIREMENTS:

{json.dumps(
    requirements_to_rewrite,
    indent=2,
    ensure_ascii=False
)}
"""

    response = llm.invoke(prompt)

    content = response.content.strip()

    print(
        "\n========== RAW NORMALIZED REQUIREMENTS =========="
    )

    print(content)

    print(
        "=================================================="
    )

    try:

        data = parse_json_response(
            content
        )

    except json.JSONDecodeError as e:

        raise ValueError(
            "LLM returned invalid JSON "
            "for requirement normalization."
        ) from e

    validate_normalized_requirements(
        data,
        requirements_to_rewrite
    )

    return data["requirements"]