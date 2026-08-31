"""
HLA Agent — FastAPI Web Server
REST API + WebSocket for the web dashboard.
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import csv
import uvicorn

from config import INPUT_DIR, RESULTS_DIR, WEB_DIR, MODELS, LLM_PROVIDER, PROVIDER_MODELS
from storage.db import get_all_runs, get_run, get_candidates
from generation.generator import check_models_available
from providers import get_provider_name
from main import elaborate_winner

from output.diagram_workflow import (
    load_workflow,
    public_workflow_view,
    score_manual_plantuml_edit,
    improve_plantuml_with_llm,
    approve_plantuml_and_generate_mermaid,
    ensure_initial_plantuml,
)

logger = logging.getLogger("HLA-Server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("HLA Agent Server starting...")
    RESULTS_DIR.mkdir(exist_ok=True)
    yield
    logger.info("HLA Agent Server shutting down...")


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HLA Agent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static web files
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


# ─── Pages ─────────────────────────────────────────
@app.get("/")
async def serve_dashboard():
    return FileResponse(str(WEB_DIR / "index.html"))


# ─── API Endpoints ─────────────────────────────────
@app.get("/api/health")
async def health():
    availability = check_models_available()
    provider = get_provider_name()
    return {
        "status": "ok",
        "provider": provider,
        "models": availability,
        "configured_models": MODELS,
        "all_providers": list(PROVIDER_MODELS.keys()),
    }


@app.get("/api/samples")
async def list_samples():
    samples = []
    for f in INPUT_DIR.glob("*.json"):
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        samples.append({"filename": f.name, "project": data.get("project", f.stem),
                         "frs": len(data.get("functional_requirements", [])),
                         "nfrs": len(data.get("non_functional_requirements", []))})
    return samples


@app.get("/api/samples/{filename}")
async def get_sample(filename: str):
    path = INPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Sample not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/history")
async def history():
    return get_all_runs()


@app.get("/api/results/{run_id}")
async def results(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    candidates = get_candidates(run_id)
    return {"run": run, "candidates": candidates}


@app.get("/api/results/{run_id}/report")
async def get_report(run_id: str):
    path = RESULTS_DIR / "evaluation_report.md"
    if not path.exists():
        raise HTTPException(404, "Report not found")
    return FileResponse(str(path), media_type="text/markdown")


@app.get("/api/results/{run_id}/radar")
async def get_radar(run_id: str):
    path = RESULTS_DIR / "radar_chart.png"
    if not path.exists():
        raise HTTPException(404, "Radar chart not found")
    return FileResponse(str(path), media_type="image/png")


@app.get("/api/results/{run_id}/diagram/{dtype}")
async def get_diagram(run_id: str, dtype: str):
    if dtype == "plantuml":
        path = RESULTS_DIR / "diagram.puml"
    elif dtype == "mermaid":
        path = RESULTS_DIR / "diagram.mmd"
    else:
        raise HTTPException(400, "Invalid diagram type. Use 'plantuml' or 'mermaid'")
    if not path.exists():
        raise HTTPException(404, "Diagram not found")
    with open(path, "r", encoding="utf-8") as f:
        return {"type": dtype, "content": f.read()}


def _load_requirements_for_run() -> dict:
    path = RESULTS_DIR / "_temp_input.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    sample_files = list(INPUT_DIR.glob("*.json"))
    if sample_files:
        try:
            with open(sample_files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "project": "SDLC Project",
        "functional_requirements": [
            {"id": "FR-1", "description": "Manage appointment bookings and cancellations"},
            {"id": "FR-2", "description": "Send confirmation notifications"},
            {"id": "FR-3", "description": "Process payments securely"}
        ],
        "non_functional_requirements": [
            {"id": "NFR-1", "type": "availability", "target": "99.9% uptime"},
            {"id": "NFR-2", "type": "performance", "target": "< 200ms latency"}
        ]
    }


def _load_winner_for_run() -> dict:
    path = RESULTS_DIR / "winner.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    runs = get_all_runs()
    if runs:
        top_run = runs[0]
        cands = get_candidates(top_run.get("run_id", ""))
        if cands:
            return {
                "model": cands[0].get("model", MODELS[0]),
                "architecture": cands[0].get("architecture", {}),
                "scores": cands[0].get("scores", {}),
                "selected_by_user": True
            }

    return {
        "model": MODELS[0],
        "architecture": {
            "architecture_style": "Layered Architecture",
            "layers": [{"name": "Presentation", "order": 1}, {"name": "Business Logic", "order": 2}, {"name": "Data Access", "order": 3}],
            "components": [
                {"name": "AppointmentController", "layer": "Presentation", "boundary": "presentation", "element_type": "controller", "responsibilities": ["Handles HTTP requests"]},
                {"name": "AppointmentService", "layer": "Business Logic", "boundary": "business_logic", "element_type": "service", "responsibilities": ["Business logic"]},
                {"name": "AppointmentRepository", "layer": "Data Access", "boundary": "data_access", "element_type": "repository", "responsibilities": ["Database operations"]}
            ],
            "connectors": [
                {"from_component": "AppointmentController", "to_component": "AppointmentService", "connector_type": "sync_call"},
                {"from_component": "AppointmentService", "to_component": "AppointmentRepository", "connector_type": "sync_call"}
            ]
        },
        "scores": {"CAS": 0.80},
        "selected_by_user": True
    }


@app.post("/api/runs/{run_id}/select")
async def select_candidate_endpoint(run_id: str, payload: dict):
    """User selects an architecture candidate. Updates winner.json and elaborates the diagram."""
    model = payload.get("model")
    architecture = payload.get("architecture")
    scores = payload.get("scores")
    
    if not model or not architecture or not scores:
        raise HTTPException(400, "Payload must contain model, architecture, and scores")
        
    RESULTS_DIR.mkdir(exist_ok=True)
    winner_data = {
        "model": model,
        "architecture": architecture,
        "scores": scores,
        "selected_by_user": True
    }
    with open(RESULTS_DIR / "winner.json", "w", encoding="utf-8") as f:
        json.dump(winner_data, f, indent=2)

    # Elaborate diagram for selected candidate
    reqs_file = RESULTS_DIR / "_temp_input.json"
    if not reqs_file.exists():
        reqs = _load_requirements_for_run()
        with open(reqs_file, "w", encoding="utf-8") as f:
            json.dump(reqs, f)
    elab = elaborate_winner(run_id, winner_data, reqs_file)
    
    # Save diagram paths
    puml_path = str(RESULTS_DIR / "diagram.puml")
    mmd_path = str(RESULTS_DIR / "diagram.mmd")
    
    return {
        "status": "success",
        "run_id": run_id,
        "outputs": {
            "plantuml": puml_path if (RESULTS_DIR / "diagram.puml").exists() else None,
            "mermaid": mmd_path if (RESULTS_DIR / "diagram.mmd").exists() else None,
        },
        "elaboration": elab
    }


@app.get("/api/results/{run_id}/diagram_workflow")
async def get_diagram_workflow(run_id: str):
    state = load_workflow()
    if not state or state.get("run_id") != run_id:
        raise HTTPException(404, "Diagram workflow not found")
    return public_workflow_view(state)


@app.post("/api/runs/{run_id}/diagram/plantuml/score")
async def score_plantuml_manual(run_id: str, payload: dict):
    """User submits manual PlantUML edits for deterministic rescoring + diff."""
    diagram = (payload or {}).get("diagram")
    if not isinstance(diagram, str) or not diagram.strip():
        raise HTTPException(400, "Missing 'diagram' PlantUML source")

    winner = _load_winner_for_run()
    architecture = winner.get("architecture") or {}

    # Ensure workflow exists.
    reqs = _load_requirements_for_run()
    project = reqs.get("project", "System")
    ensure_initial_plantuml(
        run_id=run_id,
        model=winner.get("model", ""),
        architecture=architecture,
        requirements=reqs,
        title=project,
    )

    state = score_manual_plantuml_edit(run_id=run_id, plantuml=diagram, architecture=architecture)
    return public_workflow_view(state)


@app.post("/api/runs/{run_id}/diagram/plantuml/improve")
async def improve_plantuml(run_id: str, payload: dict | None = None):
    """Ask LLM for PlantUML iteration 2 (max 2 LLM iterations total)."""
    winner = _load_winner_for_run()
    architecture = winner.get("architecture") or {}
    model = winner.get("model", "")
    reqs = _load_requirements_for_run()
    project = reqs.get("project", "System")

    ensure_initial_plantuml(
        run_id=run_id,
        model=model,
        architecture=architecture,
        requirements=reqs,
        title=project,
    )

    user_notes = None
    if isinstance(payload, dict):
        user_notes = (payload.get("notes") or "").strip() or None

    state = improve_plantuml_with_llm(
        run_id=run_id,
        model=model,
        architecture=architecture,
        requirements=reqs,
        title=project,
        user_notes=user_notes,
    )
    return public_workflow_view(state)


@app.post("/api/runs/{run_id}/diagram/plantuml/approve")
async def approve_plantuml(run_id: str):
    """Approve PlantUML and generate Mermaid as the final step."""
    winner = _load_winner_for_run()
    architecture = winner.get("architecture") or {}
    model = winner.get("model", "")
    reqs = _load_requirements_for_run()
    project = reqs.get("project", "System")

    ensure_initial_plantuml(
        run_id=run_id,
        model=model,
        architecture=architecture,
        requirements=reqs,
        title=project,
    )

    state = approve_plantuml_and_generate_mermaid(
        run_id=run_id,
        model=model,
        architecture=architecture,
        requirements=reqs,
        title=project,
    )
    return public_workflow_view(state)


@app.get("/api/results/{run_id}/winner")
async def get_winner(run_id: str):
    path = RESULTS_DIR / "winner.json"
    if not path.exists():
        raise HTTPException(404, "Winner not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/results/{run_id}/diagram_iterations_diff")
async def get_diagram_iterations_diff(run_id: str):
    """Return the v1→v2 diagram unified diff markdown (if present)."""
    path = RESULTS_DIR / "diagram_iterations_diff.md"
    if not path.exists():
        raise HTTPException(404, "Diagram diff not found")
    return FileResponse(str(path), media_type="text/markdown")


@app.post("/api/runs/{run_id}/export_evidence")
async def export_evidence(run_id: str):
    """Export per-candidate NFR evidence and raw LLM text as CSV for auditing."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    candidates = get_candidates(run_id)
    if not candidates:
        raise HTTPException(404, "No candidates found for run")

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"evidence_{run_id}.csv"

    with open(out_path, "w", newline='', encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["candidate_id", "model", "candidate_num", "nfr_id", "nfr_type", "nfr_target", "nfr_score", "nfr_reasoning", "raw_text"])

        for c in candidates:
            cid = c.get("id") or ""
            model = c.get("model", "")
            cand_num = c.get("candidate_num", "")
            scores = c.get("scores", {}) or {}
            alignment_map = scores.get("alignment_map", {}) or {}
            llm = c.get("llm", {}) or {}
            raw = llm.get("raw_text", "")

            # If alignment_map empty, write a single row per candidate
            if not alignment_map:
                writer.writerow([cid, model, cand_num, "", "", "", "", "", raw.replace('\n', ' ')])
            else:
                for nfr_id, info in alignment_map.items():
                    writer.writerow([
                        cid, model, cand_num, nfr_id, info.get("type", ""), info.get("target", ""), info.get("score", ""), info.get("reasoning", "").replace('\n',' '), raw.replace('\n', ' ')
                    ])

    return FileResponse(str(out_path), media_type="text/csv")


# ─── WebSocket for Pipeline Execution ──────────────
@app.websocket("/ws/pipeline")
async def websocket_pipeline(ws: WebSocket):
    await ws.accept()
    try:
        data = await ws.receive_json()
        requirements = data.get("requirements")
        selected_models = data.get("models", MODELS)

        if not requirements:
            await ws.send_json({"type": "error", "message": "No requirements provided"})
            return

        # Save temp input
        temp_path = RESULTS_DIR / "_temp_input.json"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(requirements, f)

        # Run pipeline Phase 1 in thread to not block
        from main import generate_and_rank

        await ws.send_json({"type": "status", "step": "start", "message": "Phase 1 starting..."})

        # Run in executor
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, lambda: generate_and_rank(str(temp_path), models=selected_models)
            )

            # Build response
            ranked_data = []
            for c in result["ranked_candidates"]:
                ranked_data.append({
                    "rank": c["rank"], "model": c["model"],
                    "candidate_num": c["candidate_num"],
                    "scores": c["scores"],
                    "architecture": c["architecture"],
                    "llm": c.get("llm", {}),
                    "id": c.get("id", None) # if we need db id later
                })

            await ws.send_json({
                "type": "phase1_complete",
                "run_id": result["run_id"],
                "candidates": ranked_data,
            })
        except Exception as e:
            await ws.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


from pydantic import BaseModel

class SelectionRequest(BaseModel):
    """User selection of a candidate for Phase 2 elaboration."""
    model: str
    architecture: dict
    scores: dict
    input_file_path: str = str(RESULTS_DIR / "_temp_input.json")

class RegenerateRequest(BaseModel):
    model: str
    candidate_num: int
    error: str

@app.post("/api/runs/{run_id}/regenerate")
async def regenerate_candidate_endpoint(run_id: str, req: RegenerateRequest):
    from generation.generator import regenerate_single
    from prompt.builder import build_architecture_prompt
    from cam.parser import extract_json_from_text, CAMParseError
    from evaluation import evaluate_architecture
    
    path = RESULTS_DIR / "_temp_input.json"
    with open(path, "r", encoding="utf-8") as f:
        requirements = json.load(f)
        
    prompt = build_architecture_prompt(requirements)
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: regenerate_single(req.model, prompt, req.candidate_num, req.error)
    )
    
    if not result.success:
        return {
            "success": False,
            "candidate": {
                "model": req.model, "candidate_num": req.candidate_num, "rank": -1,
                "error": result.error or "Regeneration failed",
                    "scores": {
                        "RTS": 0, "QAC": 0, "CI": 0, "CoS": 0,
                        "SSM1": 0, "SSM2": 0, "CAS": 0,
                        "verdict": "Failed", "detected_style": "unknown",
                    },
                    "llm": {
                        "provider": getattr(result, "provider_name", ""),
                        "duration_ms": result.duration_ms,
                        "attempts": getattr(result, "attempts", []),
                        "raw_text": result.raw_text,
                    },
                "architecture": {"architecture_style": "Failed", "components": [], "connectors": []}
            }
        }
        
    try:
        json_str = extract_json_from_text(result.raw_text)
        arch = json.loads(json_str)
        if not isinstance(arch, dict):
            raise CAMParseError(f"Expected dict, got {type(arch).__name__}")
        scores = evaluate_architecture(arch, requirements)
        return {
            "success": True,
            "candidate": {
                "model": req.model, "candidate_num": req.candidate_num, "rank": -1,
                "architecture": arch,
                "scores": scores,
                    "llm": {
                        "provider": getattr(result, "provider_name", ""),
                        "duration_ms": result.duration_ms,
                        "attempts": getattr(result, "attempts", []),
                        "raw_text": result.raw_text,
                    },
                "error": None
            }
        }
    except (CAMParseError, json.JSONDecodeError, Exception) as e:
        return {
            "success": False,
            "candidate": {
                "model": req.model, "candidate_num": req.candidate_num, "rank": -1,
                "error": f"Parse Error: {e}",
                    "scores": {
                        "RTS": 0, "QAC": 0, "CI": 0, "CoS": 0,
                        "SSM1": 0, "SSM2": 0, "CAS": 0,
                        "verdict": "Parse Failed", "detected_style": "unknown",
                    },
                    "llm": {
                        "provider": getattr(result, "provider_name", ""),
                        "duration_ms": result.duration_ms,
                        "attempts": getattr(result, "attempts", []),
                        "raw_text": result.raw_text,
                    },
                "architecture": {"architecture_style": "Unparseable", "components": [], "connectors": []}
            }
        }


@app.post("/api/runs/{run_id}/select")
async def select_winner(run_id: str, req: SelectionRequest):
    """Phase 2: Elaborate the selected winner candidate."""
    from main import elaborate_winner
    
    # Build candidate object from request
    candidate = {
        "model": req.model,
        "architecture": req.architecture,
        "scores": req.scores,
    }
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: elaborate_winner(run_id, candidate, req.input_file_path)
        )
        return {
            "status": "success",
            "run_id": run_id,
            "outputs": result["outputs"],
            "diagram_workflow": result.get("diagram_workflow"),
            "winner": {
                "model": result["winner"]["model"],
                "scores": result["winner"]["scores"],
                "architecture": result["winner"]["architecture"]
            }
        }
    except Exception as e:
        logger.error(f"Elaboration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run")
@app.post("/generate")
async def run_hld_generation(payload: dict):
    """
    Orchestrator pipeline endpoint.
    Receives RequirementsPackage / raw requirements payload, runs HLA candidate generation & evaluation engine,
    and returns a standardized ArchitecturePackage dictionary.
    """
    job_id = payload.get("job_id", "job-dev")
    tenant_id = payload.get("tenant_id", "dev")
    project_name = payload.get("project_name") or payload.get("project", "Default Project")
    payload["project"] = project_name

    try:
        from main import generate_and_rank, elaborate_winner
        import tempfile
        
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
            json.dump(payload, tf)
            temp_path = tf.name

        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: generate_and_rank(temp_path))

        candidates = res.get("ranked_candidates", [])
        winner = candidates[0] if candidates else {}
        arch = winner.get("architecture", {})
        scores = winner.get("scores", {})

        # Auto-elaborate the winner to generate initial PlantUML and mermaid diagram files
        run_id = res.get("run_id")
        elaborate_res = await loop.run_in_executor(
            None, lambda: elaborate_winner(run_id, winner, temp_path)
        )

        # Read diagram code from generated output files
        plantuml_code = None
        mermaid_code = None
        try:
            puml_path_str = elaborate_res.get("outputs", {}).get("plantuml")
            if puml_path_str:
                puml_file = Path(puml_path_str)
                if puml_file.exists():
                    with open(puml_file, "r", encoding="utf-8") as f:
                        plantuml_code = f.read()
                
                mmd_file = puml_file.parent / "diagram.mmd"
                if mmd_file.exists():
                    with open(mmd_file, "r", encoding="utf-8") as f:
                        mermaid_code = f.read()
        except Exception as e:
            logger.warning(f"Failed to read auto-elaborated diagrams: {e}")

        from cam.parser import normalize_element_type, normalize_boundary
        components = []
        for idx, c in enumerate(arch.get("components", [])):
            c_name = c.get("name", f"Component-{idx+1}")
            elem_type = normalize_element_type(c_name, c.get("element_type", "")).value
            bnd = normalize_boundary(c.get("layer", ""), c.get("boundary", "")).value
            components.append({
                "id": f"C{idx+1}",
                "name": c_name,
                "element_type": elem_type,
                "boundary": bnd,
                "responsibilities": c.get("responsibilities", ["Core logic"]),
                "provided_interfaces": c.get("provided_interfaces", []),
                "required_interfaces": c.get("required_interfaces", []),
                "requirement_ids": c.get("requirement_ids", [])
            })

        connectors = []
        for idx, conn in enumerate(arch.get("interactions", [])):
            connectors.append({
                "id": f"K{idx+1}",
                "from_component": conn.get("from", ""),
                "to_component": conn.get("to", ""),
                "connector_type": conn.get("type", "sync_call"),
                "protocol": conn.get("protocol", "REST"),
                "data_transferred": conn.get("data", "")
            })

        metric_scores = {
            "RTS":  scores.get("RTS",  0.0),
            "QAC":  scores.get("QAC",  0.0),
            "CI":   scores.get("CI",   0.0),
            "CoS":  scores.get("CoS",  0.0),
            "SSM1": scores.get("SSM1", 0.0),
            "SSM2": scores.get("SSM2", 0.0),
            "CAS":  scores.get("CAS",  0.0),
        }

        verdict = "accepted" if metric_scores["CAS"] >= 0.60 else "marginal"

        return {
            "schema_version": "1.0",
            "job_id": job_id,
            "tenant_id": tenant_id,
            "project_name": project_name,
            "architecture_style": arch.get("architecture_style", "Layered Microservices"),
            "style_confidence": 0.95,
            "components": components,
            "connectors": connectors,
            "quality_provisions": [],
            "scores": metric_scores,
            "verdict": verdict,
            "rejected_alternatives": candidates[1:] if len(candidates) > 1 else [],
            "candidates": candidates,
            "plantuml_code": plantuml_code,
            "mermaid_code": mermaid_code,
            "generation_metadata": {"run_id": run_id},
            "artifact_uris": {}
        }
    except Exception as e:
        logger.error(f"HLD pipeline run error: {e}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
