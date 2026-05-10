from fastapi import APIRouter, UploadFile, File, Form,Query
# from controllers.audio_controller import handle_audio_upload
from controllers.process_source import process_source


router = APIRouter()

# @router.post('/process-audio')
# async def process_audio(file: UploadFile = File(...)):
#     return await handle_audio_upload(file)

@router.post('/extract-requirements')
async def extract_requirements(file: UploadFile = File(...)):
    return await process_source(file)
