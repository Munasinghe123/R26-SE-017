

from fastapi import APIRouter, UploadFile, File, Form,Query
# from services.meetings_service import get_latest_requirements
from controllers.refine_controller import refine_endpoint
from pydantic import BaseModel
from typing import Dict, Any

from graph.instance import graph

refine_routes = APIRouter()


class RefineRequest(BaseModel):
    requirements: Dict[str, Any]
    feedback: str
    meetingId: str

@refine_routes.post('/refine-reqs')
async def refine_extracted_requirements(req: RefineRequest):
    return await refine_endpoint(req)

from starlette.concurrency import run_in_threadpool

@refine_routes.get("/requirements/{meeting_id}")
async def get_requirements(meeting_id: str):
    config = {"configurable": {"thread_id": meeting_id}}
    state = await run_in_threadpool(graph.get_state, config)
    
    if not state or not state.values:
        return {
            "requirements": {
                "functional": [],
                "non_functional": []
            },
            "version": 1
        }

    reqs = state.values.get("requirements", {})
    
    specified = reqs.get("specified_requirements", {})
    if isinstance(specified, dict):
        functional = specified.get("functional", [])
        non_functional = specified.get("non_functional", [])
    else:
        functional = []
        non_functional = []

    if not functional and "functional" in reqs:
        functional = reqs["functional"]
    if not non_functional and "non_functional" in reqs:
        non_functional = reqs["non_functional"]

    if not functional and "raw" in reqs:
        try:
            from services.extract.extract import parse_json_response
            raw_data = parse_json_response(reqs["raw"])
            if isinstance(raw_data, dict):
                spec = raw_data.get("specified_requirements", raw_data)
                if isinstance(spec, dict):
                    functional = spec.get("functional", [])
                    non_functional = spec.get("non_functional", [])
        except Exception:
            pass

    iteration = state.values.get("iteration_count", 0) or 0

    purpose = reqs.get("purpose", "")
    scope = reqs.get("scope", "")
    external_interfaces = reqs.get("external_interfaces", [])
    design_constraints = reqs.get("design_constraints", [])
    user_characteristics = reqs.get("user_characteristics", [])
    assumptions_and_dependencies = reqs.get("assumptions_and_dependencies", [])
    supporting_information = reqs.get("supporting_information", [])

    return {
        "requirements": {
            "purpose": purpose,
            "scope": scope,
            "functional": functional,
            "non_functional": non_functional,
            "external_interfaces": external_interfaces,
            "design_constraints": design_constraints,
            "user_characteristics": user_characteristics,
            "assumptions_and_dependencies": assumptions_and_dependencies,
            "supporting_information": supporting_information
        },
        "version": iteration + 1
    }