from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, END
from groq import Groq
from dotenv import load_dotenv
import os
from datetime import datetime
import zlib
import json
import base64
import requests

from utils.jsonCleaner import clean_json_response
from utils.irGenerator import (
  generate_class_plantuml,
  generate_sequence_plantuml,
  generate_er_plantuml
)
from Services.validationService import ValidationService
from utils.irMapper import convert_to_ir
from config.config import MAX_ITERATIONS

# LOAD ENV
load_dotenv()

# GROQ CLIENT
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# PLANTUML ENCODER
def encode_plantuml(plantuml_str):
    # ====================================
    # RAW DEFLATE - NO ZLIB HEADER
    # ====================================
    compress_obj = zlib.compressobj(
        zlib.Z_BEST_COMPRESSION,
        zlib.DEFLATED,
        -15
    )
    compressed = compress_obj.compress(plantuml_str.encode("utf-8"))
    compressed += compress_obj.flush()

    # ====================================
    # PLANTUML CUSTOM BASE64 ALPHABET
    # ====================================
    plantuml_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    standard_alphabet  = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    standard_b64 = base64.b64encode(compressed).decode("ascii")

    result = standard_b64.translate(
        str.maketrans(standard_alphabet, plantuml_alphabet)
    )

    return result


# ====================================
# LANGGRAPH STATE DEFINITION
# ====================================
class UMLGraphState(TypedDict):
    requirements: str
    requirement_ids: list[str]
    extra_rules: str
    llm_response: str
    parsed_json: Optional[dict]
    validation_result: Optional[dict]
    iterations_used: int
    max_iterations: int
    is_successful: bool


class UMLService:

    @staticmethod
    def generate_uml(requirements: str, requirement_ids: list[str] | None = None):

        def build_prompt(reqs: str, extra_rules: str = "") -> str:
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

        def build_validation_guidance(expert_guidance: str, errors: list) -> str:
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

        # ====================================
        # LANGGRAPH NODES
        # ====================================

        def generate_node(state: UMLGraphState) -> dict:
            prompt = build_prompt(state["requirements"], state["extra_rules"])
            response = client.chat.completions.create(
                model="qwen/qwen3-32b",
                temperature=0,
                max_completion_tokens=3500,
                messages=[
                    {
                        "role": "system",
                        "content": "You extract UML class, sequence, and ER structures."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return {
                "llm_response": response.choices[0].message.content,
                "iterations_used": state["iterations_used"] + 1
            }

        def parse_node(state: UMLGraphState) -> dict:
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
            
            validation_guidance = build_validation_guidance(expert_guidance, errors)
            return {"validation_result": validation_result, "is_successful": False, "extra_rules": validation_guidance}

        # ====================================
        # LANGGRAPH ROUTING
        # ====================================

        def route_after_generate(state: UMLGraphState) -> str:
            return "parse"

        def route_after_parse(state: UMLGraphState) -> str:
            if state["parsed_json"] is None:
                if state["iterations_used"] >= state["max_iterations"]:
                    return END
                return "generate"
            return "validate"
            
        def route_after_validate(state: UMLGraphState) -> str:
            if state["is_successful"] or state["iterations_used"] >= state["max_iterations"]:
                return END
            return "generate"

        # ====================================
        # COMPILE AND RUN LANGGRAPH
        # ====================================

        workflow = StateGraph(UMLGraphState)
        
        # Add nodes
        workflow.add_node("generate", generate_node)
        workflow.add_node("parse", parse_node)
        workflow.add_node("validate", validate_node)
        
        # Add edges
        workflow.set_entry_point("generate")
        workflow.add_conditional_edges("generate", route_after_generate, {"parse": "parse"})
        workflow.add_conditional_edges("parse", route_after_parse, {"generate": "generate", "validate": "validate", END: END})
        workflow.add_conditional_edges("validate", route_after_validate, {"generate": "generate", END: END})
        
        graph_app = workflow.compile()
        
        initial_state = {
            "requirements": requirements,
            "requirement_ids": requirement_ids or [],
            "extra_rules": "",
            "llm_response": "",
            "parsed_json": None,
            "validation_result": None,
            "iterations_used": 0,
            "max_iterations": max(MAX_ITERATIONS, 1),
            "is_successful": False
        }
        
        final_state = graph_app.invoke(initial_state)

        # Retrieve outputs from final state
        parsed_json = final_state.get("parsed_json") or {}
        validation_result = final_state.get("validation_result") or {}
        validation_report = validation_result.get("report")
        iterations_used = final_state.get("iterations_used", 1)

        if not parsed_json:
            raise ValueError("Failed to successfully parse or validate LLM output as JSON within iteration limits.")

        # ====================================
        # GENERATE PLANTUML
        # ====================================

        class_plantuml = generate_class_plantuml(parsed_json.get("class_diagram", {}))
        sequence_diagrams = parsed_json.get("sequence_diagrams", [])

        generated_sequences = []
        for seq in sequence_diagrams:
            sequence_plantuml = generate_sequence_plantuml(seq)
            generated_sequences.append({
                "name": seq.get("name", "sequence"),
                "plantuml": sequence_plantuml
            })
            
        er_plantuml = generate_er_plantuml(parsed_json.get("er_diagram", {}))

        # ====================================
        # ENCODE + RENDER PLANTUML
        # ====================================

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "output")
        )
        os.makedirs(output_dir, exist_ok=True)

        def render_png(plantuml_code, file_name):
            encoded = encode_plantuml(plantuml_code)
            plantuml_response = requests.get(
                f"[https://www.plantuml.com/plantuml/png/](https://www.plantuml.com/plantuml/png/){encoded}",
                timeout=30
            )

            print("=== PlantUML Server Status ===", plantuml_response.status_code)

            if plantuml_response.status_code != 200:
                raise Exception("PlantUML server error")

            file_path = os.path.join(output_dir, file_name)
            with open(file_path, "wb") as file_handle:
                file_handle.write(plantuml_response.content)

            png_base64 = base64.b64encode(plantuml_response.content).decode("ascii")
            return png_base64, file_path

        class_png, class_path = render_png(
            class_plantuml,
            f"class_{timestamp}.png"
        )
        
        sequence_outputs = []
        for index, sequence_data in enumerate(generated_sequences):
            safe_name = sequence_data["name"].replace(" ", "_").lower()
            png_base64, file_path = render_png(
                sequence_data["plantuml"],
                f"{safe_name}_{timestamp}_{index}.png"
            )
            sequence_outputs.append({
                "name": sequence_data["name"],
                "png": png_base64,
                "file": file_path
            })
            
        er_png, er_path = render_png(
            er_plantuml,
            f"er_{timestamp}.png"
        )

        # ====================================
        # FINAL RESPONSE
        # ====================================

        return {
            "structured_data": parsed_json,
            "validation": validation_report,
            "pngs": {
                "class": class_png,
                "sequence": sequence_outputs,
                "er": er_png
            },
            "files": {
                "class": class_path,
                "sequence": [item["file"] for item in sequence_outputs],
                "er": er_path
            },
            "plantuml": {
                "class": class_plantuml,
                "sequence": generated_sequences,
                "er": er_plantuml,
            },
            "iterations_used": iterations_used,
        }