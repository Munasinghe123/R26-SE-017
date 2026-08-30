from __future__ import annotations

import json

from skills.uml import SkillRegistry

_UML_SKILL_REGISTRY = SkillRegistry()
COMMON_UML_SKILL = _UML_SKILL_REGISTRY.get("common_uml")
CLASS_GENERATION_SKILL = _UML_SKILL_REGISTRY.get("class_generation")
ER_GENERATION_SKILL = _UML_SKILL_REGISTRY.get("er_generation")
SEQUENCE_GENERATION_SKILL = _UML_SKILL_REGISTRY.get("sequence_generation")


def build_class_prompt(
    requirements: str, requirement_ids: list[str] | None = None
) -> str:
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
        "methods": ["string"],
        "requirement_ids": ["REQ-001"]
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
        "primary_key": "string",
        "requirement_ids": ["REQ-001"],
        "foreign_keys": [
          {{
            "attribute": "string",
            "references_entity": "string",
            "references_attribute": "string"
          }}
        ]
      }}
    ],
    "relationships": [
      {{
        "name": "semantic relationship verb or verb phrase",
        "source": "string",
        "target": "string",
        "type": "one-to-one | one-to-many | many-to-one | many-to-many",
        "source_multiplicity": "1 | 0..1 | 0..* | 1..*",
        "target_multiplicity": "1 | 0..1 | 0..* | 1..*",
        "evidence": "string"
      }}
    ]
  }}
}}

RELATIONSHIP FIELD SEMANTICS

"name":
- semantic business meaning of the relationship
- examples: "places", "contains", "owns", "enrolls_in"
- NEVER use cardinality names such as "one-to-many"

"type":
- coarse relationship classification used programmatically
- examples: "one-to-many", "many-to-many"
- this is NOT the rendered relationship name

"source_multiplicity":
- multiplicity displayed at the source entity end

"target_multiplicity":
- multiplicity displayed at the target entity end

Example:

Customer PLACES Order

where:
- each Order belongs to exactly one Customer
- a Customer may have zero or more Orders

must be:

{{
  "name": "places",
  "source": "Customer",
  "target": "Order",
  "type": "one-to-many",
  "source_multiplicity": "1",
  "target_multiplicity": "0..*",
  "evidence": "A customer can have multiple orders, and each order belongs to one customer."
}}

Example:

Order CONTAINS CartItem

where:
- every CartItem belongs to exactly one Order
- every Order contains one or more CartItems

must be:

{{
  "name": "contains",
  "source": "Order",
  "target": "CartItem",
  "type": "one-to-many",
  "source_multiplicity": "1",
  "target_multiplicity": "1..*",
  "evidence": "An order contains one or more cart items, and each cart item belongs to one order."
}}

IMPORTANT:

Return JSON only.
Do not return Markdown.
Do not return explanations.

REQUIREMENTS:

{requirements}

VALIDATED CLASS DIAGRAM:

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
      "requirement_ids": ["REQ-001"],
      "participants": ["string"],
      "participant_types": {{
        "<participant_name>": "<participant_type>"
      }},
      "logic_blocks": [
        {{
          "block_type": "alt",
          "condition": "string",
          "messages": [
            {{
              "from": "string",
              "to": "string",
              "message": "string",
              "activate": false,
              "deactivate": false
            }}
          ],
          "logic_blocks": []
        }}
      ],
      "messages": [
        {{
          "from": "string",
          "to": "string",
          "message": "string",
          "activate": false,
          "deactivate": false
        }}
      ]
    }}
  ]
}}

Participant types may include "actor", "boundary", "control", "entity", "database", or "participant".

INPUT
Requirements:
{requirements}

Validated Class Diagram:
{json.dumps({"class_diagram": class_diagram}, ensure_ascii=True)}

Validated ER Diagram:
{json.dumps({"er_diagram": er_diagram}, ensure_ascii=True)}
"""
