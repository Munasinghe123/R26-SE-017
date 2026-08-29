"""
shared.db — Shared Neon Postgres connection pool for all R26-SE-017 agents.

Usage (in any agent's main.py):
    from shared.db import engine, get_db, persist_stage_run, persist_artifact

Every agent uses the NEON_DATABASE_URL env var — the same pooler endpoint.
SQLAlchemy 2.x async engine is used so any FastAPI service can import this
without conflicts.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional

from dotenv import load_dotenv

# Load .env from repo root (two dirs up from packages/shared/)
_here = os.path.dirname(__file__)
_root = os.path.abspath(os.path.join(_here, "..", ".."))
load_dotenv(os.path.join(_root, ".env"))

logger = logging.getLogger("shared.db")

DATABASE_URL: str = os.getenv("NEON_DATABASE_URL", "")

# ── Lazy engine: only created on first import after env is loaded ──────────
_engine = None
_async_session_factory = None


def _get_engine():
    global _engine, _async_session_factory
    if _engine is not None:
        return _engine

    if not DATABASE_URL:
        raise RuntimeError(
            "NEON_DATABASE_URL is not set. "
            "Copy .env.example to .env and fill in the Neon pooler URL."
        )

    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        # asyncpg driver — use postgresql+asyncpg scheme
        async_url = DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        ).replace("?sslmode", "?ssl")

        # Remove channel_binding param — asyncpg doesn't understand it
        # but Neon's pooler endpoint still works without it
        if "channel_binding" in async_url:
            parts = async_url.split("&")
            async_url = "&".join(p for p in parts if "channel_binding" not in p)

        _engine = create_async_engine(
            async_url,
            pool_pre_ping=True,
            pool_size=3,
            max_overflow=5,
            pool_recycle=300,
            echo=False,
        )
        _async_session_factory = sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Shared Neon Postgres engine created.")
    except ImportError:
        logger.warning(
            "SQLAlchemy/asyncpg not installed — shared.db will use asyncpg directly."
        )
        _engine = "asyncpg_fallback"

    return _engine


@asynccontextmanager
async def get_db() -> AsyncGenerator:
    """Yield an AsyncSession. Use as: `async with get_db() as session:`"""
    engine = _get_engine()
    if engine == "asyncpg_fallback":
        yield None
        return

    from sqlalchemy.ext.asyncio import AsyncSession

    async with _async_session_factory() as session:  # type: AsyncSession
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Raw asyncpg helpers (lightweight, used by legacy Agent 1 code) ─────────

_pool = None


async def get_pool():
    """Return an asyncpg connection pool. Lazily created on first call."""
    global _pool
    if _pool is not None:
        return _pool

    import asyncpg  # type: ignore

    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
        command_timeout=30,
    )
    logger.info("Shared asyncpg pool created.")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── High-level persistence helpers ─────────────────────────────────────────

async def upsert_job(
    job_id: str,
    project_name: str,
    status: str,
    tenant_id: str = "dev",
    created_by: str = "dev-user",
    input_kind: str = "requirements",
    input_uri: Optional[str] = None,
    current_stage: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """Insert or update a job row in the `jobs` table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO jobs (id, tenant_id, created_by, project_name, status,
                              input_kind, input_uri, current_stage, error, updated_at)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, now())
            ON CONFLICT (id) DO UPDATE SET
                status        = EXCLUDED.status,
                current_stage = EXCLUDED.current_stage,
                error         = EXCLUDED.error,
                updated_at    = now()
            """,
            job_id, tenant_id, created_by, project_name,
            status, input_kind, input_uri, current_stage, error,
        )


async def persist_stage_run(
    job_id: str,
    stage: str,
    status: str,
    payload: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
    attempt: int = 1,
    llm_backend: Optional[str] = None,
    schema_version: str = "1.0",
) -> str:
    """
    Insert a stage_runs row and return the new row UUID.
    Call this once per stage, at completion (or failure).
    """
    pool = await get_pool()
    row_id = str(uuid.uuid4())
    payload_json = json.dumps(payload) if payload else None

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO stage_runs
                (id, job_id, stage, attempt, status, payload, schema_version,
                 llm_backend, duration_ms, finished_at)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5,
                    $6::jsonb, $7, $8, $9, now())
            """,
            row_id, job_id, stage, attempt, status,
            payload_json, schema_version, llm_backend, duration_ms,
        )
    return row_id


async def persist_artifact(
    job_id: str,
    stage: str,
    kind: str,
    filename: str,
    uri: str,
    mime_type: str,
    size_bytes: Optional[int] = None,
) -> str:
    """Insert an artifacts row and return the new row UUID."""
    pool = await get_pool()
    row_id = str(uuid.uuid4())

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO artifacts
                (id, job_id, stage, kind, filename, uri, mime_type, size_bytes)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8)
            """,
            row_id, job_id, stage, kind, filename, uri, mime_type, size_bytes,
        )
    return row_id


async def get_job_artifacts(job_id: str) -> list:
    """Fetch all artifact rows for a job."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM artifacts WHERE job_id = $1::uuid ORDER BY created_at",
            job_id,
        )
    return [dict(r) for r in rows]


async def get_stage_results(job_id: str) -> list:
    """Fetch all stage_run rows for a job, ordered by stage."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM stage_runs WHERE job_id = $1::uuid ORDER BY started_at",
            job_id,
        )
    return [dict(r) for r in rows]
