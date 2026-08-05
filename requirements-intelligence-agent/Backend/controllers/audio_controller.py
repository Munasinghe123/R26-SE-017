
from utils.saveFile import save_file
from services.meetings_service import save_requirements
import uuid

from graph.instance import graph


async def handle_audio_upload(file):
    path = save_file(file)
    meeting_id = str(uuid.uuid4())

    result = graph.invoke(
        {
            "mode": "audio_extract",
            "audio_path": path,
            "meeting_id": meeting_id,
            "iteration_count": 0,
            "feedback_history": [],
        },
        config={"configurable": {"thread_id": meeting_id}}
    )

    save_requirements(result["requirements"], meeting_id)

    return {"meeting_id": meeting_id}

