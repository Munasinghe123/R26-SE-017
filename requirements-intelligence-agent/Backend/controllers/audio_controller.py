
import os
import uuid

from utils.saveFile import save_file
from services.meetings_service import save_srs_draft
from graph.instance import graph


async def handle_audio_upload(file, project_id):
    print("AUDIO PROJECT ID:", project_id)
    path = save_file(file)
    thread_id = str(uuid.uuid4())

    try:
        result = graph.invoke(
            {
                "mode": "audio_extract",
                "audio_path": path,
                "project_id": project_id,
                "thread_id": thread_id,
                "iteration_count": 0,
                "feedback_history": [],
            },
            config={"configurable": {"thread_id": thread_id}},
        )

        # draft = await save_srs_draft(project_id, result["requirements"])
        # print(draft)
        print("MEETING ID:", thread_id)
        return {"thread_id": thread_id}
    
    finally:
        if os.path.exists(path):
            os.remove(path)
            print(f"Temporary audio deleted: {path}")

