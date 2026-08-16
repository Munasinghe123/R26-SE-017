import os
import json
import shutil
import io
import sys
import contextlib
import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Change working directory so relative imports inside modules still work
os.chdir(os.path.dirname(__file__))

# Suppress noisy HTTP debug logs from httpcore / httpx / groq SDK
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("groq").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("langchain_groq").setLevel(logging.WARNING)

from generator.refinement_controller import run_refinement_loop
from input_normalizer import normalize_input
from screen_planner import plan_screens, screens_to_requirements, save_screen_plan
from generator.ui_generator import generate_ui
from generator.traceability import build_traceability_matrix
from evaluator.composite_scorer import evaluate, save_score_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.path.dirname(__file__)


@contextlib.contextmanager
def capture_logs():
    """
    Captures print() output by replacing sys.stdout/stderr.
    Also hooks into the root logger so library log messages are included.
    """
    buffer = io.StringIO()

    # redirect stdout / stderr
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = buffer
    sys.stderr = buffer

    # hook root logger
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    root = logging.getLogger()
    old_level = root.level
    root.setLevel(logging.WARNING)
    root.addHandler(handler)

    try:
        yield buffer
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        root.removeHandler(handler)
        root.setLevel(old_level)


def _log(buf: io.StringIO, msg: str):
    """Write a timestamped line directly into the capture buffer."""
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    buf.write(f"[{ts}] [api] {msg}\n")

class PlanRequest(BaseModel):
    requirements: dict

class GenerateRequest(BaseModel):
    screenId: str

class EvaluateRequest(BaseModel):
    screenIds: List[str] = []


@app.post("/api/plan")
def plan(req: PlanRequest):
    try:
        with capture_logs() as buf:
            _log(buf, "Planning phase started.")
            req_path = os.path.join(BASE, "samples", "sample_requirements.json")
            with open(req_path, "w", encoding="utf-8") as f:
                json.dump(req.requirements, f, indent=2)
            _log(buf, f"Requirements saved to {req_path}")

            normalized = normalize_input(req.requirements)
            _log(buf, f"Input normalized. Project: {normalized.get('project_name')}")

            _log(buf, "Calling LLM to plan screens...")
            screens = plan_screens(normalized)
            _log(buf, f"LLM returned {len(screens)} screen(s).")

            save_screen_plan(screens)
            _log(buf, "Screen plan saved to outputs/screen_plan.json")

            for i, s in enumerate(screens, 1):
                _log(buf, f"  {i}. [{s.get('priority','?')}] {s.get('screen_name')} — {s.get('purpose','')}")

        return {"screens": screens, "logs": {"stdout": buf.getvalue(), "stderr": ""}}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        with capture_logs() as buf:
            _log(buf, f"Generation phase started for screen: '{req.screenId}'")

            plan_path = os.path.join(BASE, "outputs", "screen_plan.json")
            with open(plan_path, "r", encoding="utf-8") as f:
                screens = json.load(f)
            _log(buf, f"Loaded screen plan ({len(screens)} screens).")

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

            _log(buf, f"Target screen: {target.get('screen_name')} (type: {target.get('screen_type')})")

            req_path = os.path.join(BASE, "samples", "sample_requirements.json")
            with open(req_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            normalized = normalize_input(raw)
            per_screen = screens_to_requirements([target], normalized)
            screen_req = per_screen[0]
            screen_type = screen_req.get("screen_type", "unknown")

            _log(buf, "Sending prompt to LLM (model: llama-3.3-70b-versatile)...")
            start = time.time()
            html = generate_ui(screen_req, screen_type)
            elapsed = round(time.time() - start, 1)
            _log(buf, f"LLM responded in {elapsed}s. HTML length: {len(html)} chars.")

            out_dir = os.path.join(BASE, "outputs", "generated_screens")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{screen_req['screen_id']}.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
            _log(buf, f"HTML saved to {out_path}")

        return {"screenId": screen_req["screen_id"], "html": html, "logs": {"stdout": buf.getvalue(), "stderr": ""}}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

class RefineRequest(BaseModel):
    screenId: str


@app.post("/api/refine")
def refine(req: RefineRequest):
    try:
        with capture_logs() as buf:
            _log(buf, f"Refinement loop started for screen: '{req.screenId}'")

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
                raise HTTPException(status_code=404, detail=f"Screen '{screen_id}' not found")

            req_path = os.path.join(BASE, "samples", "sample_requirements.json")
            with open(req_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            normalized = normalize_input(raw)
            per_screen = screens_to_requirements([target], normalized)
            screen_req = per_screen[0]
            screen_type = screen_req.get("screen_type", "unknown")

            existing_html_path = os.path.join(BASE, "outputs", "generated_screens", f"{screen_req['screen_id']}.html")
            initial_html = None
            if os.path.exists(existing_html_path):
                with open(existing_html_path, "r", encoding="utf-8") as f:
                    initial_html = f.read()
                _log(buf, "Found existing generated HTML — refining it instead of generating fresh.")
            else:
                _log(buf, "No existing HTML found — will generate a first pass before refining.")

            _log(buf, "Running refinement loop (up to 5 iterations)...")
            start = time.time()
            result = run_refinement_loop(screen_req, screen_type, initial_html=initial_html)
            elapsed = round(time.time() - start, 1)
            _log(buf, f"Refinement loop finished in {elapsed}s after {result['iterations']} iteration(s).")

            for entry in result["history"]:
                rpt = entry["report"]
                _log(buf, f"  Iter {entry['iteration']}: total={rpt['total_score']} "
                          f"(ISO {rpt['iso_score']} / Nielsen {rpt['nielsen_score']} / WCAG {rpt['wcag_score']}) "
                          f"threshold={rpt['threshold']} passed={rpt['passed']}")
                if entry["applied_fix"]:
                    _log(buf, f"    -> fixed: {entry['applied_fix']['weakest_standard']} / "
                              f"{entry['applied_fix']['weakest_metric']}")
                if entry["regressions"]:
                    _log(buf, f"    -> WARNING regressions: {entry['regressions']}")

            _log(buf, f"Final score: {result['final_report']['total_score']} "
                      f"(passed={result['passed']}, regressed_from_best={result['regressed']})")

            out_dir = os.path.join(BASE, "outputs", "generated_screens")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{screen_req['screen_id']}.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(result["final_html"])
            _log(buf, f"Final HTML saved to {out_path}")

            reports_dir = os.path.join(BASE, "outputs", "score_reports")
            os.makedirs(reports_dir, exist_ok=True)
            report_path = os.path.join(reports_dir, f"{screen_req['screen_id']}_score_report.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(result["final_report"], f, indent=2, ensure_ascii=False)
            _log(buf, f"Final report saved to {report_path}")

            history_summary = [
                {
                    "iteration": e["iteration"],
                    "report": e["report"],
                    "appliedFix": e["applied_fix"],
                    "regressions": e["regressions"],
                    "isFinal": e.get("is_final", False),
                }
                for e in result["history"]
            ]

            history_path = os.path.join(reports_dir, f"{screen_req['screen_id']}_history.json")
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history_summary, f, indent=2, ensure_ascii=False)
            _log(buf, f"Iteration history saved to {history_path}")

        return {
            "screenId": screen_req["screen_id"],
            "html": result["final_html"],
            "finalReport": result["final_report"],
            "passed": result["passed"],
            "iterations": result["iterations"],
            "regressed": result["regressed"],
            "history": history_summary,
            "logs": {"stdout": buf.getvalue(), "stderr": ""},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate")
def evaluate_screens(req: EvaluateRequest):
    try:
        screens_dir = os.path.join(BASE, "outputs", "generated_screens")
        reports_dir = os.path.join(BASE, "outputs", "score_reports")
        os.makedirs(reports_dir, exist_ok=True)
        # If no screens have been generated yet, return empty reports
        if not os.path.exists(screens_dir):
            return {"reports": [], "logs": {"stdout": "No screens generated yet.", "stderr": ""}}
        with capture_logs() as buf:
            html_files = [f for f in os.listdir(screens_dir) if f.endswith(".html")]
            _log(buf, f"Evaluation phase started. Found {len(html_files)} screen(s).")

            reports = []
            for file in html_files:
                sid = file.replace(".html", "")
                if req.screenIds and sid not in req.screenIds:
                    continue

                _log(buf, f"\n=== Evaluating: {sid} ===")
                with open(os.path.join(screens_dir, file), "r", encoding="utf-8") as f:
                    html = f.read()

                _log(buf, "Running ISO 9241-11 metrics...")
                _log(buf, "Running Nielsen heuristic metrics...")
                _log(buf, "Running WCAG 2.2 metrics (axe-core + BS4)...")

                report = evaluate(html, iteration_number=1)

                _log(buf, f"ISO score:     {report['iso_score']}/100")
                _log(buf, f"Nielsen score: {report['nielsen_score']}/100")
                _log(buf, f"WCAG score:    {report['wcag_score']}/100")
                _log(buf, f"Total score:   {report['total_score']}/100  (threshold: {report['threshold']})")
                _log(buf, f"Status:        {'PASSED ✓' if report['passed'] else 'NEEDS REFINEMENT ✗'}")
                _log(buf, f"Weakest:       {report['weakest_standard']} → {report['weakest_metric']}")

                wcag = report.get('wcag_details', {})
                if wcag.get('reliability') == 'partial':
                    _log(buf, "WARNING: axe-core unavailable — WCAG score is partial (BS4 checks only).")
                elif wcag.get('axe_available'):
                    _log(buf, f"Axe violations: {wcag.get('violations_count', 0)}")

                report_path = os.path.join(reports_dir, f"{sid}_score_report.json")
                save_score_report(report, report_path)
                _log(buf, f"Report saved to {report_path}")
                reports.append({"screenId": sid, "report": report})

            _log(buf, f"\nEvaluation complete. {len(reports)} report(s) saved.")

        return {"reports": reports, "logs": {"stdout": buf.getvalue(), "stderr": ""}}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outputs")
def outputs(screenId: str = None):
    try:
        out_dir = os.path.join(BASE, "outputs", "generated_screens")
        from fastapi import HTTPException

        if screenId:
            html_path = os.path.join(out_dir, f"{screenId}.html")
            if not os.path.exists(html_path):
                raise HTTPException(status_code=404, detail=f"Screen '{screenId}' not found")
            with open(html_path, "r", encoding="utf-8") as f:
                return {"screenId": screenId, "html": f.read()}

        # If directory doesn't exist yet, return empty list
        if not os.path.exists(out_dir):
            return {"screens": []}

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


@app.get("/api/history")
def history(screenId: str):
    try:
        history_path = os.path.join(BASE, "outputs", "score_reports", f"{screenId}_history.json")
        if not os.path.exists(history_path):
            return {"history": []}
        with open(history_path, "r", encoding="utf-8") as f:
            return {"history": json.load(f)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/traceability")
def traceability(screenId: str):
    try:
        plan_path = os.path.join(BASE, "outputs", "screen_plan.json")
        req_path = os.path.join(BASE, "samples", "sample_requirements.json")
        html_path = os.path.join(BASE, "outputs", "generated_screens", f"{screenId}.html")

        if not os.path.exists(html_path):
            raise HTTPException(status_code=404, detail=f"Screen '{screenId}' not found")

        with open(plan_path, "r", encoding="utf-8") as f:
            screens = json.load(f)

        target = None
        if screenId.isdigit():
            idx = int(screenId) - 1
            if 0 <= idx < len(screens):
                target = screens[idx]
        if not target:
            target = next((s for s in screens if s.get("screen_id") == screenId), None)
        if not target:
            raise HTTPException(status_code=404, detail=f"Screen '{screenId}' not found in the screen plan")

        with open(req_path, "r", encoding="utf-8") as f:
            raw_requirements = json.load(f)

        normalized = normalize_input(raw_requirements)
        per_screen = screens_to_requirements([target], normalized)
        if not per_screen:
            return {"traceability": {"matrix": [], "coverage_pct": 0.0, "total_frs": 0, "covered_frs": 0, "untagged_elements": 0, "total_interactive_elements": 0}}

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        traceability_report = build_traceability_matrix(html, per_screen[0].get("functional_requirements", []))
        return {"screenId": screenId, "traceability": traceability_report}
    except HTTPException:
        raise
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
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
