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
from cloudinary_service import upload_html_to_cloudinary, upload_image_to_cloudinary

app = FastAPI(title="UI/UX Usability Agent", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

            # Clear previous session outputs
            for folder in ["generated_screens", "score_reports"]:
                folder_path = os.path.join(BASE, "outputs", folder)
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                os.makedirs(folder_path, exist_ok=True)

            old_plan = os.path.join(BASE, "outputs", "screen_plan.json")
            if os.path.exists(old_plan):
                os.remove(old_plan)
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
            errors = []
            for file in html_files:
                sid = file.replace(".html", "")
                if req.screenIds and sid not in req.screenIds:
                    continue

                try:
                    _log(buf, f"\n=== Evaluating: {sid} ===")
                    with open(os.path.join(screens_dir, file), "r", encoding="utf-8") as f:
                        html = f.read()

                    _log(buf, "Running ISO 9241-11 metrics...")
                    _log(buf, "Running Nielsen heuristic metrics...")
                    _log(buf, "Running WCAG 2.2 metrics (axe-core + BS4)...")

                    report = evaluate(html, iteration_number=1)

                    _log(buf, f"Total score:   {report['total_score']}/100  (threshold: {report['threshold']})")
                    _log(buf, f"Status:        {'PASSED ✓' if report['passed'] else 'NEEDS REFINEMENT ✗'}")

                    wcag = report.get('wcag_details', {})
                    if wcag.get('reliability') == 'partial':
                        _log(buf, "WARNING: axe-core unavailable — WCAG score is partial (BS4 checks only).")

                    report_path = os.path.join(reports_dir, f"{sid}_score_report.json")
                    save_score_report(report, report_path)
                    _log(buf, f"Report saved to {report_path}")
                    reports.append({"screenId": sid, "report": report})

                except Exception as screen_err:
                    # A single screen failing (e.g. axe-core / node hiccup)
                    # must NOT wipe out the results already computed for
                    # every other screen in this batch.
                    _log(buf, f"ERROR evaluating {sid}: {screen_err}")
                    errors.append({"screenId": sid, "error": str(screen_err)})
                    continue

            _log(buf, f"\nEvaluation complete. {len(reports)} succeeded, {len(errors)} failed.")

        return {"reports": reports, "errors": errors, "logs": {"stdout": buf.getvalue(), "stderr": ""}}
    
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
            if not file.endswith("_score_report.json"):  
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


from contracts.v1 import UIRequest, PlannedScreen, UIPackage, SRSDesignAnnex

@app.get("/health")
def health():
    return {"ok": True, "agent": "ui", "schema": "1.0"}


@app.post("/run")
def run(payload: UIRequest) -> dict:
    """
    Standard inter-agent endpoint. Accepts UIRequest, runs planning, generation, evaluation,
    uploads to Cloudinary, and returns UIPackage.
    """
    try:
        # Clear previous session outputs
        for folder in ["generated_screens", "score_reports"]:
            folder_path = os.path.join(BASE, "outputs", folder)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            os.makedirs(folder_path, exist_ok=True)

        old_plan = os.path.join(BASE, "outputs", "screen_plan.json")
        if os.path.exists(old_plan):
            os.remove(old_plan)
        req_dict = {
            "project_name": payload.project_name,
            "domain": payload.domain,
            "functional_requirements": [fr.model_dump() for fr in payload.functional_requirements],
            "non_functional_requirements": [nfr.model_dump() for nfr in payload.non_functional_requirements],
            "design_artifacts": payload.design_artifacts or {
                "class_diagram": {"classes": payload.data_dictionary},
                "er_diagram": {"entities": payload.data_dictionary},
                "sequence_diagram": {"messages": payload.api_contracts},
            },
        }

        # Save to samples/sample_requirements.json
        req_path = os.path.join(BASE, "samples", "sample_requirements.json")
        os.makedirs(os.path.dirname(req_path), exist_ok=True)
        with open(req_path, "w", encoding="utf-8") as f:
            json.dump(req_dict, f, indent=2)

        normalized = normalize_input(req_dict)
        screens = plan_screens(normalized)
        if not screens:
            # Fallback default screens if LLM rate limited
            screens = [
                {
                    "screen_id": "dashboard",
                    "screen_name": f"{payload.project_name} Dashboard",
                    "screen_type": "dashboard",
                    "user_role": "User",
                    "purpose": f"Main operational dashboard for {payload.project_name}",
                    "key_actions": ["View summary", "Navigate modules", "Export data"],
                    "relevant_frs": [fr.id for fr in payload.functional_requirements[:3]],
                    "depends_on": None,
                    "priority": "High"
                }
            ]

        save_screen_plan(screens)

        generated_screens = {}
        eval_reports = []
        refinement_histories = {}
        traceability_matrices = {}
        artifact_uris = {}

        # Generate all planned screens (previously capped at 4 — removed per user request)
        target_screens = screens
        per_screen_reqs = screens_to_requirements(target_screens, normalized)

        for s_req in per_screen_reqs:
            s_id = s_req.get("screen_id", "screen")
            s_type = s_req.get("screen_type", "dashboard")

            # Clear any stale score-report/history from a previous run for
            # this screen_id, so UIReview never shows leftover 0-score data
            # before the user has actually pressed Evaluate.
            reports_dir = os.path.join(BASE, "outputs", "score_reports")
            os.makedirs(reports_dir, exist_ok=True)
            for stale in (f"{s_id}_score_report.json", f"{s_id}_history.json"):
                stale_path = os.path.join(reports_dir, stale)
                if os.path.exists(stale_path):
                    os.remove(stale_path)

            try:
                html = generate_ui(s_req, s_type)
            except Exception as gen_err:
                logging.warning(f"Failed to generate UI for {s_id}: {gen_err}")
                html = f"<!DOCTYPE html><html><body class='p-8 bg-slate-900 text-white'><h1 class='text-2xl font-bold'>{s_req.get('screen_name')}</h1><p class='text-slate-400 mt-2'>{s_req.get('purpose')}</p></body></html>"

            out_dir = os.path.join(BASE, "outputs", "generated_screens")
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, f"{s_id}.html"), "w", encoding="utf-8") as f:
                f.write(html)

            # NOTE: evaluation / score-report / traceability generation is
            # intentionally SKIPPED here so /run stays fast (plan+generate only).
            # These are triggered manually per-screen from UIReview.jsx, which
            # calls /api/evaluate, /api/refine, /api/traceability directly —
            # those endpoints read/write the exact same outputs/ files.

            c_url = upload_html_to_cloudinary(html, payload.job_id, s_id)
            artifact_uris[s_id] = c_url or f"/outputs/generated_screens/{s_id}.html"

            generated_screens[s_id] = html

        planned_pydantic = [PlannedScreen(**s) for s in screens]
        # eval_reports is empty at this point (evaluation happens manually later),
        # so overall_score is just a placeholder — 0.0 means "not yet evaluated".
        overall_score = round(sum(r["report"].get("total_score", 0.0) for r in eval_reports) / max(len(eval_reports), 1), 1)

        pkg = UIPackage(
            schema_version="1.0",
            job_id=payload.job_id,
            project_name=payload.project_name,
            domain=payload.domain,
            screens=planned_pydantic,
            generated_screens=generated_screens,
            evaluation_reports=eval_reports,
            refinement_histories=refinement_histories,
            traceability_matrices=traceability_matrices,
            overall_score=overall_score,
            artifact_uris=artifact_uris
        )
        return pkg.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"UI Agent Generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)

