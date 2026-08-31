from __future__ import annotations

import json

from skills.uml import SkillRegistry


_UML_SKILL_REGISTRY = SkillRegistry()
COMMON_UML_SKILL = _UML_SKILL_REGISTRY.get("common_uml")
CLASS_GENERATION_SKILL = _UML_SKILL_REGISTRY.get("class_generation")
ER_GENERATION_SKILL = _UML_SKILL_REGISTRY.get("er_generation")
SEQUENCE_GENERATION_SKILL = _UML_SKILL_REGISTRY.get("sequence_generation")


def build_unified_lld_prompt(requirements: str, requirement_ids: list[str] | None = None) -> str:
    req_ids = ", ".join(requirement_ids or [])
    return f"""You are a Principal Software Architect.
Generate a complete, consistent Low-Level Design (LLD) containing Class Diagram, ER Diagram, and Sequence Diagrams matching the given functional requirements.

REQUIREMENTS:
Requirement IDs: {req_ids}
{requirements}

OUTPUT INSTRUCTIONS:
- Return ONLY valid JSON with no markdown wrapping or preamble.
- Ensure cross-diagram consistency: Entity names in ER diagram MUST match persistent class names in Class diagram.
- Methods in Class diagram MUST match message interactions in Sequence diagrams.

REQUIRED JSON OUTPUT SCHEMA:
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
  }},
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
  }},
  "sequence_diagrams": [
    {{
      "name": "string",
      "description": "string",
      "participants": ["string"],
      "participant_types": {{
        "Customer": "actor",
        "FrontendUI": "boundary",
        "OrderController": "controller"
      }},
      "items": [
        {{
          "from": "string",
          "to": "string",
          "message": "string",
          "type": "call",
          "activate": false,
          "deactivate": false
        }},
        {{
          "block_type": "loop",
          "condition": "string",
          "items": [
            {{
              "from": "string",
              "to": "string",
              "message": "string",
              "type": "call"
            }}
          ]
        }},
        {{
          "from": "string",
          "to": "string",
          "message": "string",
          "type": "return",
          "activate": false,
          "deactivate": false
        }}
      ]
    }}
  ]
}}
"""


def build_class_prompt(requirements: str, requirement_ids: list[str] | None = None) -> str:
    req_ids = ", ".join(requirement_ids or [])
    return f"""
{COMMON_UML_SKILL.instructions}

{CLASS_GENERATION_SKILL.instructions}

INPUT
Requirement IDs:
{req_ids}

Requirements:
{requirements}

OUTPUT SCHEMA

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
        "cardinality": "string"
      }}
    ]
  }}
}}

Allowed cardinality values include "1", "0..1", "1..*", and "0..*".
"""


def build_er_prompt(requirements: str, class_diagram: dict) -> str:
    return f"""
{COMMON_UML_SKILL.instructions}

{ER_GENERATION_SKILL.instructions}

OUTPUT SCHEMA

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

Supported relationship types: "one-to-one", "one-to-many", "many-to-one", "many-to-many".

INPUT
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
{COMMON_UML_SKILL.instructions}

{SEQUENCE_GENERATION_SKILL.instructions}

OUTPUT SCHEMA

{{
  "sequence_diagrams": [
    {{
      "name": "string",
      "description": "string",
      "participants": ["string"],
      "participant_types": {{
        "<participant_name>": "<participant_type>"
      }},
      "items": [
        {{
          "from": "string",
          "to": "string",
          "message": "string",
          "type": "call",
          "activate": false,
          "deactivate": false
        }},
        {{
          "block_type": "loop",
          "condition": "string",
          "items": [
            {{
              "from": "string",
              "to": "string",
              "message": "string",
              "type": "call"
            }}
          ]
        }},
        {{
          "from": "string",
          "to": "string",
          "message": "string",
          "type": "return"
        }}
      ]
    }}
  ]
}}

Participant types may include "actor", "boundary", "controller", "service", "repository", "entity", "database", or "external_system".

INPUT
Requirements:
{requirements}

Validated Class Diagram:
{json.dumps({"class_diagram": class_diagram}, ensure_ascii=True)}

Validated ER Diagram:
{json.dumps({"er_diagram": er_diagram}, ensure_ascii=True)}
"""
