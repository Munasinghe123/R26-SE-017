

from fastapi import APIRouter, UploadFile, File, Form,Query
from services.meetings_service import get_latest_requirements
from controllers.refine_controller import refine_endpoint
from pydantic import BaseModel
from typing import Dict, Any

refine_routes = APIRouter()


class RefineRequest(BaseModel):
    requirements: Dict[str, Any]
    feedback: str
    meetingId: str

@refine_routes.post('/refine-reqs')
async def refine_extracted_requirements(req: RefineRequest):
    return await refine_endpoint(req)

@refine_routes.get("/requirements/{meeting_id}")
async def get_requirements(meeting_id: str):
    data = get_latest_requirements(meeting_id)

    return {
        "requirements": {
            "functional": data["functional"],
            "non_functional": data["non_functional"]
        },
        "version": data["version"]
    }