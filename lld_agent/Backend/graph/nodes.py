import json

from utils.jsonCleaner import clean_json_response
from utils.irMapper import convert_to_ir
from Services.validationService import ValidationService
from graph.state import UMLGraphState
from config.config import GENERATION_MODEL_1, GENERATION_PROVIDER
from llm.factory import get_llm_provider

llm_provider = get_llm_provider(GENERATION_PROVIDER)

# ====================================
# HELPER FUNCTIONS
# ====================================

def _build_prompt(reqs: str, extra_rules: str = "") -> str:
    return f"""
Analyze the requirements and generate a complete UML Intermediate Representation.

STRICT RULES:
- Return ONLY valid minified JSON
- Root JSON type MUST be object
- Do NOT use <think>
- Do NOT explain reasoning
- Skip internal analysis
- Output JSON immediately
- NEVER return arrays at top level
- NEVER wrap JSON inside []
- Do NOT include markdown
- Do NOT include explanations
- Do NOT include comments
- Do NOT include thinking text
- Do NOT include ```json
- Output must start with {{
- Output must end with }}
- All keys and strings must use double quotes
- Never truncate JSON
- If unsure use empty arrays
{extra_rules}

JSON Schema:

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
  ],

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
{reqs}

{f'''
VALIDATION FIX INSTRUCTIONS:

{extra_rules}

IMPORTANT:
Apply these fixes while STILL returning ONLY valid JSON.
''' if extra_rules else ""}
"""

def _build_validation_guidance(expert_guidance: str, errors: list) -> str:
    if expert_guidance:
        body = expert_guidance.strip()
    else:
        lines = []
        for err in errors or []:
            message = err.get("message", "").strip()
            if message:
                lines.append(f"- {message}")
        body = "\n".join(lines)

    if not body:
        return ""
    return f"\nFix these validation issues:\n{body}\n"


def _create_completion_with_retry(prompt: str):
    return llm_provider.complete(
        model=GENERATION_MODEL_1,
        temperature=0,
        max_tokens=3500,
        messages=[
            {
                "role": "system",
                "content": "You extract UML class, sequence, and ER structures.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )


# ====================================
# LANGGRAPH NODES
# ====================================

def generate_node(state: UMLGraphState) -> dict:
  """Calls the LLM to generate or fix the UML JSON."""
  prompt = _build_prompt(state["requirements"], state["extra_rules"])
  response = _create_completion_with_retry(prompt)
  return {
    "llm_response": response.content,
    "iterations_used": state["iterations_used"] + 1,
  }

def parse_node(state: UMLGraphState) -> dict:
    """Attempts to parse the LLM output into clean JSON."""
    content = state["llm_response"]
    print("=== RAW LLM OUTPUT ===")
    print(content)
    
    try:
        parsed_json = clean_json_response(content)
        return {"parsed_json": parsed_json, "extra_rules": ""}
    except json.JSONDecodeError as e:
        print("JSON PARSE FAILED")
        print(e)
        parse_retry_rules = (
            "\nCRITICAL JSON FIX RULES:"
            "\n- Return ONLY ONE JSON object"
            "\n- NEVER wrap output in []"
            "\n- Ensure all strings are closed"
            "\n- Do not truncate output"
            "\n- Do not split er_diagram"
            "\n- Output must start with {"
            "\n- Output must end with }"
            "\n- Use empty arrays or objects if unsure"
        )
        return {"parsed_json": None, "extra_rules": parse_retry_rules}

def validate_node(state: UMLGraphState) -> dict:
    """Validates the parsed JSON and generates retry instructions if needed."""
    parsed_json = state["parsed_json"]
    try:
        ir = convert_to_ir(parsed_json)
        validation_result = ValidationService.validate(
            ir,
            requirement_ids=state["requirement_ids"],
        )
    except Exception as exc:
        validation_result = {
            "report": {
                "passed": False,
                "consistency_score": 0.0,
                "total_checks": 0,
                "passed_checks": 0,
                "errors": [
                    {
                        "rule_id": "VALIDATION-ERROR",
                        "severity": "high",
                        "message": str(exc),
                        "suggestion": "Review the IR mapping and validation inputs.",
                        "educational_feedback": "",
                    }
                ],
                "traceability_matrix": [],
                "overdesign_flags": [],
                "naming_violations": [],
                "naming_violations_fixed": 0,
            },
            "errors": [],
            "expert_guidance": "",
        }

    errors = validation_result.get("errors", [])
    expert_guidance = validation_result.get("expert_guidance", "")

    has_critical = any(err.get("severity") == "critical" for err in errors)
    
    if not has_critical:
        return {"validation_result": validation_result, "is_successful": True, "extra_rules": ""}
    
    validation_guidance = _build_validation_guidance(expert_guidance, errors)
    return {"validation_result": validation_result, "is_successful": False, "extra_rules": validation_guidance}
