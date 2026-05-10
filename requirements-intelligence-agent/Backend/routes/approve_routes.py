
from fastapi import APIRouter, UploadFile, File, Form,Query
from controllers.approve_controller import approve_endpoint
from pydantic import BaseModel


approve_routes = APIRouter()

class ApproveRequest(BaseModel):
    meeting_id: str
    
@approve_routes.post("/approve-reqs")
async def approve_requirements(req: ApproveRequest):
    return await approve_endpoint(req)