import uuid

from utils.saveFile import save_file
from graph.instance import graph
from services.meetings_service import save_srs_draft

async def handle_document_upload(file, project_id):
    path = save_file(file)
    meeting_id = str(uuid.uuid4())

    result = graph.invoke(
        {
            "mode": "document_extract",
            "document_path": path,
            "project_id": project_id,
            "meeting_id": meeting_id,
            "iteration_count": 0,
            "feedback_history": [],
        },
        config={"configurable": {"thread_id": meeting_id}}
    )
    
    await save_srs_draft(project_id,result["requirements"])

    return {
        "meeting_id": meeting_id
    }