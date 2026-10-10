"""
HLA Agent — Neon Postgres Writer (Shared Research Dataset)

Dual-write strategy:
  - SQLite  → fast local history (offline-capable, per-developer)
  - Neon PG → shared thesis dataset (all collaborators, all runs)

Writes to: architecture_candidates (infra/create_tables.py schema)
Fails gracefully — a Neon error never kills the pipeline.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ── Neon connection (lazy, cached) ─────────────────────────────────────────
_neon_conn = None


def _get_neon_url() -> Optional[str]:
    """Read NEON_DATABASE_URL from agent2-hld .env, then root .env."""
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")  # repo root
    return os.getenv("NEON_DATABASE_URL", "")


def _get_neon_connection():
    """Return a psycopg2 connection, or None if unavailable."""
    global _neon_conn
    if _neon_conn is not None:
        try:
            _neon_conn.cursor().execute("SELECT 1")
            return _neon_conn
        except Exception:
            _neon_conn = None

    url = _get_neon_url()
    if not url:
        return None

    try:
        import psycopg2
        _neon_conn = psycopg2.connect(url)
        _neon_conn.autocommit = True
        logger.info("Neon Postgres: connected (architecture_candidates writer active)")
        return _neon_conn
    except ImportError:
        logger.warning("psycopg2 not installed — skipping Neon write. Run: pip install psycopg2-binary")
        return None
    except Exception as e:
        logger.warning(f"Neon Postgres: connection failed ({e}) — running in local-only mode")
        return None


def record_candidate(
    job_id: Optional[str],
    case_study_id: str,
    llm_model: str,
    seed: int,
    detected_style: str,
    style_confidence: float,
    scores: dict,
    rank_position: int,
    cam: dict,
) -> bool:
    """
    Write one evaluated architecture candidate to the shared Neon DB.

    Maps agent2-hld internal scores to the architecture_candidates schema:
      rts, qac, ci, cos, ssm1, ssm2, cas, verdict, detected_style

    Returns True on success, False on any error (pipeline continues either way).
    """
    conn = _get_neon_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()

        # job_id must be a valid UUID for the FK — use None if not a UUID
        import uuid as _uuid
        try:
            pg_job_id = str(_uuid.UUID(str(job_id))) if job_id else None
        except (ValueError, AttributeError):
            pg_job_id = None  # non-UUID job IDs (dev runs) skip the FK

        cur.execute("""
            INSERT INTO architecture_candidates
              (job_id, case_study_id, llm_model, seed,
               detected_style, style_confidence,
               rts, qac, ci, cos, ssm1, ssm2, cas,
               verdict, rank_position, cam)
            VALUES
              (%s, %s, %s, %s,
               %s, %s,
               %s, %s, %s, %s, %s, %s, %s,
               %s, %s, %s)
        """, (
            pg_job_id,
            case_study_id,
            llm_model,
            seed,
            detected_style,
            round(float(style_confidence), 3),
            round(float(scores.get("RTS",  0)), 3),
            round(float(scores.get("QAC",  0)), 3),
            round(float(scores.get("CI",   0)), 3),
            round(float(scores.get("CoS",  0)), 3),
            round(float(scores.get("SSM1", 0)), 3),
            round(float(scores.get("SSM2", 0)), 3),
            round(float(scores.get("CAS",  0)), 3),
            scores.get("verdict", "marginal"),
            rank_position,
            json.dumps(cam),
        ))

        logger.info(
            f"Neon: recorded {llm_model} | style={detected_style} | "
            f"CAS={scores.get('CAS', 0):.3f} | rank={rank_position}"
        )
        return True

    except Exception as e:
        logger.warning(f"Neon write failed (non-fatal): {e}")
        global _neon_conn
        _neon_conn = None
        return False
