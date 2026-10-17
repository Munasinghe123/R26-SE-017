from fastapi import APIRouter, UploadFile, File, Form, Query, BackgroundTasks
from controllers.process_source import process_source
from typing import Optional

router = APIRouter()

@router.post('/extract-requirements')
async def extract_requirements(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    projectId: Optional[str] = Form(None)
):
    return await process_source(file, project_id=projectId, background_tasks=background_tasks)
