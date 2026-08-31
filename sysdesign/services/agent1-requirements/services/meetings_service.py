import json
import os
import uuid
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("agent1.meetings")

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "meetings")
os.makedirs(CACHE_DIR, exist_ok=True)


async def save_meeting_requirements(
    meeting_id: str,
    requirements: Dict[str, Any],
    client_view: Optional[Dict[str, Any]] = None,
    version: int = 1,
    project_id: Optional[str] = None
) -> str:
    """Save extracted or refined requirements to DB and local cache."""
    if not meeting_id:
        return ""

    # 1. Local JSON cache fallback
    try:
        cache_file = os.path.join(CACHE_DIR, f"{meeting_id}.json")
        cache_data = {
            "id": meeting_id,
            "requirements": requirements,
            "client_view": client_view,
            "version": version,
            "project_id": project_id
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Failed to write meeting cache file: {e}")

    # 2. Neon Postgres asyncpg pool
    try:
        import db.config as db
        if db.pool:
            reqs_json = json.dumps(requirements, default=str) if requirements else None
            cview_json = json.dumps(client_view, default=str) if client_view else None
            
            p_uuid = None
            if project_id:
                try:
                    p_uuid = uuid.UUID(project_id)
                except Exception:
                    p_uuid = None

            m_uuid = None
            try:
                m_uuid = uuid.UUID(meeting_id)
            except Exception:
                m_uuid = None

            if m_uuid:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO meetings (id, project_id, status, requirements, client_view, version, updated_at)
                        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, now())
                        ON CONFLICT (id) DO UPDATE SET
                            requirements = EXCLUDED.requirements,
                            client_view = EXCLUDED.client_view,
                            version = EXCLUDED.version,
                            updated_at = now();
                        """,
                        m_uuid,
                        p_uuid,
                        "ready_for_review",
                        reqs_json,
                        cview_json,
                        version
                    )
                logger.info(f"Persisted meeting {meeting_id} to database successfully.")
    except Exception as e:
        logger.warning(f"Failed to persist meeting to database: {e}")

    return meeting_id


async def get_meeting_requirements(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve requirements for a meeting from DB or local cache."""
    if not meeting_id:
        return None

    # 1. Try Neon Postgres
    try:
        import db.config as db
        if db.pool:
            m_uuid = None
            try:
                m_uuid = uuid.UUID(meeting_id)
            except Exception:
                pass

            async with db.pool.acquire() as conn:
                row = None
                if m_uuid:
                    row = await conn.fetchrow(
                        """
                        SELECT id, project_id, requirements, client_view, version, status
                        FROM meetings
                        WHERE id = $1 OR project_id = $1
                        ORDER BY updated_at DESC
                        LIMIT 1;
                        """,
                        m_uuid
                    )

                if row and row["requirements"]:
                    reqs = row["requirements"]
                    if isinstance(reqs, str):
                        reqs = json.loads(reqs)
                    cview = row["client_view"]
                    if isinstance(cview, str):
                        cview = json.loads(cview)
                    return {
                        "id": str(row["id"]),
                        "requirements": reqs,
                        "client_view": cview,
                        "version": row["version"] or 1,
                        "status": row["status"]
                    }
    except Exception as e:
        logger.warning(f"Could not load meeting {meeting_id} from database: {e}")

    # 2. Try Local File Cache
    try:
        cache_file = os.path.join(CACHE_DIR, f"{meeting_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
    except Exception as e:
        logger.warning(f"Could not load meeting {meeting_id} from file cache: {e}")

    return None
