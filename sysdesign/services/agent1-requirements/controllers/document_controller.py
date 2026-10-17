import os
import uuid
import asyncio
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from utils.saveFile import save_file
from graph.instance import graph
from services.read_document import read_document
from services.validate_document import validate_technical_document
from services.meetings_service import save_meeting_requirements


async def _run_document_extraction_task(path: str, meeting_id: str, project_id: str = None):
    """Executes multi-LLM LangGraph extraction asynchronously in the background."""
    print(f"[Agent1 Background] Starting document extraction for meeting: {meeting_id}")
    try:
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
            reqs["input_method"] = "document"
        if isinstance(cview, dict):
            cview["input_method"] = "document"

        await save_meeting_requirements(
            meeting_id,
            reqs or {},
            client_view=cview or {},
            version=1,
            project_id=project_id,
            status="ready_for_review"
        )
        print(f"[Agent1 Background] Successfully completed document extraction for {meeting_id} (status: ready_for_review)")
    except Exception as exc:
        print(f"[Agent1 Background] Error during document extraction: {exc}")
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
        # Clean up temporary uploaded document file
        try:
            if path and os.path.exists(path):
                os.remove(path)
                print(f"[Agent1 Background] Cleaned up temp file: {path}")
        except Exception as del_err:
            print(f"[Agent1 Background] Notice: Could not delete temp document file {path}: {del_err}")


async def handle_document_upload(file, project_id=None, background_tasks=None):
    path = save_file(file)

    try:
        # 1. Read document text and validate whether it is a technical requirements document
        try:
            text = await run_in_threadpool(read_document, path)
            validation = await run_in_threadpool(validate_technical_document, text)
            if not validation.get("is_technical", False):
                if path and os.path.exists(path):
                    os.remove(path)
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded document rejected: {validation.get('reason', 'The document does not contain technical software requirements.')}"
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Document pre-validation notice: {e}")

        meeting_id = project_id if project_id else str(uuid.uuid4())

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
            background_tasks.add_task(_run_document_extraction_task, path, meeting_id, project_id)
        else:
            asyncio.create_task(_run_document_extraction_task(path, meeting_id, project_id))

        # Return immediately in < 100ms
        return {
            "meeting_id": meeting_id,
            "project_id": project_id,
            "status": "processing"
        }
    except Exception:
        # If early error occurred before queuing background task, clean up
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        raise