import asyncio
import json
import uuid
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from pipeline import (
    initialize_job,
    run_stage_requirements,
    run_stage_hld,
    run_stage_lld,
    run_stage_ui,
    run_stage_srs,
    get_job_state,
    restore_job_from_db,
    select_candidate,
    refine_diagram,
    JOB_STORE,
    JOB_ARTIFACTS,
    JOB_LISTENERS,
)

app = FastAPI(title="Pipeline Orchestrator Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "service": "orchestrator", "active_jobs": len(JOB_STORE)}


@app.post("/jobs")
async def create_job(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    # Initialize state
    await initialize_job(job_id, payload)
    # Start step 1: Requirements
    background_tasks.add_task(run_stage_requirements, job_id)
    return {"job_id": job_id, "status": "queued", "message": "Pipeline run queued successfully"}


@app.post("/jobs/{job_id}/start-hld")
async def start_hld(job_id: str, background_tasks: BackgroundTasks):
    job = get_job_state(job_id) or await restore_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    background_tasks.add_task(run_stage_hld, job_id)
    return {"job_id": job_id, "status": "queued", "message": "HLD stage queued"}


@app.post("/jobs/{job_id}/start-lld")
async def start_lld(job_id: str, background_tasks: BackgroundTasks):
    job = get_job_state(job_id) or await restore_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    background_tasks.add_task(run_stage_lld, job_id)
    return {"job_id": job_id, "status": "queued", "message": "LLD stage queued"}


@app.post("/jobs/{job_id}/start-ui")
async def start_ui(job_id: str, background_tasks: BackgroundTasks):
    job = get_job_state(job_id) or await restore_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    background_tasks.add_task(run_stage_ui, job_id)
    return {"job_id": job_id, "status": "queued", "message": "UI stage queued"}


@app.post("/jobs/{job_id}/start-srs")
async def start_srs(job_id: str, background_tasks: BackgroundTasks):
    job = get_job_state(job_id) or await restore_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    background_tasks.add_task(run_stage_srs, job_id)
    return {"job_id": job_id, "status": "queued", "message": "SRS assembly queued"}


@app.post("/jobs/{job_id}/retry-hld")
async def retry_hld(job_id: str, background_tasks: BackgroundTasks):
    job = get_job_state(job_id) or await restore_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    background_tasks.add_task(run_stage_hld, job_id)
    return {"job_id": job_id, "status": "queued", "message": "HLD retry queued"}


@app.post("/jobs/{job_id}/select-candidate")
async def select_candidate_endpoint(job_id: str, payload: Dict[str, Any]):
    try:
        await select_candidate(job_id, payload)
        return {"status": "success", "message": "Candidate selected and elaborated successfully"}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/jobs/{job_id}/refine-diagram")
async def refine_diagram_endpoint(job_id: str, payload: Dict[str, Any]):
    try:
        res = await refine_diagram(job_id, payload)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/jobs")
def list_jobs():
    return [j.model_dump(mode="json") for j in JOB_STORE.values()]


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = get_job_state(job_id)
    if not job:
        job = await restore_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job": job.model_dump(mode="json"),
        "artifacts": {
            k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v
            for k, v in JOB_ARTIFACTS.get(job_id, {}).items()
        }
    }


@app.get("/jobs/{job_id}/stream")
async def stream_job_events(job_id: str):
    """Server-Sent Events (SSE) endpoint for real-time pipeline status updates."""
    job = get_job_state(job_id)
    if not job:
        job = await restore_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        q = asyncio.Queue()
        JOB_LISTENERS.setdefault(job_id, []).append(q)
        try:
            yield f"data: {json.dumps({'event': 'init', 'job': job.model_dump(mode='json')})}\n\n"
            while True:
                data = await q.get()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("event") in ["complete", "failed", "needs_review", "paused"]:
                    # Do not break on pause, because client may want to keep listening
                    if data.get("event") in ["complete", "failed"]:
                        break
        except asyncio.CancelledError:
            pass
        finally:
            if job_id in JOB_LISTENERS and q in JOB_LISTENERS[job_id]:
                JOB_LISTENERS[job_id].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
