
import uuid
from starlette.concurrency import run_in_threadpool
from utils.saveFile import save_file
from graph.instance import graph


async def handle_document_upload(file):
    path = save_file(file)
    meeting_id = str(uuid.uuid4())

    payload = {
        "mode": "document_extract",
        "document_path": path,
        "meeting_id": meeting_id,
        "iteration_count": 0,
        "feedback_history": [],
    }
    config = {"configurable": {"thread_id": meeting_id}}

    result = await run_in_threadpool(graph.invoke, payload, config)

    return {
        "meeting_id": meeting_id
    }