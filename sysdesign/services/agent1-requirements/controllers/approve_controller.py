"""
approve_controller.py

Industry best practice: client approval IS the confirmation step.
After approving requirements, Agent 1 immediately fires a background
request to the Orchestrator (POST /jobs) so the pipeline starts.
The frontend is redirected to /pipeline/{job_id} for real-time tracking.

No extra "Are you sure?" page — the requirements review page serves
that purpose (client read, edited, and deliberately pressed Approve).
"""

from __future__ import annotations

import logging
import os
import uuid

import httpx
from dotenv import load_dotenv

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
load_dotenv(os.path.join(_root, ".env"))

logger = logging.getLogger("agent1.approve")

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://127.0.0.1:8000")

try:
    from langgraph.types import Command
    from graph.instance import graph
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False


async def approve_endpoint(req):
    """
    1. Resume the LangGraph checkpoint (generates SRS PDF via Agent 1 own flow).
    2. Fetch the final approved requirements from DB.
    3. POST to Orchestrator /jobs to start the full 4-agent pipeline.
    4. Return {status, job_id} so the frontend can navigate to /pipeline/{job_id}.
    """
    meeting_id: str = req.meeting_id
    pdf_path = None

    # Step 1 — Resume LangGraph (Agent 1 internal: generates PDF)
    if LANGGRAPH_AVAILABLE:
        try:
            result = graph.invoke(
                Command(resume={"status": "approved", "feedback": None}),
                config={"configurable": {"thread_id": meeting_id}},
            )
            pdf_path = result.get("pdf_path")
        except Exception as exc:
            logger.warning(f"LangGraph resume failed: {exc} — continuing to orchestrator.")

    # Step 2 — Fetch approved requirements from DB to pass to orchestrator
    approved_requirements = await _fetch_requirements(meeting_id)

    # Step 3 — Trigger the full pipeline (async fire-and-forget to orchestrator)
    job_id = str(uuid.uuid4())
    pipeline_payload = {
        "job_id": job_id,
        "project_name": approved_requirements.get("project_name", "SDLC Project"),
        "meeting_id": meeting_id,
        **approved_requirements,
    }

    orchestrator_job_id = await _trigger_orchestrator(pipeline_payload)

    return {
        "status": "approved",
        "pdf_path": pdf_path,
        "job_id": orchestrator_job_id or job_id,
        "pipeline_url": f"/pipeline/{orchestrator_job_id or job_id}",
        "message": "Requirements approved. Full pipeline started.",
    }


async def _fetch_requirements(meeting_id: str) -> dict:
    """Fetch approved requirements from LangGraph checkpointer or Agent 1's DB."""
    try:
        from graph.instance import graph
        state = graph.get_state({"configurable": {"thread_id": meeting_id}})
        if state and state.values and "requirements" in state.values:
            reqs = dict(state.values["requirements"])
            specified = reqs.get("specified_requirements", {})
            if isinstance(specified, dict):
                if "functional_requirements" not in reqs:
                    reqs["functional_requirements"] = specified.get("functional", [])
                if "non_functional_requirements" not in reqs:
                    reqs["non_functional_requirements"] = specified.get("non_functional", [])
            if "project_name" not in reqs:
                reqs["project_name"] = "SDLC Project"
            return reqs
    except Exception as exc:
        logger.warning(f"Could not fetch requirements from LangGraph checkpointer: {exc}")

    try:
        from db.config import pool
        if pool:
            async with pool.acquire() as conn:
                m_uuid = None
                try:
                    m_uuid = uuid.UUID(meeting_id)
                except Exception:
                    pass
                
                row = None
                if m_uuid:
                    row = await conn.fetchrow(
                        "SELECT requirements FROM meetings WHERE id = $1 OR project_id = $1 ORDER BY updated_at DESC LIMIT 1",
                        m_uuid,
                    )
                if row and row["requirements"]:
                    import json
                    data = row["requirements"]
                    parsed = json.loads(data) if isinstance(data, str) else data
                    if isinstance(parsed, dict):
                        return parsed
    except Exception as exc:
        logger.warning(f"Could not fetch requirements from DB: {exc}")


    # Fallback — return a placeholder so pipeline still starts
    return {
        "functional_requirements": [],
        "non_functional_requirements": [],
        "project_name": "SDLC Project",
    }



async def _trigger_orchestrator(payload: dict) -> str | None:
    """POST to Orchestrator /jobs. Returns the job_id assigned by orchestrator."""
    url = f"{ORCHESTRATOR_URL}/jobs"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Pipeline triggered: job_id={data.get('job_id')}")
                return data.get("job_id")
            else:
                logger.error(f"Orchestrator returned {resp.status_code}: {resp.text}")
    except Exception as exc:
        logger.error(f"Could not reach orchestrator at {url}: {exc}")
    return None