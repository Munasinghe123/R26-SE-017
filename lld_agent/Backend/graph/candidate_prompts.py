from __future__ import annotations

import json


JSON_RULES = """
STRICT RULES:
- Return ONLY valid minified JSON
- Root JSON type MUST be object
- Do NOT explain reasoning
- Do NOT include markdown
- Do NOT include comments
- All keys and strings must use double quotes
- Never truncate JSON
- If unsure use empty arrays
"""


def build_class_prompt(requirements: str, requirement_ids: list[str] | None = None) -> str:
    req_ids = ", ".join(requirement_ids or [])
    return f"""
Generate only the Class Diagram portion of a UML Intermediate Representation.

{JSON_RULES}

Return this schema only:
{{
  "class_diagram": {{
    "classes": [
      {{
        "name": "string",
        "attributes": ["string"],
        "methods": ["string"]
      }}
    ],
    "relationships": [
      {{
        "source": "string",
        "target": "string",
        "type": "association",
        "cardinality": "1..*"
      }}
    ]
  }}
}}

Requirement IDs, if useful: {req_ids}

Requirements:
{requirements}
"""


def build_er_prompt(requirements: str, class_diagram: dict) -> str:
    return f"""
Generate only the ER Diagram portion of a UML Intermediate Representation.
Use the provided class diagram as the structural source of truth.

{JSON_RULES}

Return this schema only:
{{
  "er_diagram": {{
    "entities": [
      {{
        "name": "string",
        "attributes": ["string"],
        "primary_key": "string"
      }}
    ],
    "relationships": [
      {{
        "source": "string",
        "target": "string",
        "type": "one-to-many"
      }}
    ]
  }}
}}

Requirements:
{requirements}

Validated Class Diagram:
{json.dumps({"class_diagram": class_diagram}, ensure_ascii=True)}
"""


def build_sequence_prompt(
    requirements: str,
    class_diagram: dict,
    er_diagram: dict,
) -> str:
    return f"""
Generate only the Sequence Diagrams portion of a UML Intermediate Representation.
Use the provided class diagram and ER diagram as the structural source of truth.

{JSON_RULES}

Return this schema only:
{{
  "sequence_diagrams": [
    {{
      "name": "string",
      "description": "string",
      "participants": ["string"],
      "messages": [
        {{
          "from": "string",
          "to": "string",
          "message": "string"
        }}
      ]
    }}
  ]
}}

Requirements:
{requirements}

Validated Class Diagram:
{json.dumps({"class_diagram": class_diagram}, ensure_ascii=True)}

Validated ER Diagram:
{json.dumps({"er_diagram": er_diagram}, ensure_ascii=True)}
"""
