import os
import uuid
import asyncio
from starlette.concurrency import run_in_threadpool
from utils.saveFile import save_file
from graph.instance import graph
from services.meetings_service import save_meeting_requirements


async def _run_audio_extraction_task(path: str, meeting_id: str, project_id: str = None):
    """Executes audio transcription and multi-LLM extraction asynchronously in the background."""
    print(f"[Agent1 Background] Starting audio extraction for meeting: {meeting_id}")
    try:
        payload = {
            "mode": "audio_extract",
            "audio_path": path,
            "meeting_id": meeting_id,
            "project_id": project_id,
            "iteration_count": 0,
            "feedback_history": [],
        }
        config = {"configurable": {"thread_id": meeting_id}}

        result = await run_in_threadpool(graph.invoke, payload, config)

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
        if not cview and reqs:
            try:
                from services.HITL.client_view import build_client_view
                cview = build_client_view(reqs)
            except Exception as cv_err:
                print(f"[Agent1 Background] Notice: could not build client_view: {cv_err}")
        if isinstance(reqs, dict):
            reqs["input_method"] = "audio"
        if isinstance(cview, dict):
            cview["input_method"] = "audio"

        await save_meeting_requirements(
            meeting_id,
            reqs or {},
            client_view=cview or {},
            version=1,
            project_id=project_id,
            status="ready_for_review"
        )
        print(f"[Agent1 Background] Successfully completed audio extraction for {meeting_id} (status: ready_for_review)")
    except Exception as exc:
        print(f"[Agent1 Background] Error during audio extraction: {exc}")
        try:
            await save_meeting_requirements(
                meeting_id,
                {},
                client_view={},
                version=1,
                project_id=project_id,
                status="failed"
            )
        except Exception as save_err:
            print(f"[Agent1 Background] Error recording failed status: {save_err}")
    finally:
        # Clean up temporary uploaded audio file
        try:
            if path and os.path.exists(path):
                os.remove(path)
                print(f"[Agent1 Background] Cleaned up temp audio file: {path}")
        except Exception as del_err:
            print(f"[Agent1 Background] Notice: Could not delete temp audio file {path}: {del_err}")


async def handle_audio_upload(file, project_id=None, background_tasks=None):
    path = save_file(file)
    meeting_id = project_id if project_id else str(uuid.uuid4())

    try:
        # Save initial "processing" status in DB/cache immediately
        await save_meeting_requirements(
            meeting_id,
            {},
            client_view={},
            version=1,
            project_id=project_id,
            status="processing"
        )

        # Launch background task
        if background_tasks:
            background_tasks.add_task(_run_audio_extraction_task, path, meeting_id, project_id)
        else:
            asyncio.create_task(_run_audio_extraction_task(path, meeting_id, project_id))

        # Return immediately in < 100ms
        return {
            "meeting_id": meeting_id,
            "project_id": project_id,
            "status": "processing"
        }
    except Exception:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        raise
