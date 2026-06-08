import os
import json
import shutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Change working directory so relative imports inside modules still work
os.chdir(os.path.dirname(__file__))

from input_normalizer import normalize_input
from screen_planner import plan_screens, screens_to_requirements, save_screen_plan
from generator.ui_generator import generate_ui
from evaluator.composite_scorer import evaluate, save_score_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.path.dirname(__file__)

class PlanRequest(BaseModel):
    requirements: dict

class GenerateRequest(BaseModel):
    screenId: str

class EvaluateRequest(BaseModel):
    screenIds: List[str] = []


@app.post("/api/plan")
def plan(req: PlanRequest):
    try:
        req_path = os.path.join(BASE, "samples", "sample_requirements.json")
        with open(req_path, "w", encoding="utf-8") as f:
            json.dump(req.requirements, f, indent=2)
        normalized = normalize_input(req.requirements)
        screens = plan_screens(normalized)
        save_screen_plan(screens)
        return {"screens": screens, "logs": ""}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        plan_path = os.path.join(BASE, "outputs", "screen_plan.json")
        with open(plan_path, "r", encoding="utf-8") as f:
            screens = json.load(f)

        screen_id = req.screenId
        target = None
        if screen_id.isdigit():
            idx = int(screen_id) - 1
            if 0 <= idx < len(screens):
                target = screens[idx]
        if not target:
            target = next((s for s in screens if s.get("screen_id") == screen_id), None)
        if not target:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Screen '{screen_id}' not found")

        req_path = os.path.join(BASE, "samples", "sample_requirements.json")
        with open(req_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        normalized = normalize_input(raw)
        per_screen = screens_to_requirements([target], normalized)
        screen_req = per_screen[0]
        screen_type = screen_req.get("screen_type", "unknown")

        html = generate_ui(screen_req, screen_type)

        out_dir = os.path.join(BASE, "outputs", "generated_screens")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{screen_req['screen_id']}.html"), "w", encoding="utf-8") as f:
            f.write(html)

        return {"screenId": screen_req["screen_id"], "html": html, "logs": ""}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate")
def evaluate_screens(req: EvaluateRequest):
    try:
        screens_dir = os.path.join(BASE, "outputs", "generated_screens")
        reports_dir = os.path.join(BASE, "outputs", "score_reports")
        os.makedirs(reports_dir, exist_ok=True)

        html_files = [f for f in os.listdir(screens_dir) if f.endswith(".html")]
        reports = []
        for file in html_files:
            sid = file.replace(".html", "")
            if req.screenIds and sid not in req.screenIds:
                continue
            with open(os.path.join(screens_dir, file), "r", encoding="utf-8") as f:
                html = f.read()
            report = evaluate(html, iteration_number=1)
            save_score_report(report, os.path.join(reports_dir, f"{sid}_score_report.json"))
            reports.append({"screenId": sid, "report": report})

        return {"reports": reports, "logs": ""}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outputs")
def outputs(screenId: str = None):
    try:
        out_dir = os.path.join(BASE, "outputs", "generated_screens")
        if screenId:
            with open(os.path.join(out_dir, f"{screenId}.html"), "r", encoding="utf-8") as f:
                return {"screenId": screenId, "html": f.read()}
        files = [f.replace(".html", "") for f in os.listdir(out_dir) if f.endswith(".html")]
        return {"screens": files}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports")
def reports():
    try:
        reports_dir = os.path.join(BASE, "outputs", "score_reports")
        if not os.path.exists(reports_dir):
            return {"reports": []}
        result = []
        for file in os.listdir(reports_dir):
            if not file.endswith(".json"):
                continue
            sid = file.replace("_score_report.json", "")
            with open(os.path.join(reports_dir, file), "r", encoding="utf-8") as f:
                result.append({"screenId": sid, "report": json.load(f)})
        return {"reports": result}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear-session")
def clear_session():
    import shutil
    try:
        to_delete = [
            os.path.join(BASE, "outputs", "screen_plan.json"),
            os.path.join(BASE, "outputs", "generated_screens"),
            os.path.join(BASE, "outputs", "score_reports"),
            os.path.join(BASE, "samples", "sample_requirements.json"),
        ]
        for p in to_delete:
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p)
                elif os.path.isfile(p):
                    os.unlink(p)
            except Exception:
                pass
        return {"cleared": True}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/plan-status")
def plan_status():
    try:
        plan_path = os.path.join(BASE, "outputs", "screen_plan.json")
        with open(plan_path, "r", encoding="utf-8") as f:
            screens = json.load(f)
        return {"screens": screens}
    except Exception:
        return {"screens": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
