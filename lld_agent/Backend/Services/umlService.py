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
from config.config import MAX_ITERATIONS, USE_CANDIDATE_PIPELINE
from Services.candidateService import CandidateService

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
    def generate_candidate_internal(requirements: str, requirement_ids: list[str] | None = None):
        return CandidateService.run_candidate_internal(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )

    @staticmethod
    def generate_uml(requirements: str, requirement_ids: list[str] | None = None):
        if USE_CANDIDATE_PIPELINE:
            return UMLService._generate_uml_candidate(
                requirements=requirements,
                requirement_ids=requirement_ids or [],
            )
        return UMLService._generate_uml_legacy(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )

    @staticmethod
    def _generate_uml_legacy(requirements: str, requirement_ids: list[str] | None = None):
        
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

        return UMLService._build_rendered_response(
            parsed_json=parsed_json,
            validation_report=validation_report,
            iterations_used=iterations_used,
        )

    @staticmethod
    def _generate_uml_candidate(requirements: str, requirement_ids: list[str] | None = None):
        candidate_configs = [
            CandidateService.get_candidate_1_config(),
            CandidateService.get_candidate_2_config(),
            # CandidateService.get_candidate_3_config(),
        ]
        print(candidate_configs)
        candidate_outputs: list[dict] = []
        primary_candidate = None

        for candidate_config in candidate_configs:
            candidate = CandidateService.run_candidate_internal(
                requirements=requirements,
                requirement_ids=requirement_ids or [],
                candidate_config=candidate_config,
            )
            print(candidate)
            candidate_outputs.append(_serialize_candidate_output(candidate))
            if primary_candidate is None:
                primary_candidate = candidate

            result = UMLService._build_rendered_response(
                        parsed_json=candidate.final_ir,
                        validation_report=_aggregate_candidate_validation(candidate),
                        iterations_used=1,
                    )

        #if primary_candidate is None or primary_candidate.status == "failed" or not primary_candidate.final_ir:
            #raise ValueError(_candidate_failure_message(primary_candidate))

        result = UMLService._build_rendered_response(
            parsed_json=primary_candidate.final_ir,
            validation_report=_aggregate_candidate_validation(primary_candidate),
            iterations_used=1,
        )
        result["candidate_outputs"] = candidate_outputs
        result["selected_candidate_id"] = primary_candidate.candidate_id
        return result

    @staticmethod
    def _build_rendered_response(parsed_json: dict, validation_report: dict | None, iterations_used: int):
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


def _candidate_failure_message(candidate) -> str:
    if candidate.provider_errors:
        stage = candidate.provider_errors[0].get("stage", "unknown")
        return f"Candidate generation failed during {stage} provider execution."
    if candidate.parse_errors:
        stage = candidate.parse_errors[0].get("stage", "unknown")
        return f"Candidate generation failed because {stage} output could not be parsed."
    return "Candidate generation failed before a complete UML IR was available."


def _aggregate_candidate_validation(candidate) -> dict:
    stage_validations = {
        "class": candidate.class_validation,
        "er": candidate.er_validation,
        "sequence": candidate.sequence_validation,
    }

    errors = []
    total_checks = 0
    passed_checks = 0

    for stage, validation in stage_validations.items():
        validation = validation or {}
        total_checks += int(validation.get("total_checks", 0) or 0)
        passed_checks += int(validation.get("passed_checks", 0) or 0)

        for error in validation.get("errors", []) or []:
            errors.append({
                **error,
                "stage": stage,
            })

        for warning in validation.get("warnings", []) or []:
            errors.append({
                **warning,
                "stage": stage,
                "severity": "low",
            })

    passed = candidate.status == "valid" and not any(
        error.get("severity") in ("critical", "high", "medium")
        for error in errors
    )
    consistency_score = round((passed_checks / total_checks * 100), 2) if total_checks else 0.0

    return {
        "passed": passed,
        "consistency_score": consistency_score,
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "errors": errors,
        "traceability_matrix": [],
        "overdesign_flags": [],
        "naming_violations": [],
        "naming_violations_fixed": 0,
    }


def _serialize_candidate_output(candidate) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "provider": candidate.provider,
        "model": candidate.model,
        "status": candidate.status,
        "final_ir": candidate.final_ir,
        "validation": {
            "class": candidate.class_validation,
            "er": candidate.er_validation,
            "sequence": candidate.sequence_validation,
            "aggregate": _aggregate_candidate_validation(candidate),
        },
        "errors": {
            "provider": candidate.provider_errors,
            "parse": candidate.parse_errors,
        },
        "metrics": {
            "total_tokens": candidate.metrics.total_tokens,
            "total_latency_ms": candidate.metrics.total_latency_ms,
            "model_call_count": candidate.metrics.model_call_count,
        },
    }
