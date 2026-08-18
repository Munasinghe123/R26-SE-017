
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