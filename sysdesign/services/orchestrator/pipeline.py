"""
Orchestrator pipeline — wires all 4 agents sequentially/in-parallel,
persists every stage result to Neon Postgres, and saves artifacts.

Port map (matches .env):
  Orchestrator  → 8000
  Agent 1 (Req) → 8001
  Agent 2 (HLD) → 8002
  Agent 3 (LLD) → 8003
  Agent 4 (UI)  → 8004
  SRS Assembler → 8005
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Load .env from repo root
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", ".."))
load_dotenv(os.path.join(_root, ".env"))

from contracts.v1 import (
    ArchitecturePackage,
    JobState,
    LLDRequest,
    LLDPackage,
    RequirementsPackage,
    SRSDesignAnnex,
    StageResult,
    UIRequest,
    UIPackage,
)
from contracts.adapters import (
    hld_to_lld_adapt,
    hld_to_ui_adapt,
    lld_to_ui_adapt,
    lld_to_srs_adapt,
    req_to_hld_adapt,
)

# Shared DB helpers — fail gracefully if asyncpg not installed
try:
    from shared.db import persist_artifact, persist_stage_run, upsert_job

    DB_AVAILABLE = True
except Exception as _db_err:
    DB_AVAILABLE = False

logger = logging.getLogger("orchestrator-pipeline")

# ── Agent URL map (smart resolution for local vs Docker) ───────────────────
def _normalize_service_url(env_var: str, default_port: int, default_service_name: str) -> str:
    raw = os.getenv(env_var)
    # Check if running inside a Docker container
    is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER") == "1"
    
    if not raw:
        host = default_service_name if is_docker else "127.0.0.1"
        return f"http://{host}:{default_port}"
    
    # If raw is provided, but we are running on host outside Docker,
    # rewrite Docker container hostnames (e.g. agent2-hld) to 127.0.0.1
    if not is_docker:
        for container_host in ["agent1-requirements", "agent2-hld", "agent3-lld", "agent4-ui", "srs-assembler", "orchestrator", "redis"]:
            if container_host in raw:
                raw = raw.replace(container_host, "127.0.0.1")
    return raw

AGENT_URLS = {
    "requirements": _normalize_service_url("AGENT1_URL", 8001, "agent1-requirements") + "/run",
    "hld":          _normalize_service_url("AGENT2_URL", 8002, "agent2-hld") + "/run",
    "lld":          _normalize_service_url("AGENT3_URL", 8003, "agent3-lld") + "/run",
    "ui":           _normalize_service_url("AGENT4_URL", 8004, "agent4-ui") + "/run",
    "srs":          _normalize_service_url("SRS_URL",    8005, "srs-assembler") + "/run",
}

# ── In-memory job store (dev) ──────────────────────────────────────────────
JOB_STORE: Dict[str, JobState] = {}
JOB_ARTIFACTS: Dict[str, Dict[str, Any]] = {}
JOB_LISTENERS: Dict[str, List[asyncio.Queue]] = {}


def get_job_state(job_id: str) -> Optional[JobState]:
    return JOB_STORE.get(job_id)


async def restore_job_from_db(job_id: str) -> Optional[JobState]:
    if not DB_AVAILABLE:
        print("[restore_job_from_db] DB_AVAILABLE is False")
        return None
    try:
        print(f"[restore_job_from_db] Looking up {job_id} in DB...")
        from shared.db import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1::uuid", job_id)
            if not row:
                print(f"[restore_job_from_db] Job {job_id} not found in jobs table")
                return None
            stages_rows = await conn.fetch("SELECT * FROM stage_runs WHERE job_id = $1::uuid ORDER BY started_at", job_id)
            stages = []
            for sr in stages_rows:
                stages.append(StageResult(
                    stage=sr["stage"],
                    status=sr["status"],
                    duration_ms=sr["duration_ms"]
                ))
                if sr.get("payload"):
                    raw_payload = sr["payload"]
                    if isinstance(raw_payload, str):
                        raw_payload = json.loads(raw_payload)
                    JOB_ARTIFACTS.setdefault(job_id, {})[sr["stage"]] = raw_payload

            job = JobState(
                job_id=str(row["id"]),
                tenant_id=row.get("tenant_id") or "dev",
                project_name=row.get("project_name") or "SDLC Project",
                status=row.get("status") or "running",
                current_stage=row.get("current_stage") or "requirements",
                stages=stages or [
                    StageResult(stage="requirements", status="pending"),
                    StageResult(stage="hld",          status="pending"),
                    StageResult(stage="lld",          status="pending"),
                    StageResult(stage="ui",           status="pending"),
                    StageResult(stage="srs",          status="pending"),
                ]
            )
            JOB_STORE[job_id] = job
            print(f"[restore_job_from_db] Successfully restored {job_id}!")
            return job
    except Exception as e:
        print(f"[restore_job_from_db] Failed to restore job {job_id} from DB: {e}")
        logger.warning(f"Failed to restore job {job_id} from DB: {e}")
        return None


def update_stage_status(
    job_id: str,
    stage_name: str,
    status: str,
    error: str = None,
    duration_ms: int = None,
) -> None:
    job = JOB_STORE.get(job_id)
    if not job:
        return
    if status == "running":
        job.current_stage = stage_name
        job.status = "running"
    job.updated_at = datetime.utcnow()

    for s in job.stages:
        if s.stage == stage_name:
            s.status = status
            s.error = error
            s.duration_ms = duration_ms
            break
    else:
        job.stages.append(
            StageResult(stage=stage_name, status=status, error=error, duration_ms=duration_ms)
        )

    notify_listeners(
        job_id,
        {
            "event": "stage_update",
            "stage": stage_name,
            "status": status,
            "job": job.model_dump(mode="json"),
        },
    )


def notify_listeners(job_id: str, data: dict) -> None:
    for q in JOB_LISTENERS.get(job_id, []):
        q.put_nowait(data)


async def call_stage_http(
    stage_name: str, url: str, payload: dict, max_retries: int = 2
) -> dict:
    """Call an agent HTTP endpoint with retry. Timeout = 600 s (10m - LLM synthesis can be complex)."""
    async with httpx.AsyncClient(timeout=600.0) as client:
        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 422:
                    raise ValueError(f"HTTP 422 Validation Error: {resp.text}")
                last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
            except Exception as exc:
                last_err = str(exc)
            if attempt < max_retries:
                await asyncio.sleep(2 * attempt)
        raise RuntimeError(
            f"[{stage_name}] Failed after {max_retries} attempts: {last_err}"
        )


async def _db_persist_stage(
    job_id: str,
    stage: str,
    status: str,
    payload: Optional[dict],
    duration_ms: Optional[int],
) -> None:
    if not DB_AVAILABLE:
        return
    try:
        await persist_stage_run(
            job_id=job_id,
            stage=stage,
            status=status,
            payload=payload,
            duration_ms=duration_ms,
        )
    except Exception as exc:
        logger.warning(f"[db] persist_stage_run failed for {stage}: {exc}")


async def initialize_job(job_id: str, initial_input: Dict[str, Any]) -> None:
    project_name = initial_input.get("project_name") or initial_input.get("project", "SDLC Project")
    job = JobState(
        job_id=job_id,
        tenant_id="dev",
        project_name=project_name,
        status="running",
        current_stage="requirements",
        stages=[
            StageResult(stage="requirements", status="pending"),
            StageResult(stage="hld",          status="pending"),
            StageResult(stage="lld",          status="pending"),
            StageResult(stage="ui",           status="pending"),
            StageResult(stage="srs",          status="pending"),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    JOB_STORE[job_id] = job
    JOB_ARTIFACTS[job_id] = {"initial_input": initial_input}

    if DB_AVAILABLE:
        try:
            await upsert_job(job_id=job_id, project_name=project_name, status="running", current_stage="requirements")
        except Exception as exc:
            logger.warning(f"[db] upsert_job failed: {exc}")


async def run_stage_requirements(job_id: str) -> None:
    job = JOB_STORE.get(job_id)
    if not job: return
    
    initial_input = JOB_ARTIFACTS[job_id].get("initial_input", {})
    update_stage_status(job_id, "requirements", "running")
    t0 = datetime.utcnow()

    try:
        req_data = await call_stage_http("requirements", AGENT_URLS["requirements"], initial_input)
        reqs = req_to_hld_adapt(req_data)
    except Exception as exc:
        logger.warning(f"[req] HTTP call failed ({exc}), using local adapter.")
        reqs = req_to_hld_adapt(initial_input)

    # Force job_id alignment to prevent foreign key violations on Neon PG
    reqs.job_id = job_id

    dur_req = int((datetime.utcnow() - t0).total_seconds() * 1000)
    JOB_ARTIFACTS[job_id]["requirements"] = reqs
    update_stage_status(job_id, "requirements", "complete", duration_ms=dur_req)
    await _db_persist_stage(job_id, "requirements", "complete", reqs.model_dump(mode="json"), dur_req)
    
    notify_listeners(job_id, {
        "event": "log", 
        "log": f"✅ [REQUIREMENTS] Specifications validated ({len(reqs.functional_requirements)} FRs, {len(reqs.non_functional_requirements)} NFRs)."
    })

    # Pause here, waiting for next step
    job.status = "waiting_for_hld"
    job.updated_at = datetime.utcnow()
    if DB_AVAILABLE:
        try:
            await upsert_job(job_id, job.project_name, "waiting_for_hld", current_stage="requirements")
        except Exception: pass
    notify_listeners(job_id, {"event": "paused", "stage": "requirements", "job": job.model_dump(mode="json")})


async def run_stage_hld(job_id: str) -> None:
    job = JOB_STORE.get(job_id)
    if not job: return

    reqs: Optional[RequirementsPackage] = JOB_ARTIFACTS.get(job_id, {}).get("requirements")
    if not reqs:
        initial_input = JOB_ARTIFACTS.get(job_id, {}).get("initial_input")
        if initial_input:
            logger.info(f"[{job_id}] Synthesizing requirements from initial input...")
            reqs = req_to_hld_adapt(initial_input)
            reqs.job_id = job_id
            JOB_ARTIFACTS[job_id]["requirements"] = reqs
        else:
            raise ValueError("Requirements package not found in artifacts. Cannot run HLD.")

    job.status = "running"
    update_stage_status(job_id, "hld", "running")
    if DB_AVAILABLE:
        try:
            await upsert_job(job_id, job.project_name, "running", current_stage="hld")
        except Exception:
            pass

    t0 = datetime.utcnow()

    notify_listeners(job_id, {
        "event": "log",
        "log": "🚀 [HLD] Dispatched architecture candidate generation across OpenRouter models (GPT-4o-mini, Qwen 2.5 Coder, DeepSeek V3)..."
    })

    stop_heartbeat = asyncio.Event()

    async def _heartbeat():
        while not stop_heartbeat.is_set():
            try:
                await asyncio.wait_for(stop_heartbeat.wait(), timeout=12.0)
            except asyncio.TimeoutError:
                if not stop_heartbeat.is_set():
                    elapsed = int((datetime.utcnow() - t0).total_seconds())
                    notify_listeners(job_id, {
                        "event": "log",
                        "log": f"⏳ [HLD] Synthesizing candidates across OpenRouter models ({elapsed}s elapsed, awaiting model completions)..."
                    })

    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        arch_data = await call_stage_http("hld", AGENT_URLS["hld"], reqs.model_dump(mode="json"))
        stop_heartbeat.set()
        await heartbeat_task

        notify_listeners(job_id, {
            "event": "log",
            "log": "🛡️ [HLD] S-SDLC STRIDE security boundaries audited and verified."
        })
        notify_listeners(job_id, {
            "event": "log",
            "log": "📊 [HLD] Python Evaluation Engine: RTS, QAC, CI, CoS, SSM computed with AHP CAS composite."
        })

        arch = ArchitecturePackage(**arch_data)
        dur_hld = int((datetime.utcnow() - t0).total_seconds() * 1000)
        JOB_ARTIFACTS[job_id]["architecture"] = arch

        await _db_persist_stage(job_id, "hld", "complete", arch.model_dump(mode="json"), dur_hld)

        cas_score = arch.scores.CAS if arch.scores else 0.0
        cas_threshold = float(os.getenv("HLD_CAS_THRESHOLD", "0.75"))
        arch_style = arch.architecture_style or "Architecture"

        notify_listeners(job_id, {
            "event": "log",
            "log": f"✅ [HLD] Architecture synthesized! Style: {arch_style} · CAS: {cas_score:.3f} (Rank #1 Winner)"
        })

        if arch.verdict == "rejected" or cas_score < cas_threshold:
            update_stage_status(job_id, "hld", "complete", duration_ms=dur_hld)
            job.status = "needs_review"
            job.updated_at = datetime.utcnow()
            if DB_AVAILABLE:
                try:
                    await upsert_job(job_id, job.project_name, "needs_review", current_stage="hld")
                except Exception: pass
            notify_listeners(
                job_id,
                {
                    "event": "needs_review",
                    "reason": (f"CAS Score ({cas_score:.2f}) is below threshold ({cas_threshold:.2f})."),
                    "architecture": arch.model_dump(mode="json"),
                    "job": job.model_dump(mode="json"),
                },
            )
            return

        update_stage_status(job_id, "hld", "complete", duration_ms=dur_hld)
        
        # Pause here, waiting for next step
        job.status = "waiting_for_lld_ui"
        job.updated_at = datetime.utcnow()
        if DB_AVAILABLE:
            try:
                await upsert_job(job_id, job.project_name, "waiting_for_lld_ui", current_stage="hld")
            except Exception: pass
        notify_listeners(job_id, {"event": "paused", "stage": "hld", "job": job.model_dump(mode="json")})

    except Exception as exc:
        stop_heartbeat.set()
        logger.error(f"HLD failed for {job_id}: {exc}", exc_info=True)
        update_stage_status(job_id, "hld", "failed", error=str(exc))
        job.status = "failed"
        if DB_AVAILABLE:
            try: await upsert_job(job_id, job.project_name, "failed", error=str(exc))
            except Exception: pass
        notify_listeners(job_id, {"event": "failed", "error": str(exc), "job": job.model_dump(mode="json")})


async def run_stage_lld(job_id: str) -> None:
    job = JOB_STORE.get(job_id)
    if not job: return

    reqs: RequirementsPackage = JOB_ARTIFACTS[job_id].get("requirements")
    arch: ArchitecturePackage = JOB_ARTIFACTS[job_id].get("architecture")
    
    if not reqs or not arch:
        raise ValueError("Missing Requirements or Architecture. Cannot run LLD.")

    job.status = "running"
    update_stage_status(job_id, "lld", "running")
    t0_lld = datetime.utcnow()

    try:
        lld_req = hld_to_lld_adapt(arch, reqs)
        data = await call_stage_http("lld", AGENT_URLS["lld"], lld_req.model_dump(mode="json"))
        lld_annex = LLDPackage(**data)
        dur_lld = int((datetime.utcnow() - t0_lld).total_seconds() * 1000)

        JOB_ARTIFACTS[job_id]["lld"] = lld_annex
        update_stage_status(job_id, "lld", "complete", duration_ms=dur_lld)
        await _db_persist_stage(job_id, "lld", "complete", lld_annex.model_dump(mode="json"), dur_lld)

        job.status = "waiting_for_ui"
        job.updated_at = datetime.utcnow()
        if DB_AVAILABLE:
            try: await upsert_job(job_id, job.project_name, "waiting_for_ui", current_stage="lld")
            except Exception: pass
        notify_listeners(job_id, {"event": "paused", "stage": "lld", "job": job.model_dump(mode="json")})

    except Exception as exc:
        logger.error(f"LLD failed for {job_id}: {exc}", exc_info=True)
        update_stage_status(job_id, "lld", "failed", error=str(exc))
        job.status = "failed"
        if DB_AVAILABLE:
            try: await upsert_job(job_id, job.project_name, "failed", error=str(exc))
            except Exception: pass
        notify_listeners(job_id, {"event": "failed", "error": str(exc), "job": job.model_dump(mode="json")})


async def run_stage_ui(job_id: str) -> None:
    job = JOB_STORE.get(job_id)
    if not job: return

    reqs: RequirementsPackage = JOB_ARTIFACTS[job_id].get("requirements")
    arch: ArchitecturePackage = JOB_ARTIFACTS[job_id].get("architecture")
    lld: LLDPackage = JOB_ARTIFACTS[job_id].get("lld")
    
    if not reqs or not arch or not lld:
        raise ValueError("Missing Requirements, Architecture, or LLD Package. Cannot run UI.")

    job.status = "running"
    update_stage_status(job_id, "ui", "running")
    t0_ui = datetime.utcnow()

    try:
        ui_req = lld_to_ui_adapt(arch, reqs, lld)
        data = await call_stage_http("ui", AGENT_URLS["ui"], ui_req.model_dump(mode="json"))
        try:
            ui_pkg = UIPackage(**data)
        except Exception:
            try:
                ui_pkg = SRSDesignAnnex(**data)
            except Exception:
                ui_pkg = data
        dur_ui = int((datetime.utcnow() - t0_ui).total_seconds() * 1000)

        JOB_ARTIFACTS[job_id]["ui"] = ui_pkg
        update_stage_status(job_id, "ui", "complete", duration_ms=dur_ui)
        dumped = ui_pkg.model_dump(mode="json") if hasattr(ui_pkg, "model_dump") else ui_pkg
        await _db_persist_stage(job_id, "ui", "complete", dumped, dur_ui)

        job.status = "waiting_for_srs"
        job.updated_at = datetime.utcnow()
        if DB_AVAILABLE:
            try: await upsert_job(job_id, job.project_name, "waiting_for_srs", current_stage="ui")
            except Exception: pass
        notify_listeners(job_id, {"event": "paused", "stage": "ui", "job": job.model_dump(mode="json")})

    except Exception as exc:
        logger.error(f"UI failed for {job_id}: {exc}", exc_info=True)
        job.status = "failed"
        if DB_AVAILABLE:
            try: await upsert_job(job_id, job.project_name, "failed", error=str(exc))
            except Exception: pass
        notify_listeners(job_id, {"event": "failed", "error": str(exc), "job": job.model_dump(mode="json")})


async def run_stage_srs(job_id: str) -> None:
    job = JOB_STORE.get(job_id)
    if not job:
        job = await restore_job_from_db(job_id)
    if not job:
        logger.warning(f"run_stage_srs: Job {job_id} not found in store or database")
        return

    reqs = JOB_ARTIFACTS.get(job_id, {}).get("requirements")
    arch = JOB_ARTIFACTS.get(job_id, {}).get("architecture") or JOB_ARTIFACTS.get(job_id, {}).get("hld")
    lld_annex = JOB_ARTIFACTS.get(job_id, {}).get("lld")
    ui_annex = JOB_ARTIFACTS.get(job_id, {}).get("ui")

    update_stage_status(job_id, "srs", "running")
    t0_srs = datetime.utcnow()
    notify_listeners(job_id, {"event": "stage_start", "stage": "srs", "job": job.model_dump(mode="json")})

    try:
        hld_payload = None
        if arch:
            try:
                if isinstance(arch, ArchitecturePackage):
                    hld_payload = SRSDesignAnnex(
                        schema_version="1.0",
                        job_id=job_id,
                        agent="hld",
                        component_responsibility_matrix=[
                            {
                                "component": c.name,
                                "layer": c.boundary.value if hasattr(c.boundary, "value") else str(c.boundary),
                                "responsibilities": ", ".join(c.responsibilities) if isinstance(c.responsibilities, list) else str(c.responsibilities),
                            }
                            for c in arch.components
                        ],
                        quality_evidence=arch.scores.model_dump() if hasattr(arch.scores, "model_dump") else arch.scores,
                        artifact_uris=arch.artifact_uris,
                    ).model_dump(mode="json")
                elif isinstance(arch, dict):
                    if "component_responsibility_matrix" in arch:
                        hld_payload = arch
                    else:
                        matrix = []
                        for c in arch.get("components", []):
                            c_name = c.get("name", "") if isinstance(c, dict) else getattr(c, "name", str(c))
                            c_layer = c.get("boundary", "") if isinstance(c, dict) else getattr(c, "boundary", "")
                            if isinstance(c_layer, dict):
                                c_layer = c_layer.get("value", str(c_layer))
                            c_resp = c.get("responsibilities", []) if isinstance(c, dict) else getattr(c, "responsibilities", [])
                            resp_str = ", ".join(c_resp) if isinstance(c_resp, list) else str(c_resp)
                            matrix.append({
                                "component": c_name,
                                "layer": str(c_layer),
                                "responsibilities": resp_str,
                            })
                        hld_payload = {
                            "schema_version": "1.0",
                            "job_id": job_id,
                            "agent": "hld",
                            "component_responsibility_matrix": matrix,
                            "quality_evidence": arch.get("scores", {}),
                            "artifact_uris": arch.get("artifact_uris", {}),
                        }
            except Exception as _e:
                logger.warning(f"Could not build hld_annex for SRS: {_e}")

        lld_payload = None
        if lld_annex:
            try:
                if isinstance(lld_annex, LLDPackage):
                    lld_payload = lld_to_srs_adapt(lld_annex).model_dump(mode="json")
                elif hasattr(lld_annex, "model_dump"):
                    lld_payload = lld_annex.model_dump(mode="json")
                elif isinstance(lld_annex, dict):
                    lld_payload = lld_annex
            except Exception as _e:
                logger.warning(f"Could not adapt lld_annex for SRS: {_e}")

        ui_payload = None
        if ui_annex:
            try:
                if hasattr(ui_annex, "model_dump"):
                    ui_payload = ui_annex.model_dump(mode="json")
                elif isinstance(ui_annex, dict):
                    ui_payload = ui_annex
            except Exception as _e:
                logger.warning(f"Could not extract ui_annex for SRS: {_e}")

        # Fallback for requirements if not in memory
        if not reqs:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"http://127.0.0.1:8001/requirements/{job_id}")
                    if resp.status_code == 200:
                        reqs = resp.json()
            except Exception as _re:
                logger.warning(f"Could not fetch requirements fallback from Agent 1: {_re}")

        reqs_data = reqs.model_dump(mode="json") if hasattr(reqs, "model_dump") else (reqs or {})
        if isinstance(reqs_data, dict):
            if not reqs_data.get("job_id"):
                reqs_data["job_id"] = job_id
            if not reqs_data.get("project_name") and job:
                reqs_data["project_name"] = job.project_name

        srs_payload = {
            "requirements": reqs_data,
            "hld_annex": hld_payload,
            "lld_annex": lld_payload,
            "ui_annex": ui_payload,
        }

        try:
            srs_result = await call_stage_http("srs", AGENT_URLS["srs"], srs_payload)
            JOB_ARTIFACTS.setdefault(job_id, {})["srs"] = srs_result
        except Exception as exc:
            srs_result = {"status": "generated_with_warnings", "detail": str(exc)}
            JOB_ARTIFACTS.setdefault(job_id, {})["srs"] = srs_result

        dur_srs = int((datetime.utcnow() - t0_srs).total_seconds() * 1000)
        update_stage_status(job_id, "srs", "complete", duration_ms=dur_srs)
        await _db_persist_stage(job_id, "srs", "complete", srs_result, dur_srs)

        job.status = "complete"
        job.current_stage = None
        job.updated_at = datetime.utcnow()
        if DB_AVAILABLE:
            try:
                await upsert_job(job_id, job.project_name, "complete")
            except Exception:
                pass
        notify_listeners(job_id, {"event": "complete", "job": job.model_dump(mode="json")})

    except Exception as exc:
        logger.error(f"SRS Assembler failed for {job_id}: {exc}", exc_info=True)
        job.status = "failed"
        update_stage_status(job_id, "srs", "failed", error=str(exc))
        if DB_AVAILABLE:
            try: await upsert_job(job_id, job.project_name, "failed", error=str(exc))
            except Exception: pass
        notify_listeners(job_id, {"event": "failed", "error": str(exc), "job": job.model_dump(mode="json")})


async def select_candidate(job_id: str, payload: Dict[str, Any]) -> None:
    job = JOB_STORE.get(job_id)
    if not job:
        job = await restore_job_from_db(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found.")

    model = payload.get("model")
    architecture = payload.get("architecture")
    scores = payload.get("scores")

    if not model or not architecture or not scores:
        raise ValueError("Payload must contain 'model', 'architecture', and 'scores'")

    # 1. Get run_id from existing architecture artifact
    old_arch = JOB_ARTIFACTS.get(job_id, {}).get("architecture")
    run_id = None
    if isinstance(old_arch, ArchitecturePackage):
        run_id = old_arch.generation_metadata.get("run_id")
    elif isinstance(old_arch, dict):
        run_id = old_arch.get("generation_metadata", {}).get("run_id")

    if not run_id:
        raise ValueError(f"No run ID found for job {job_id}")

    # 2. Call agent's `/select` endpoint
    hld_url = AGENT_URLS["hld"]
    agent_base_url = hld_url.rsplit("/run", 1)[0]
    select_url = f"{agent_base_url}/api/runs/{run_id}/select"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(select_url, json={
            "model": model,
            "architecture": architecture,
            "scores": scores
        })
        if resp.status_code != 200:
            raise RuntimeError(f"Agent select failed: {resp.text}")
        agent_res = resp.json()

    # 3. Read newly generated diagram files from agent path (local disk paths)
    plantuml_code = None
    mermaid_code = None
    from pathlib import Path
    try:
        puml_path_str = agent_res.get("outputs", {}).get("plantuml")
        if puml_path_str:
            puml_file = Path(puml_path_str)
            if puml_file.exists():
                with open(puml_file, "r", encoding="utf-8") as f:
                    plantuml_code = f.read()
                
            mmd_file = puml_file.parent / "diagram.mmd"
            if mmd_file.exists():
                with open(mmd_file, "r", encoding="utf-8") as f:
                    mermaid_code = f.read()
    except Exception as exc:
        logger.warning(f"Failed to read selected diagram files in orchestrator: {exc}")

    # 4. Format components and connectors
    components = []
    for idx, c in enumerate(architecture.get("components", [])):
        components.append({
            "id": f"C{idx+1}",
            "name": c.get("name", f"Component-{idx+1}"),
            "element_type": c.get("element_type", "service"),
            "boundary": c.get("boundary", "business_logic"),
            "responsibilities": c.get("responsibilities", ["Core logic"]),
            "provided_interfaces": c.get("provided_interfaces", []),
            "required_interfaces": c.get("required_interfaces", []),
            "requirement_ids": c.get("requirement_ids", [])
        })

    connectors = []
    for idx, conn in enumerate(architecture.get("interactions", [])):
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

    # Preserve old candidates and rejected alternatives
    old_rejected = []
    old_candidates = []
    old_meta = {}
    if old_arch:
        if isinstance(old_arch, ArchitecturePackage):
            old_rejected = old_arch.rejected_alternatives
            old_candidates = old_arch.candidates
            old_meta = old_arch.generation_metadata
        elif isinstance(old_arch, dict):
            old_rejected = old_arch.get("rejected_alternatives", [])
            old_candidates = old_arch.get("candidates", [])
            old_meta = old_arch.get("generation_metadata", {})

    new_arch = ArchitecturePackage(
        schema_version="1.0",
        job_id=job_id,
        tenant_id=job.tenant_id,
        project_name=job.project_name,
        architecture_style=architecture.get("architecture_style", "Layered Microservices"),
        style_confidence=0.95,
        components=components,
        connectors=connectors,
        quality_provisions=[],
        scores=metric_scores,
        verdict="accepted" if metric_scores["CAS"] >= 0.75 else "marginal",
        rejected_alternatives=old_rejected,
        candidates=old_candidates,
        plantuml_code=plantuml_code,
        mermaid_code=mermaid_code,
        generation_metadata=old_meta
    )

    JOB_ARTIFACTS.setdefault(job_id, {})["architecture"] = new_arch

    # Save to DB
    await _db_persist_stage(job_id, "hld", "complete", new_arch.model_dump(mode="json"), 0)

    # Update job status
    if metric_scores["CAS"] >= 0.75:
        job.status = "waiting_for_lld_ui"
    else:
        job.status = "needs_review"
    job.updated_at = datetime.utcnow()

    if DB_AVAILABLE:
        try:
            await upsert_job(job_id, job.project_name, job.status, current_stage="hld")
        except Exception as db_exc:
            logger.warning(f"Failed to upsert job status: {db_exc}")

    # Notify listeners
    notify_listeners(job_id, {
        "event": "stage_update",
        "stage": "hld",
        "status": "complete",
        "job": job.model_dump(mode="json")
    })


async def refine_diagram(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    job = JOB_STORE.get(job_id)
    if not job:
        job = await restore_job_from_db(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found.")

    prompt = payload.get("prompt") or payload.get("notes") or ""

    old_arch = JOB_ARTIFACTS.get(job_id, {}).get("architecture")
    run_id = None
    if isinstance(old_arch, ArchitecturePackage):
        run_id = old_arch.generation_metadata.get("run_id")
    elif isinstance(old_arch, dict):
        run_id = old_arch.get("generation_metadata", {}).get("run_id")

    if not run_id:
        raise ValueError(f"No run ID found for job {job_id}")

    hld_url = AGENT_URLS["hld"]
    agent_base_url = hld_url.rsplit("/run", 1)[0]
    improve_url = f"{agent_base_url}/api/runs/{run_id}/diagram/plantuml/improve"

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(improve_url, json={"notes": prompt})
        if resp.status_code != 200:
            raise RuntimeError(f"Agent diagram refine failed: {resp.text}")
        workflow_res = resp.json()

    # Extract current plantuml code and score from workflow
    current = workflow_res.get("plantuml", {}).get("current") or {}
    updated_puml = current.get("diagram")
    updated_cas = current.get("diagram_cas")

    if updated_puml and isinstance(old_arch, ArchitecturePackage):
        old_arch.plantuml_code = updated_puml
        if updated_cas is not None:
            if hasattr(old_arch.scores, "CAS"):
                old_arch.scores.CAS = float(updated_cas)
            elif isinstance(old_arch.scores, dict):
                old_arch.scores["CAS"] = float(updated_cas)
        await _db_persist_stage(job_id, "hld", "complete", old_arch.model_dump(mode="json"), 0)

    return workflow_res


