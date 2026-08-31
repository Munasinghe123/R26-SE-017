

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
    
    reqs = None
    final_reqs = None
    cview = None
    iteration = 0

    if state and state.values:
        reqs = state.values.get("requirements")
        final_reqs = state.values.get("final_requirements")
        cview = state.values.get("client_view")
        iteration = state.values.get("iteration_count", 0) or 0

    # Fallback to DB or persistent file cache if state in memory is empty
    if not reqs and not final_reqs:
        try:
            from services.meetings_service import get_meeting_requirements
            db_data = await get_meeting_requirements(meeting_id)
            if db_data:
                reqs = db_data.get("requirements")
                final_reqs = db_data.get("final_requirements")
                cview = db_data.get("client_view")
                iteration = max(0, (db_data.get("version", 1) or 1) - 1)
        except Exception as exc:
            print(f"Warning: could not fetch meeting from DB: {exc}")

    if not reqs and not final_reqs:
        return {
            "requirements": {
                "functional": [],
                "non_functional": []
            },
            "client_view": None,
            "version": 1
        }

    reqs = reqs or {}
    functional = []
    non_functional = []

    # If final_requirements from HITL reconciliation is present, extract directly
    if final_reqs and isinstance(final_reqs, dict) and "sections" in final_reqs:
        for section in final_reqs.get("sections", []):
            stitle = section.get("title", "").lower()
            for item in section.get("items", []):
                mapped = {
                    "id": item.get("id"),
                    "description": item.get("text") or item.get("description", "")
                }
                if "non" in stitle or item.get("type") == "non_functional":
                    non_functional.append(mapped)
                else:
                    functional.append(mapped)
    else:
        # Normalize functional & non_functional from specified_requirements or top-level keys
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

        # Normalize any dicts that might have "text" instead of "description"
        functional = [
            {"id": f.get("id"), "description": f.get("description") or f.get("text", "")}
            if isinstance(f, dict) else {"id": f"FR-{i+1}", "description": str(f)}
            for i, f in enumerate(functional)
        ]
        non_functional = [
            {"id": nf.get("id"), "description": nf.get("description") or nf.get("text", "")}
            if isinstance(nf, dict) else {"id": f"NFR-{i+1}", "description": str(nf)}
            for i, nf in enumerate(non_functional)
        ]

    purpose = reqs.get("purpose", "")
    scope = reqs.get("scope", "")
    external_interfaces = reqs.get("external_interfaces", [])
    design_constraints = reqs.get("design_constraints", [])
    user_characteristics = reqs.get("user_characteristics", [])
    assumptions_and_dependencies = reqs.get("assumptions_and_dependencies", [])
    supporting_information = reqs.get("supporting_information", [])

    # If client_view is not present, synthesize a natural language view from requirements
    if not cview and (functional or non_functional):
        import re
        items = []
        for f in functional:
            desc = f.get("description", "") if isinstance(f, dict) else str(f)
            clean = re.sub(r"^(The system shall|The system will|System shall|The platform shall)\s+", "", desc, flags=re.IGNORECASE).strip()
            if clean:
                clean = clean[0].upper() + clean[1:]
            items.append({"id": f.get("id", "FR"), "text": clean or desc})
        for nf in non_functional:
            desc = nf.get("description", "") if isinstance(nf, dict) else str(nf)
            clean = re.sub(r"^(The system shall|The system will|System shall|The platform shall)\s+", "", desc, flags=re.IGNORECASE).strip()
            if clean:
                clean = clean[0].upper() + clean[1:]
            items.append({"id": nf.get("id", "NFR"), "text": clean or desc})
        cview = {
            "sections": [
                {
                    "title": "Business Capabilities & Requirements",
                    "items": items
                }
            ]
        }

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
        "client_view": cview,
        "version": iteration + 1
    }