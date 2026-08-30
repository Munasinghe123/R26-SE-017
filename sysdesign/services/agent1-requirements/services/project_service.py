
import db.config as db
from fastapi import HTTPException


async def create_project_service(creator_id, data):

    async with db.pool.acquire() as connection:

        async with connection.transaction():

            # 1. Make sure the creator exists and is a USER
            creator = await connection.fetchrow(
                """
                SELECT id, role
                FROM users
                WHERE id = $1;
                """,
                creator_id
            )

            if not creator:
                raise HTTPException(
                    status_code=404,
                    detail="Creator not found"
                )

            if creator["role"] not in ("USER", "PRODUCT_OWNER"):
                raise HTTPException(
                    status_code=400,
                    detail="User cannot create a project"
                )

            # 2. Make sure the selected client exists and is a USER
            client = await connection.fetchrow(
                """
                SELECT id, role
                FROM users
                WHERE id = $1;
                """,
                data.clientId
            )

            if not client:
                raise HTTPException(
                    status_code=404,
                    detail="Client not found"
                )

            # 3. Change creator → PRODUCT_OWNER
            await connection.execute(
                """
                UPDATE users
                SET role = 'PRODUCT_OWNER'
                WHERE id = $1;
                """,
                creator_id
            )

            # 4. Change selected user → CLIENT
            await connection.execute(
                """
                UPDATE users
                SET role = 'CLIENT'
                WHERE id = $1;
                """,
                data.clientId
            )

            # 5. Create the project
            project = await connection.fetchrow(
                """
                INSERT INTO projects (
                    id,
                    name,
                    description,
                    product_owner_id,
                    client_id
                )
                VALUES (
                    gen_random_uuid(),
                    $1,
                    $2,
                    $3,
                    $4
                )
                RETURNING id, name, description, product_owner_id, client_id, created_at;
                """,
                data.projectName,
                data.projectDescription,
                creator_id,
                data.clientId
            )

    return {
        "message": "Project created successfully",
        "project": {
            "id": str(project["id"]),
            "name": project["name"],
            "description": project["description"],
            "product_owner_id": str(project["product_owner_id"]),
            "client_id": str(project["client_id"]),
            "created_at": project["created_at"],
        }
    }


async def get_projects_by_user_service(user_id):
    async with db.pool.acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT p.id, p.name, p.description, p.product_owner_id, p.client_id, p.created_at,
                   COALESCE(u1.name, 'Product Owner') AS product_owner_name,
                   COALESCE(u2.name, 'Client') AS client_name
            FROM projects p
            LEFT JOIN users u1 ON p.product_owner_id = u1.id
            LEFT JOIN users u2 ON p.client_id = u2.id
            WHERE p.product_owner_id = $1 OR p.client_id = $1 OR $1 IS NULL
            ORDER BY p.created_at DESC;
            """,
            user_id
        )

        if not rows:
            rows = await connection.fetch(
                """
                SELECT p.id, p.name, p.description, p.product_owner_id, p.client_id, p.created_at,
                       COALESCE(u1.name, 'Product Owner') AS product_owner_name,
                       COALESCE(u2.name, 'Client') AS client_name
                FROM projects p
                LEFT JOIN users u1 ON p.product_owner_id = u1.id
                LEFT JOIN users u2 ON p.client_id = u2.id
                ORDER BY p.created_at DESC;
                """
            )

        projects = []
        for row in rows:
            projects.append({
                "id": str(row["id"]),
                "name": row["name"],
                "description": row["description"],
                "product_owner_id": str(row["product_owner_id"]) if row["product_owner_id"] else None,
                "client_id": str(row["client_id"]) if row["client_id"] else None,
                "product_owner_name": row["product_owner_name"],
                "client_name": row["client_name"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            })

        try:
            job_rows = await connection.fetch(
                """
                SELECT id, project_name, status, current_stage, created_at
                FROM jobs
                ORDER BY created_at DESC;
                """
            )
            for j in job_rows:
                projects.append({
                    "id": str(j["id"]),
                    "name": j["project_name"],
                    "description": f"Pipeline Run ({j['status'].upper()}) - Stage: {j['current_stage'] or 'N/A'}",
                    "product_owner_name": "Multi-Agent System",
                    "client_name": "SDLC Pipeline",
                    "status": j["status"],
                    "is_job": True,
                    "created_at": j["created_at"].isoformat() if j["created_at"] else None
                })
        except Exception:
            pass

        return projects