from graph.workflow import build_graph
from utils.saveFile import save_file
from services.meetings_service import save_requirements

graph = build_graph()

async def handle_audio_upload(file):
    path = save_file(file)

    result = graph.invoke({
        "mode": "extract",
        "audio_path": path,
       
    })

    meeting_id=save_requirements(result["requirements"])

    return {"meeting_id": meeting_id}

