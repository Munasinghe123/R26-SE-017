
import uuid
from starlette.concurrency import run_in_threadpool
from utils.saveFile import save_file
from graph.instance import graph


async def handle_document_upload(file, project_id=None):
    path = save_file(file)
    meeting_id = project_id if project_id else str(uuid.uuid4())

    payload = {
        "mode": "document_extract",
        "document_path": path,
        "meeting_id": meeting_id,
        "project_id": project_id,
        "iteration_count": 0,
        "feedback_history": [],
    }
    config = {"configurable": {"thread_id": meeting_id}}

    result = await run_in_threadpool(graph.invoke, payload, config)

    # Persist extracted requirements to DB and local cache
    try:
        from services.meetings_service import save_meeting_requirements
        reqs = result.get("requirements") if isinstance(result, dict) else None
        if not reqs:
            state = graph.get_state(config)
            if state and state.values:
                reqs = state.values.get("requirements")
        cview = result.get("client_view") if isinstance(result, dict) else None
        if not cview:
            state = graph.get_state(config)
            if state and state.values:
                cview = state.values.get("client_view")
        await save_meeting_requirements(meeting_id, reqs, client_view=cview, version=1, project_id=project_id)
    except Exception as exc:
        print(f"Warning: could not persist meeting requirements: {exc}")

    return {
        "meeting_id": meeting_id,
        "project_id": project_id
    }