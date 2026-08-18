from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID

from services.project_service import create_project_service

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