from __future__ import annotations

import os
import re
import logging
from typing import Dict, Any, Tuple
from fastapi import HTTPException

from graph.srs_state import SRSConfig
from graph.agent import SRSAgent
from utils.pdf_generator import generate_srs_pdf_bytes
from utils.cloudinary_service import upload_srs_pdf_to_cloudinary, is_cloudinary_configured
from utils.logger import (
    log_banner,
    log_request_received,
    log_assembly_complete,
    log_stage_error,
)

logger = logging.getLogger("srs-assembler.service")




class SRSService:
    """
    Business logic and orchestration service for the IEEE 29148 SRS Assembler Agent.
    Handles payload processing, agent execution, PDF compilation, metrics formatting,
    and download dispatching.
    """

    def __init__(self, agent: SRSAgent | None = None) -> None:
        self.agent = agent or SRSAgent()

    def get_health_status(self) -> Dict[str, Any]:
        """Returns service health status and architecture metadata."""
        return {
            "ok": True,
            "service": "srs-assembler",
            "schema": "2.0",
            "architecture": "langgraph-deterministic-repair",
            "cloudinary_configured": is_cloudinary_configured(),
        }

    async def process_assembly_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates full IEEE 29148 Software Requirements Specification (SRS)
        generation using a LangGraph multi-stage pipeline with deterministic validation
        and targeted self-repair.
        """
        try:
            reqs = payload.get("requirements", {})
            hld_annex = payload.get("hld_annex")
            lld_annex = payload.get("lld_annex")
            ui_annex = payload.get("ui_annex")

            project_name = reqs.get("project_name", "Software System")
            job_id = reqs.get("job_id", "job-dev")
            model = payload.get("model") or os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")

            num_in_fr = len(reqs.get("functional_requirements", []))
            num_in_nfr = len(reqs.get("non_functional_requirements", []))

            log_banner("SRS ASSEMBLER AGENT - PROCESSING REQUEST")
            log_request_received(
                job_id=job_id,
                project_name=project_name,
                model=model,
                num_fr=num_in_fr,
                num_nfr=num_in_nfr,
                has_hld=bool(hld_annex),
                has_lld=bool(lld_annex),
                has_ui=bool(ui_annex),
            )

            config = SRSConfig(
                job_id=job_id,
                project_name=project_name,
                provider="openrouter",
                model=model,
                temperature=0.0,
                max_tokens=3500,
            )

            result_state = await self.agent.agenerate(
                config=config,
                requirements=reqs,
                hld_annex=hld_annex,
                lld_annex=lld_annex,
                ui_annex=ui_annex,
            )

            num_fr = len(result_state.functional_section or [])
            num_nfr = len(result_state.non_functional_section or [])

            # Compile in-memory PDF document & upload directly to Cloudinary CDN
            cloudinary_url = None
            if result_state.status != "failed" and result_state.final_srs_markdown:
                try:
                    pdf_bytes = generate_srs_pdf_bytes(
                        srs_markdown=result_state.final_srs_markdown,
                        project_name=result_state.project_name,
                        job_id=result_state.job_id,
                    )
                    # Upload to dedicated Cloudinary
                    cloudinary_url = upload_srs_pdf_to_cloudinary(
                        pdf_bytes=pdf_bytes,
                        job_id=result_state.job_id,
                        project_name=result_state.project_name,
                    )
                except Exception as pdf_err:
                    logger.error(f"[PDF Compilation Error]: {pdf_err}", exc_info=True)
                    log_stage_error("PDF Compilation", pdf_err.__class__.__name__, str(pdf_err))
            else:
                log_stage_error(
                    "PDF Generation Guard",
                    "PipelineFailedOrEmpty",
                    f"Skipping PDF compilation & upload. Status: {result_state.status}, Markdown Length: {len(result_state.final_srs_markdown or '')}",
                )

            log_assembly_complete(
                status=result_state.status,
                total_tokens=result_state.metrics.total_tokens,
                total_latency_ms=result_state.metrics.total_latency_ms,
                pdf_path=cloudinary_url,
            )

            return {
                "status": result_state.status,
                "job_id": result_state.job_id,
                "project_name": result_state.project_name,
                "srs_markdown": result_state.final_srs_markdown,
                "srs_ir": result_state.final_ir,
                "pdf_url": cloudinary_url,
                "cloudinary_url": cloudinary_url,
                "repair_metadata": result_state.repair_metadata,
                "summary": (
                    f"IEEE 29148 SRS assembled ({result_state.status.upper()}) with "
                    f"{num_fr} FRs, {num_nfr} NFRs, and RTM."
                ),
                "metrics": {
                    "total_tokens": result_state.metrics.total_tokens,
                    "total_latency_ms": result_state.metrics.total_latency_ms,
                    "model_call_count": result_state.metrics.model_call_count,
                    "stages": {
                        k: {
                            "tokens": v.total_tokens,
                            "latency_ms": v.latency_ms,
                            "model": v.model,
                        }
                        for k, v in result_state.metrics.stages.items()
                    },
                },
                "validations": {
                    "overview": result_state.overview_validation,
                    "functional": result_state.functional_validation,
                    "non_functional": result_state.non_functional_validation,
                    "traceability": result_state.traceability_validation,
                },
            }
        except Exception as e:
            logger.error(f"[SRS ASSEMBLER ERROR] Unhandled failure in process_assembly_request: {e}", exc_info=True)
            log_stage_error("Pipeline Orchestration", e.__class__.__name__, str(e))
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"SRS Assembly failed: {str(e)}")

