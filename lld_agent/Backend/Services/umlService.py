import os
from datetime import datetime
import zlib
import base64
import requests

from utils.irGenerator import (
  generate_class_plantuml,
  generate_sequence_plantuml,
  generate_er_plantuml
)
from config.config import MAX_ITERATIONS

# Import the newly created LangGraph orchestrator
from graph.graph import build_uml_graph


# ====================================
# PLANTUML ENCODER
# ====================================
def encode_plantuml(plantuml_str):
    # RAW DEFLATE - NO ZLIB HEADER
    compress_obj = zlib.compressobj(
        zlib.Z_BEST_COMPRESSION,
        zlib.DEFLATED,
        -15
    )
    compressed = compress_obj.compress(plantuml_str.encode("utf-8"))
    compressed += compress_obj.flush()

    # PLANTUML CUSTOM BASE64 ALPHABET
    plantuml_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    standard_alphabet  = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    standard_b64 = base64.b64encode(compressed).decode("ascii")

    result = standard_b64.translate(
        str.maketrans(standard_alphabet, plantuml_alphabet)
    )

    return result


class UMLService:

    @staticmethod
    def generate_uml(requirements: str, requirement_ids: list[str] | None = None):
        
        # ====================================
        # 1. INITIALIZE & RUN LANGGRAPH
        # ====================================
        
        # Build and compile the graph
        graph_app = build_uml_graph()
        
        # Set up the initial memory state for the agents
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
        
        # Execute the LangGraph workflow
        final_state = graph_app.invoke(initial_state)

        # Retrieve outputs from the final state
        parsed_json = final_state.get("parsed_json") or {}
        validation_result = final_state.get("validation_result") or {}
        validation_report = validation_result.get("report")
        iterations_used = final_state.get("iterations_used", 1)

        # Catch edge cases where the limit was hit without success
        if not parsed_json:
            raise ValueError("Failed to successfully parse or validate LLM output as JSON within iteration limits.")

        # ====================================
        # 2. GENERATE PLANTUML SYNTAX
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
        # 3. ENCODE + RENDER PNGs
        # ====================================

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "output")
        )
        os.makedirs(output_dir, exist_ok=True)

        def render_png(plantuml_code, file_name):
            encoded = encode_plantuml(plantuml_code)
            plantuml_response = requests.get(
                f"https://www.plantuml.com/plantuml/png/{encoded}",
                timeout=30
            )

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
        # 4. FINAL RESPONSE
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