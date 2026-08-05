
from utils.saveFile import save_file
from services.meetings_service import save_requirements

from graph.instance import graph


async def handle_document_upload(file):

    path = save_file(file)

    result = graph.invoke({
        "mode": "document_extract",
        "document_path": path
    })

    meeting_id = save_requirements(
        result["requirements"]
    )

    return {
        "meeting_id": meeting_id
    }