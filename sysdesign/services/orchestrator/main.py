import asyncio
import json
import uuid
from typing import Dict, Any, Optional
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
    call_stage_http,
    AGENT_URLS,
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


@app.post("/jobs/{job_id}/test-srs")
@app.post("/jobs/test-srs")
async def test_srs_endpoint(job_id: str = "direct-test", payload: Optional[Dict[str, Any]] = None):
    """
    Temporary direct testing endpoint for the SRS Assembler.
    Bypasses waiting for upstream stages (HLD, LLD, UI) to test SRS directly.
    Can be called per project/job ID (e.g. /jobs/{project_id}/test-srs) with optional custom JSON.
    """
    payload = payload or {}

    if "requirements" in payload:
        srs_payload = payload
    elif payload.get("functional_requirements") or payload.get("functional"):
        srs_payload = {"requirements": payload}
    else:
        # Check if requirements exist in in-memory artifacts for this job_id
        stored_reqs = JOB_ARTIFACTS.get(job_id, {}).get("requirements")
        if stored_reqs:
            srs_payload = {
                "requirements": stored_reqs.model_dump(mode="json") if hasattr(stored_reqs, "model_dump") else stored_reqs
            }
        else:
            # Fallback: try fetching from Agent 1 requirements endpoint
            fetched_reqs = None
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"http://127.0.0.1:8001/requirements/{job_id}")
                    if resp.status_code == 200:
                        data = resp.json()
                        raw = data.get("final_requirements") or data.get("requirements") or {}
                        raw_fr = raw.get("functional") or raw.get("functional_requirements") or []
                        raw_nfr = raw.get("non_functional") or raw.get("non_functional_requirements") or []

                        norm_fr = []
                        for idx, fr in enumerate(raw_fr):
                            if isinstance(fr, dict):
                                norm_fr.append({
                                    "id": fr.get("id", f"FR-{idx+1}"),
                                    "title": fr.get("title", fr.get("description", f"Requirement {idx+1}")[:40]),
                                    "description": fr.get("description", fr.get("text", str(fr))),
                                })
                            else:
                                norm_fr.append({
                                    "id": f"FR-{idx+1}",
                                    "title": str(fr)[:40],
                                    "description": str(fr),
                                })

                        norm_nfr = []
                        for idx, nfr in enumerate(raw_nfr):
                            if isinstance(nfr, dict):
                                norm_nfr.append({
                                    "id": nfr.get("id", f"NFR-{idx+1}"),
                                    "iso_characteristic": nfr.get("iso_characteristic", "quality"),
                                    "description": nfr.get("description", nfr.get("text", str(nfr))),
                                })
                            else:
                                norm_nfr.append({
                                    "id": f"NFR-{idx+1}",
                                    "iso_characteristic": "quality",
                                    "description": str(nfr),
                                })

                        fetched_reqs = {
                            "project_name": data.get("project_name", f"Project {job_id[:8]}"),
                            "job_id": job_id,
                            "functional_requirements": norm_fr,
                            "non_functional_requirements": norm_nfr,
                        }
            except Exception:
                pass

            if fetched_reqs and (fetched_reqs["functional_requirements"] or fetched_reqs["non_functional_requirements"]):
                srs_payload = {"requirements": fetched_reqs}
            else:
                srs_payload = {
                    "requirements": {
                        "project_name": f"Project {job_id[:8] if len(job_id) > 8 else job_id}",
                        "job_id": job_id,
                        "functional_requirements": [
                            {
                                "id": "FR-1",
                                "title": "User Authentication",
                                "description": "The system shall allow users to log in securely using credentials."
                            },
                            {
                                "id": "FR-2",
                                "title": "Dashboard Overview",
                                "description": "The system shall display project overview and status."
                            }
                        ],
                        "non_functional_requirements": [
                            {
                                "id": "NFR-1",
                                "iso_characteristic": "performance_efficiency",
                                "description": "The system response time must not exceed 500ms under standard load."
                            },
                            {
                                "id": "NFR-2",
                                "iso_characteristic": "security",
                                "description": "All API endpoints must enforce encrypted communication."
                            }
                        ]
                    }
                }

    try:
        srs_result = await call_stage_http("srs", AGENT_URLS["srs"], srs_payload)
        return {
            "status": "success",
            "job_id": job_id,
            "dispatched_payload": srs_payload,
            "srs_response": srs_result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SRS Assembler test failed: {str(exc)}")



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
