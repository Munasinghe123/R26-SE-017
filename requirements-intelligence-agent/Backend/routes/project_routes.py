from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID

from services.project_service import create_project_service
from services.project_service import get_user_projects_service

project_routes = APIRouter()


class CreateProjectRequest(BaseModel):
    projectName: str
    projectDescription: str
    clientId: UUID
    creatorId: UUID


@project_routes.post("/projects", status_code=201)
async def create_project(
    data: CreateProjectRequest
):
    return await create_project_service(
        data.creatorId,
        data
    )
    
@project_routes.get("/projects/user/{user_id}")
async def get_user_projects(
    user_id: UUID
):
    return await get_user_projects_service(user_id)