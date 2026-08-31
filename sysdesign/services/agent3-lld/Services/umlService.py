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

    return result.replace("=", "0")


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
    def generate_uml(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None, generation_run_id: int | None = None):
        return UMLService._generate_uml_multi_agent(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
            generation_run_id=generation_run_id,
        )

    @staticmethod
    async def agenerate_uml(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None, generation_run_id: int | None = None):
        return await UMLService._agenerate_uml_multi_agent(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
            generation_run_id=generation_run_id,
        )

    @staticmethod
    def _generate_uml_multi_agent(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None, generation_run_id: int | None = None):
        multi_agent_result = UMLService.generate_multi_agent_internal(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )
        return UMLService._render_multi_agent_result(
            multi_agent_result=multi_agent_result,
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
            generation_run_id=generation_run_id,
        )

    @staticmethod
    async def _agenerate_uml_multi_agent(requirements: str, requirement_ids: list[str] | None = None, project_id: int | None = None, generation_run_id: int | None = None):
        multi_agent_result = await UMLService.agenerate_multi_agent_internal(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )
        return UMLService._render_multi_agent_result(
            multi_agent_result=multi_agent_result,
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            project_id=project_id,
            generation_run_id=generation_run_id,
        )

    @staticmethod
    def _render_multi_agent_result(
        *,
        multi_agent_result: MultiAgentGenerationResult,
        requirements: str,
        requirement_ids: list[str],
        project_id: int | None = None,
        generation_run_id: int | None = None,
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

        # =========================================================
        # RESEARCH EVALUATION PIPELINE (POST-REFINEMENT & RENDER)
        # =========================================================
        try:
            UMLService._run_and_print_evaluation(
                result=result,
                requirements_text=requirements,
                requirement_ids=requirement_ids or [],
                project_id=project_id,
                generation_run_id=generation_run_id,
                candidate_id=selected_candidate.candidate_id if selected_candidate else None,
            )
        except Exception as eval_exc:
            logger.exception("research_evaluation_execution_failed", extra={"error": str(eval_exc)})

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
            logger.info("plantuml_render_started", extra={"diagram_type": diagram_type})
            encoded = encode_plantuml(plantuml_code)
            try:
                plantuml_response = requests.get(
                    f"https://www.plantuml.com/plantuml/png/{encoded}",
                    timeout=30,
                )

                if plantuml_response.status_code != 200:
                    logger.error("plantuml_render_failed", extra={"diagram_type": diagram_type, "status_code": plantuml_response.status_code})
                    return f"https://www.plantuml.com/plantuml/png/{encoded}"

                logger.info("plantuml_render_successful", extra={"diagram_type": diagram_type, "bytes": len(plantuml_response.content)})
                public_id = f"{name or diagram_type}_{uuid.uuid4().hex[:8]}"
                cloudinary_url = upload_png_to_cloudinary(
                    png_bytes=plantuml_response.content,
                    project_id=project_id,
                    diagram_type=diagram_type,
                    public_id=public_id,
                )
                return cloudinary_url
            except Exception as exc:
                logger.warning(f"PlantUML render fallback used due to: {exc}")
                return f"https://www.plantuml.com/plantuml/png/{encoded}"

        class_url = render_png(class_plantuml, "class", "class_diagram")

        sequence_outputs = []
        for index, sequence_data in enumerate(generated_sequences):
            sequence_type = "sequence"
            sequence_url = render_png(sequence_data["plantuml"], sequence_type, f"sequence_{index + 1}")
            sequence_outputs.append({
                "name": sequence_data["name"],
                "cloudinary_url": sequence_url,
            })
        # Normalize: generate_er_plantuml may return a string or a list of strings (pages)
        if isinstance(er_plantuml, str):
            er_plantuml = [er_plantuml]

        print("===== ER PLANTUML =====")
        for i, pu in enumerate(er_plantuml):
            print(f"--- Page {i+1} ---")
            print(pu)
        print("=======================")
            
        if len(er_plantuml) == 1:
            er_url = render_png(er_plantuml[0], "er", "er_diagram")
        else:
            er_url = [
                render_png(pu, "er", f"er_diagram_p{i+1}")
                for i, pu in enumerate(er_plantuml)
            ]

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
    def _run_and_print_evaluation(
        *,
        result: dict,
        requirements_text: str,
        requirement_ids: list[str],
        project_id: int | str | None = None,
        generation_run_id: int | None = None,
        candidate_id: int | None = None,
    ):
        import dataclasses
        from evaluation.evaluator import Evaluator
        from utils.irMapper import convert_to_ir

        req_list = UMLService._extract_requirements_from_input(requirements_text, requirement_ids or [])

        # Normalize post-refinement IR
        final_ir_dict = result.get("structured_data", {})
        if final_ir_dict:
            try:
                ir_obj = convert_to_ir(final_ir_dict)
                normalized_ir = dataclasses.asdict(ir_obj)
            except Exception:
                normalized_ir = final_ir_dict
        else:
            normalized_ir = {}

        eval_input = {
            "ir": normalized_ir,
            "diagrams": result.get("plantuml", {}),
        }

        evaluator = Evaluator()
        ref_data = {}
        has_reference = False
        target_case = None

        try:
            import re
            from evaluation.reference_loader import ReferenceLoader

            def _norm(s: str) -> str:
                cleaned = UMLService._clean_requirement_text(s)
                return cleaned.lower()

            input_req_ids = {r["id"].strip().upper() for r in req_list if r.get("id")}
            input_req_texts = {_norm(r["text"]) for r in req_list if r.get("text")}

            loader = ReferenceLoader()
            if loader.references_dir.exists():
                for case_dir in loader.references_dir.iterdir():
                    if not case_dir.is_dir():
                        continue
                    case_id = case_dir.name
                    try:
                        case_ref = loader.load_case(case_id)
                        ref_reqs = case_ref.get("requirements", {}).get("requirements", []) or []
                        ref_req_ids = {r["id"].strip().upper() for r in ref_reqs if r.get("id")}
                        ref_req_texts = {_norm(r["text"]) for r in ref_reqs if r.get("text")}

                        # Priority 1: Complete requirement ID set equality
                        id_match = bool(input_req_ids and ref_req_ids and input_req_ids == ref_req_ids)

                        # Priority 2: Complete requirement text set equality
                        text_match = bool(input_req_texts and ref_req_texts and input_req_texts == ref_req_texts)

                        if id_match or text_match:
                            ref_data = case_ref
                            has_reference = True
                            target_case = case_id
                            break
                    except Exception:
                        continue
        except Exception as ref_err:
            logger.warning(f"Could not load reference case for evaluation: {ref_err}")

        eval_result = evaluator.evaluate(
            generated=eval_input,
            reference=ref_data,
            requirements=req_list,
        )

        UMLService._print_research_evaluation_summary(
            eval_result=eval_result,
            has_reference=has_reference,
            target_case=target_case,
        )

    @staticmethod
    def _clean_requirement_text(raw_text: str) -> str:
        import re
        s = str(raw_text or "").strip()
        # Extract content after "Description:" if present
        desc_match = re.search(r"description\s*:\s*(.+)$", s, flags=re.IGNORECASE)
        if desc_match:
            s = desc_match.group(1).strip()
        # Remove leading bullets, numbering
        s = re.sub(r"^[-*•\d.]+\s*", "", s)
        # Remove bracketed IDs (e.g. [FR-1], [REQ-001])
        s = re.sub(r"^\[[A-Za-z0-9_-]+\]\s*[:|-]?\s*", "", s)
        # Remove unbracketed IDs starting with FR/REQ/NFR/R followed by digits (e.g. FR-1:, REQ-001:, FR1)
        s = re.sub(r"^(?:FR|REQ|NFR|R)[-_.]?\d+\w*\s*[:|-]?\s*", "", s, flags=re.IGNORECASE)
        # Remove leftover "Description:" prefix if present
        s = re.sub(r"^(?:description|desc)\s*:\s*", "", s, flags=re.IGNORECASE)
        # Collapse whitespace
        return re.sub(r"\s+", " ", s).strip()

    @staticmethod
    def _extract_requirements_from_input(requirements_text: str, requirement_ids: list[str]) -> list[dict]:
        import re
        req_list = []
        if requirement_ids:
            req_text_map = {}
            if requirements_text:
                current_id = None
                for line in requirements_text.splitlines():
                    sline = line.strip()
                    matched_id = None
                    for rid in requirement_ids:
                        if f"[{rid}]" in sline or sline.startswith(f"{rid}:") or sline.startswith(f"{rid} "):
                            matched_id = rid
                            break
                    if matched_id:
                        current_id = matched_id
                        req_text_map[current_id] = sline
                    elif current_id and sline:
                        req_text_map[current_id] += " " + sline

            for req_id in requirement_ids:
                raw_text = req_text_map.get(req_id, requirements_text.strip() if requirements_text else f"{req_id}")
                cleaned_text = UMLService._clean_requirement_text(raw_text)
                req_list.append({"id": req_id, "text": cleaned_text or raw_text})
        elif requirements_text and requirements_text.strip():
            lines = [l.strip() for l in requirements_text.splitlines() if l.strip()]
            req_items = []
            for line in lines:
                match = re.match(r"^[-*]?\s*\[?([A-Za-z0-9_-]+)\]?\s*[:|-]?\s*(.+)", line)
                if match and ("REQ" in match.group(1).upper() or "FR" in match.group(1).upper() or "R" in match.group(1).upper()):
                    cleaned_line = UMLService._clean_requirement_text(match.group(2))
                    req_items.append({"id": match.group(1), "text": cleaned_line or match.group(2)})
            if req_items:
                req_list = req_items
            else:
                cleaned_full = UMLService._clean_requirement_text(requirements_text)
                req_list = [{"id": "REQ-1", "text": cleaned_full or requirements_text.strip()}]
        return req_list

    @staticmethod
    def _print_research_evaluation_summary(*, eval_result: dict, has_reference: bool, target_case: str | None = None):
        class_res = eval_result.get("class", {})
        seq_res = eval_result.get("sequence", {})
        er_res = eval_result.get("er", {})
        req_res = eval_result.get("requirements", {})
        syntax_res = eval_result.get("syntax", {})

        req_cov = req_res.get("coverage_score", 0.0) * 100.0
        syntax_score = syntax_res.get("overall_score", 0.0) * 100.0

        def extract_p_r(res_dict, keys):
            if not has_reference or not res_dict:
                return None, None
            p_list = [res_dict.get(k, {}).get("precision", 0.0) for k in keys if k in res_dict]
            r_list = [res_dict.get(k, {}).get("recall", 0.0) for k in keys if k in res_dict]
            p = (sum(p_list) / len(p_list)) if p_list else 0.0
            r = (sum(r_list) / len(r_list)) if r_list else 0.0
            return p, r

        c_p, c_r = extract_p_r(class_res, ["classes", "attributes", "methods", "relationships"])
        c_f1 = class_res.get("overall_f1") if has_reference else None

        s_p, s_r = extract_p_r(seq_res, ["participants", "messages"])
        s_f1 = seq_res.get("overall_f1") if has_reference else None
        s_order = seq_res.get("message_order", {}).get("score") if has_reference else None

        e_p, e_r = extract_p_r(er_res, ["entities", "attributes", "relationships"])
        e_f1 = er_res.get("overall_f1") if has_reference else None

        def fmt_val(val):
            if not has_reference or val is None:
                return "N/A"
            return f"{val * 100.0:.2f}%"

        ref_block = (
            f"Reference Used: YES\nReference Case: {target_case}\n========================"
            if has_reference
            else "Reference Used: NO\n=================="
        )

        summary_text = f"""
        ============================================================
        RESEARCH DIAGRAM EVALUATION
        ===========================

        Class Diagram
        Precision : {fmt_val(c_p)}
        Recall    : {fmt_val(c_r)}
        F1        : {fmt_val(c_f1)}

        Sequence Diagram
        Precision : {fmt_val(s_p)}
        Recall    : {fmt_val(s_r)}
        F1        : {fmt_val(s_f1)}
        Order     : {fmt_val(s_order)}

        ER Diagram
        Precision : {fmt_val(e_p)}
        Recall    : {fmt_val(e_r)}
        F1        : {fmt_val(e_f1)}

        Requirement Coverage  : {req_cov:.2f}%
        Syntax / Renderability: {syntax_score:.2f}%

        {ref_block}
        """
        print(summary_text, flush=True)
        logger.info("research_diagram_evaluation_completed\n" + summary_text)

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
            er_data = diagram_urls.get("er", "")
            er_pus = plantuml.get("er", "")
            if isinstance(er_data, list):
                for i, url in enumerate(er_data):
                    pu_code = er_pus[i] if isinstance(er_pus, list) and i < len(er_pus) else ""
                    records.append({
                        "diagram_type": "er",
                        "plantuml_code": pu_code,
                        "cloudinary_url": url,
                    })
            else:
                records.append({
                    "diagram_type": "er",
                    "plantuml_code": er_pus if isinstance(er_pus, str) else (er_pus[0] if er_pus else ""),
                    "cloudinary_url": er_data,
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
        except Exception as exc:
            logger.warning("diagram_database_save_failed_continuing", extra={"project_id": project_id, "error": str(exc)})
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
