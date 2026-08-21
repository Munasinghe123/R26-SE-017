import json
import db.config as db


async def save_srs_draft(project_id, content):
    async with db.pool.acquire() as connection:
        draft = await connection.fetchrow(
            """
            INSERT INTO srs_draft (
                project_id,
                content
            )
            VALUES (
                $1,
                $2::jsonb
            )
            RETURNING id, project_id, content, created_at, updated_at;
            """,
            project_id,
            json.dumps(content)
        )

    return draft