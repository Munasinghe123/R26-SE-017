import uuid

from utils.saveFile import save_file
from graph.instance import graph
from services.meetings_service import save_srs_draft
import os

async def handle_document_upload(file, project_id):
    path = save_file(file)
    thread_id = str(uuid.uuid4())

    result = graph.invoke(
        {
            "mode": "document_extract",
            "document_path": path,
            "project_id": project_id,
            "thread_id": thread_id,
            "iteration_count": 0,
            "feedback_history": [],
        },
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # await save_srs_draft(project_id,result["requirements"])

    print("thread_id", thread_id)
    
    if os.path.exists(path):
            os.remove(path)
            print(f"Temporary audio deleted: {path}")
            
    return {
        "thread_id": thread_id
    }