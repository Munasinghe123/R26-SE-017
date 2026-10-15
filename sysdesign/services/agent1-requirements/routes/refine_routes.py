

from fastapi import APIRouter, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
from starlette.concurrency import run_in_threadpool
from controllers.refine_controller import refine_endpoint
from graph.instance import graph
from services.evaluation import evaluate_requirements_suite
from services.meetings_service import get_meeting_requirements

refine_routes = APIRouter()


class RefineRequest(BaseModel):
    requirements: Dict[str, Any]
    feedback: str
    meetingId: str


class EvaluationRequest(BaseModel):
    requirements: Dict[str, Any]
    project_scope: Optional[str] = None
    meetingId: Optional[str] = None


@refine_routes.post('/refine-reqs')
async def refine_extracted_requirements(req: RefineRequest):
    return await refine_endpoint(req)


@refine_routes.post('/evaluate-requirements')
async def evaluate_requirements_endpoint(req: EvaluationRequest):
  
    res = await run_in_threadpool(evaluate_requirements_suite, req.requirements)
    return res


@refine_routes.get("/requirements/{meeting_id}/evaluation")
async def get_requirements_evaluation(meeting_id: str):
    
    # First get the requirements
    req_data = await get_requirements(meeting_id)
    raw_reqs = req_data.get("final_requirements") or req_data.get("requirements") or {}
    res = await run_in_threadpool(evaluate_requirements_suite, raw_reqs)
    return res

@refine_routes.get("/requirements/{meeting_id}")
async def get_requirements(meeting_id: str):
    config = {"configurable": {"thread_id": meeting_id}}
    snapshot = await run_in_threadpool(graph.get_state, config)
    state = dict(snapshot.values) if snapshot and snapshot.values else {}

    # Fallback to DB if memory state is empty (e.g. server restarted)
    if not state.get("final_requirements") and not state.get("requirements"):
        try:
            
            db_data = await get_meeting_requirements(meeting_id)
            if db_data:
                db_reqs = db_data.get("requirements")
                state = {
                    **state,
                    "final_requirements": db_data.get("final_requirements") or db_reqs,
                    "requirements": db_reqs,
                    "client_view": db_data.get("client_view"),
                    "status": db_data.get("status", "completed"),
                    "version": db_data.get("version", 1),
                }
        except Exception as exc:
            print(f"Warning: could not fetch meeting from DB: {exc}")

    final_reqs = state.get("final_requirements") or state.get("requirements") or {}

    return {
        "meeting_id": meeting_id,
        "final_requirements": final_reqs,
        "requirements": state.get("requirements") or final_reqs,
    }