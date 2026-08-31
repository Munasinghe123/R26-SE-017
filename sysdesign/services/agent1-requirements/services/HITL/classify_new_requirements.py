import json
import re

from services.llm import llm


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
            "Classification response must contain a requirements list."
        )

    expected_ids = {
        requirement["id"]
        for requirement in source_requirements
    }

    req_map = {r.get("id"): r for r in requirements if isinstance(r, dict)}
    valid_types = {"functional", "non_functional", "non-functional"}

    sanitized = []
    for src in source_requirements:
        sid = src["id"]
        classified_item = req_map.get(sid)
        if classified_item:
            raw_type = str(classified_item.get("type", "functional")).strip().lower().replace("-", "_")
            if raw_type not in ["functional", "non_functional"]:
                raw_type = "functional"
            sanitized.append({
                "id": sid,
                "text": src.get("text", classified_item.get("text", "")),
                "type": raw_type
            })
        else:
            sanitized.append({
                "id": sid,
                "text": src.get("text", ""),
                "type": "functional"
            })

    data["requirements"] = sanitized
    return True


def classify_new_requirements(
    requirements: list
):

    print(
        "\n========== CLASSIFYING NEW REQUIREMENTS =========="
    )

    if not requirements:
        print("[classify_new_requirements] No new requirements to classify.")
        return []

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

    except Exception as e:

        raise ValueError(
            "LLM returned invalid JSON for requirement classification."
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