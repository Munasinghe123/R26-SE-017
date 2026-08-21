
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

            # 2. Make sure the selected client exists
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
            product_owner = await connection.fetchrow(
                        """
                        UPDATE users
                        SET role = 'PRODUCT_OWNER'
                        WHERE id = $1
                        RETURNING id, name, email, role;
                        """,
                        creator_id
                    )

            # 4. Change selected user → CLIENT
            client_user = await connection.fetchrow(
                        """
                        UPDATE users
                        SET role = 'CLIENT'
                        WHERE id = $1
                        RETURNING id, name, email, role;
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
    print("PRODUCT OWNER:", dict(product_owner))
    print("CLIENT:", dict(client_user))
    print("PROJECT:", dict(project))

    return {
    "message": "Project created successfully",

    "product_owner": {
        "id": str(product_owner["id"]),
        "name": product_owner["name"],
        "email": product_owner["email"],
        "role": product_owner["role"],
    },

    "client": {
        "id": str(client_user["id"]),
        "name": client_user["name"],
        "email": client_user["email"],
        "role": client_user["role"],
    },

    "project": {
        "id": str(project["id"]),
        "name": project["name"],
        "description": project["description"],
        "product_owner_id": str(project["product_owner_id"]),
        "client_id": str(project["client_id"]),
        "created_at": project["created_at"],
    },
}
    

async def get_user_projects_service(user_id):

    async with db.pool.acquire() as connection:

        user = await connection.fetchrow(
            """
            SELECT id, role
            FROM users
            WHERE id = $1;
            """,
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if user["role"] == "PRODUCT_OWNER":

            projects = await connection.fetch(
                """
                SELECT
                    id,
                    name,
                    description,
                    product_owner_id,
                    client_id,
                    created_at
                FROM projects
                WHERE product_owner_id = $1
                ORDER BY created_at DESC;
                """,
                user_id
            )

        elif user["role"] == "CLIENT":

            projects = await connection.fetch(
                """
                SELECT
                    id,
                    name,
                    description,
                    product_owner_id,
                    client_id,
                    created_at
                FROM projects
                WHERE client_id = $1
                ORDER BY created_at DESC;
                """,
                user_id
            )

        else:
            projects = []

    return {
        "role": user["role"],
        "projects": [
            {
                "id": str(project["id"]),
                "name": project["name"],
                "description": project["description"],
                "product_owner_id": str(project["product_owner_id"]),
                "client_id": str(project["client_id"]),
                "created_at": project["created_at"],
            }
            for project in projects
        ]
    }