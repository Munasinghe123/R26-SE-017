import base64
import logging
import uuid
import zlib
import requests

from utils.irGenerator import (
  generate_class_plantuml,
  generate_sequence_plantuml,
  generate_er_plantuml
)
from Services.agenticReconciliation import AgenticReconciliationService
from Services.candidateService import CandidateService
from Services.expertReviewService import ExpertReviewService
from Services.multiAgentGeneration import MultiAgentGenerationResult
from Services.validationService import ValidationService
from graph.ensemble_graph import arun_multi_agent_graph, run_multi_agent_graph
from utils.irMapper import convert_to_ir
from Services.cloudinary_service import upload_png_to_cloudinary


logger = logging.getLogger(__name__)


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
    def generate_candidates_internal(requirements: str, requirement_ids: list[str] | None = None):
        return CandidateService.run_all_candidates_internal(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )

    @staticmethod
    def generate_multi_agent_internal(requirements: str, requirement_ids: list[str] | None = None):
        return run_multi_agent_graph(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            candidate_configs=CandidateService.get_candidate_configs(),
        )

    @staticmethod
    async def agenerate_multi_agent_internal(requirements: str, requirement_ids: list[str] | None = None):
        return await arun_multi_agent_graph(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            candidate_configs=CandidateService.get_candidate_configs(),
        )

    @staticmethod
    def generate_uml(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None):
        return UMLService._generate_uml_multi_agent(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
        )

    @staticmethod
    async def agenerate_uml(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None):
        return await UMLService._agenerate_uml_multi_agent(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
        )


    @staticmethod
    def _generate_uml_multi_agent(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None):
        multi_agent_result = UMLService.generate_multi_agent_internal(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )
        return UMLService._render_multi_agent_result(
            multi_agent_result=multi_agent_result,
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
        )

    @staticmethod
    async def _agenerate_uml_multi_agent(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None):
        multi_agent_result = await UMLService.agenerate_multi_agent_internal(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )
        return UMLService._render_multi_agent_result(
            multi_agent_result=multi_agent_result,
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
        )

    @staticmethod
    def _render_multi_agent_result(
        *,
        multi_agent_result: MultiAgentGenerationResult,
        requirements: str,
        requirement_ids: list[str],
        project_id: int | None = None,
    ):
        selected_candidate = multi_agent_result.selected_candidate

        if selected_candidate is None:
            raise ValueError("Multi-agent generation failed because no usable candidate was selected.")
        if not selected_candidate.final_ir:
            raise ValueError(_candidate_failure_message(selected_candidate))

        validation_result = multi_agent_result.initial_validation_result
        if validation_result is None:
            validation_result = ValidationService.validate(
                convert_to_ir(selected_candidate.final_ir),
                requirement_ids=requirement_ids or [],
            )
        final_validation_report = dict(validation_result.get("report") or {})
        final_validation_report["expert_guidance"] = validation_result.get("expert_guidance", "")
        final_validation_report["stage_validation"] = _aggregate_candidate_validation(selected_candidate)
        final_validation_report["repair"] = selected_candidate.repair_metadata

        reconciliation = multi_agent_result.reconciliation
        if reconciliation is None:
            reconciliation = AgenticReconciliationService.reconcile(
                selected_final_ir=selected_candidate.final_ir,
                requirements=requirements,
                requirement_ids=requirement_ids or [],
                initial_validation_result=validation_result,
                context={
                    "selected_candidate_id": selected_candidate.candidate_id,
                    "class_diagram": selected_candidate.class_diagram,
                    "er_diagram": selected_candidate.er_diagram,
                    "sequence_diagrams": selected_candidate.sequence_diagrams,
                    "expert_review": {
                        "reason": multi_agent_result.expert_review.reason,
                        "confidence": multi_agent_result.expert_review.confidence,
                        "fallback_used": multi_agent_result.expert_review.fallback_used,
                    },
                },
            )
        final_validation_report = dict(reconciliation.validation_report or final_validation_report)
        final_validation_report["expert_guidance"] = validation_result.get("expert_guidance", "")
        final_validation_report["stage_validation"] = _aggregate_candidate_validation(selected_candidate)
        final_validation_report["repair"] = {
            "stage": selected_candidate.repair_metadata,
            "agentic_reconciliation": reconciliation.repair_metadata,
        }
        final_validation_report["agent_trace"] = reconciliation.agent_trace
        final_validation_report["agentic_reconciliation"] = reconciliation.metadata()

        _log_multi_agent_summary(multi_agent_result)

        result = UMLService._build_rendered_response(
            parsed_json=reconciliation.final_ir,
            validation_report=final_validation_report,
            iterations_used=reconciliation.iterations,
            project_id=project_id,
        )
        result["selected_candidate_id"] = selected_candidate.candidate_id
        result["multi_agent"] = {
            "selected_candidate_id": selected_candidate.candidate_id,
            "expert_review": {
                "reason": multi_agent_result.expert_review.reason,
                "confidence": multi_agent_result.expert_review.confidence,
                "fallback_used": multi_agent_result.expert_review.fallback_used,
            },
            "repair": selected_candidate.repair_metadata,
            "agent_trace": reconciliation.agent_trace,
            "agentic_reconciliation": reconciliation.metadata(),
            "orchestration": {
                "total_agents": multi_agent_result.orchestration.total_agents,
                "valid_agents": multi_agent_result.orchestration.valid_agents,
                "invalid_agents": multi_agent_result.orchestration.invalid_agents,
                "failed_agents": multi_agent_result.orchestration.failed_agents,
                "total_model_calls": multi_agent_result.orchestration.total_model_calls,
                "total_tokens": multi_agent_result.orchestration.total_tokens,
                "total_latency_ms": multi_agent_result.orchestration.total_latency_ms,
            },
        }
        return result

    @staticmethod
    def _build_rendered_response(parsed_json: dict, validation_report: dict | None, iterations_used: int, project_id: int | None = None):
        class_plantuml = generate_class_plantuml(parsed_json.get("class_diagram", {}))
        #print(class_plantuml)
        sequence_diagrams = parsed_json.get("sequence_diagrams", [])

        generated_sequences = []
        for seq in sequence_diagrams:
            sequence_plantuml = generate_sequence_plantuml(seq)
            generated_sequences.append({
                "name": seq.get("name", "sequence"),
                "plantuml": sequence_plantuml
            })

        er_plantuml = generate_er_plantuml(parsed_json.get("er_diagram", {}))

        def render_png(plantuml_code: str, diagram_type: str, name: str | None = None):
            if not plantuml_code:
                return ""
            try:
                encoded = encode_plantuml(plantuml_code)
                png_url = f"https://www.plantuml.com/plantuml/png/~1{encoded}"
                resp = requests.get(png_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
                if resp.status_code == 200 and resp.content:
                    c_url = upload_png_to_cloudinary(
                        resp.content,
                        project_id=project_id,
                        diagram_type=diagram_type,
                        public_id=f"{diagram_type}_{name or 'diagram'}"
                    )
                    if c_url:
                        return c_url
                return f"https://www.plantuml.com/plantuml/svg/~1{encoded}"
            except Exception as e:
                logger.warning(f"PlantUML Cloudinary render/upload warning: {e}")
                try:
                    encoded = encode_plantuml(plantuml_code)
                    return f"https://www.plantuml.com/plantuml/svg/~1{encoded}"
                except Exception:
                    return ""

        class_url = render_png(class_plantuml, "class", "class_diagram")

        sequence_outputs = []
        for index, sequence_data in enumerate(generated_sequences):
            sequence_type = "sequence"
            sequence_url = render_png(sequence_data["plantuml"], sequence_type, f"sequence_{index + 1}")
            sequence_outputs.append({
                "name": sequence_data["name"],
                "cloudinary_url": sequence_url,
                "plantuml": sequence_data.get("plantuml", ""),
            })
            
        er_url = render_png(er_plantuml, "er", "er_diagram")

        result = {
            "structured_data": parsed_json,
            "validation": validation_report,
            "pngs": {
                "class": class_url,
                "sequence": [
                    {"name": item["name"], "png": item["cloudinary_url"], "cloudinary_url": item["cloudinary_url"]}
                    for item in sequence_outputs
                ],
                "er": er_url,
            },
            "cloudinary_urls": {
                "class": class_url,
                "sequence": sequence_outputs,
                "er": er_url,
            },
            "files": {
                "class": class_url,
                "sequence": [item["cloudinary_url"] for item in sequence_outputs],
                "er": er_url,
            },
            "plantuml": {
                "class": class_plantuml,
                "sequence": generated_sequences,
                "er": er_plantuml,
            },
            "iterations_used": iterations_used,
        }

        if project_id is not None:
            UMLService._persist_diagrams(project_id=project_id, diagram_urls={
                "class": class_url,
                "sequence": sequence_outputs,
                "er": er_url,
            }, plantuml=result["plantuml"])

        return result

    @staticmethod
    def _persist_diagrams(project_id: int, diagram_urls: dict, plantuml: dict):
        from database import SessionLocal
        from models.diagram import Diagram

        session = None
        try:
            session = SessionLocal()
            records = []
            records.append({
                "diagram_type": "class",
                "plantuml_code": plantuml.get("class", ""),
                "cloudinary_url": diagram_urls.get("class", ""),
            })
            for index, sequence in enumerate(plantuml.get("sequence", []) or []):
                seq_url = (diagram_urls.get("sequence", []) or [])[index].get("cloudinary_url") if index < len(diagram_urls.get("sequence", []) or []) else ""
                records.append({
                    "diagram_type": "sequence",
                    "plantuml_code": sequence.get("plantuml", ""),
                    "cloudinary_url": seq_url,
                })
            er_url = diagram_urls.get("er", "")
            records.append({
                "diagram_type": "er",
                "plantuml_code": plantuml.get("er", ""),
                "cloudinary_url": er_url,
            })

            for record in records:
                if not record["cloudinary_url"]:
                    raise ValueError(f"Cloudinary URL missing for {record['diagram_type']} diagram; DB persistence aborted.")
                session.add(Diagram(
                    project_id=project_id,
                    diagram_type=record["diagram_type"],
                    plantuml_code=record["plantuml_code"],
                    cloudinary_url=record["cloudinary_url"],
                ))

            session.commit()
            logger.info("diagram_database_save_successful", extra={"project_id": project_id, "record_count": len(records)})
        except Exception:
            logger.exception("diagram_database_save_failed", extra={"project_id": project_id})
            raise
        finally:
            if session is not None:
                session.close()


def _candidate_failure_message(candidate) -> str:
    if candidate.provider_errors:
        stage = candidate.provider_errors[0].get("stage", "unknown")
        return f"Candidate generation failed during {stage} provider execution."
    if candidate.parse_errors:
        stage = candidate.parse_errors[0].get("stage", "unknown")
        return f"Candidate generation failed because {stage} output could not be parsed."
    return "Candidate generation failed before a complete UML IR was available."


def _log_multi_agent_summary(result: MultiAgentGenerationResult) -> None:
    candidate_summary = {
        candidate_id: {
            "status": candidate.status,
            "model": candidate.model,
        }
        for candidate_id, candidate in result.orchestration.candidates.items()
    }  
    expert_metrics = result.expert_review.metrics
    logger.info(
        "multi_agent_generation_summary",
        extra={
            "candidate_summary": candidate_summary,
            "selected_candidate_id": result.expert_review.selected_candidate_id,
            "expert_confidence": result.expert_review.confidence,
            "fallback_used": result.expert_review.fallback_used,
            "total_candidate_model_calls": result.orchestration.total_model_calls,
            "total_candidate_tokens": result.orchestration.total_tokens,
            "orchestration_latency_ms": result.orchestration.total_latency_ms,
            "expert_latency_ms": expert_metrics.latency_ms if expert_metrics else None,
        },
    )


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
        "repair": candidate.repair_metadata,
    }
