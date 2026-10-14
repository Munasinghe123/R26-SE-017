
import db.config as db
from fastapi import HTTPException


async def create_project_service(creator_id, data):

    async with db.pool.acquire() as connection:

        async with connection.transaction():

            # 1. Make sure the creator exists and is a USER
            creator = await connection.fetchrow(
                """
                SELECT id, name, role
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
                SELECT id, name, role
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

            # 6. Initialize meeting invitation record in meetings table
            await connection.execute(
                """
                INSERT INTO meetings (
                    id,
                    project_id,
                    status,
                    version,
                    created_at,
                    updated_at
                )
                VALUES ($1, $1, 'invited', 1, now(), now())
                ON CONFLICT (id) DO NOTHING;
                """,
                project["id"]
            )

            # 7. Create in-app notification for the client
            po_name = creator["name"] if (creator and "name" in creator and creator["name"]) else "Product Owner"
            notif_row = await connection.fetchrow(
                """
                INSERT INTO notifications (
                    id,
                    user_id,
                    title,
                    message,
                    type,
                    project_id,
                    is_read,
                    created_at
                )
                VALUES (
                    gen_random_uuid(),
                    $1,
                    $2,
                    $3,
                    'PROJECT_ASSIGNED',
                    $4,
                    FALSE,
                    now()
                )
                RETURNING id, user_id, title, message, type, project_id, is_read, created_at;
                """,
                data.clientId,
                "New Project Assigned",
                f"You have been added to project '{project['name']}' by {po_name}.",
                project["id"]
            )
            try:
                from services.notification_service import push_notification_to_user
                await push_notification_to_user(str(data.clientId), notif_row)
            except Exception as e:
                pass

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


# async def get_projects_by_user_service(user_id):
#     async with db.pool.acquire() as connection:
#         rows = await connection.fetch(
#             """
#             SELECT p.id, p.name, p.description, p.product_owner_id, p.client_id, p.created_at,
#                    COALESCE(u1.name, 'Product Owner') AS product_owner_name,
#                    COALESCE(u2.name, 'Client') AS client_name,
#                    (SELECT id FROM meetings WHERE project_id = p.id ORDER BY updated_at DESC LIMIT 1) AS latest_meeting_id
#             FROM projects p
#             LEFT JOIN users u1 ON p.product_owner_id = u1.id
#             LEFT JOIN users u2 ON p.client_id = u2.id
#             WHERE p.product_owner_id = $1 OR p.client_id = $1 OR $1 IS NULL
#             ORDER BY p.created_at DESC;
#             """,
#             user_id
#         )

#         if not rows:
#             rows = await connection.fetch(
#                 """
#                 SELECT p.id, p.name, p.description, p.product_owner_id, p.client_id, p.created_at,
#                        COALESCE(u1.name, 'Product Owner') AS product_owner_name,
#                        COALESCE(u2.name, 'Client') AS client_name,
#                        (SELECT id FROM meetings WHERE project_id = p.id ORDER BY updated_at DESC LIMIT 1) AS latest_meeting_id
#                 FROM projects p
#                 LEFT JOIN users u1 ON p.product_owner_id = u1.id
#                 LEFT JOIN users u2 ON p.client_id = u2.id
#                 ORDER BY p.created_at DESC;
#                 """
#             )

#         projects = []
#         for row in rows:
#             projects.append({
#                 "id": str(row["id"]),
#                 "name": row["name"],
#                 "description": row["description"],
#                 "product_owner_id": str(row["product_owner_id"]) if row["product_owner_id"] else None,
#                 "client_id": str(row["client_id"]) if row["client_id"] else None,
#                 "product_owner_name": row["product_owner_name"],
#                 "client_name": row["client_name"],
#                 "latest_meeting_id": str(row["latest_meeting_id"]) if row.get("latest_meeting_id") else None,
#                 "created_at": row["created_at"].isoformat() if row["created_at"] else None
#             })

#         try:
#             job_rows = await connection.fetch(
#                 """
#                 SELECT id, project_name, status, current_stage, created_at
#                 FROM jobs
#                 ORDER BY created_at DESC;
#                 """
#             )
#             for j in job_rows:
#                 projects.append({
#                     "id": str(j["id"]),
#                     "name": j["project_name"],
#                     "description": f"Pipeline Run ({j['status'].upper()}) - Stage: {j['current_stage'] or 'N/A'}",
#                     "product_owner_name": "Multi-Agent System",
#                     "client_name": "SDLC Pipeline",
#                     "status": j["status"],
#                     "is_job": True,
#                     "created_at": j["created_at"].isoformat() if j["created_at"] else None
#                 })
#         except Exception:
#             pass

#         return projects

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

        effective_role = user["role"]

        if user["role"] == "PRODUCT_OWNER":

            projects = await connection.fetch(
                """
                SELECT
                    p.id,
                    p.name,
                    p.description,
                    p.product_owner_id,
                    p.client_id,
                    p.created_at,
                    COALESCE(c.name, 'Client Partner') AS client_name,
                    COALESCE(c.email, '') AS client_email,
                    m.id AS meeting_id,
                    m.status AS meeting_status,
                    m.input_method AS input_method
                FROM projects p
                LEFT JOIN users c ON p.client_id = c.id
                LEFT JOIN LATERAL (
                    SELECT id, status, (requirements->>'input_method') AS input_method, updated_at
                    FROM meetings
                    WHERE project_id = p.id OR id = p.id
                    ORDER BY updated_at DESC
                    LIMIT 1
                ) m ON true
                WHERE p.product_owner_id = $1
                ORDER BY p.created_at DESC;
                """,
                user_id
            )

        else:
            # Query projects where the user is assigned as client
            projects = await connection.fetch(
                """
                SELECT
                    p.id,
                    p.name,
                    p.description,
                    p.product_owner_id,
                    p.client_id,
                    p.created_at,
                    COALESCE(po.name, 'Business Analyst') AS product_owner_name,
                    COALESCE(po.email, '') AS product_owner_email,
                    m.id AS meeting_id,
                    m.status AS meeting_status,
                    m.input_method AS input_method
                FROM projects p
                LEFT JOIN users po ON p.product_owner_id = po.id
                LEFT JOIN LATERAL (
                    SELECT id, status, (requirements->>'input_method') AS input_method, updated_at
                    FROM meetings
                    WHERE project_id = p.id OR id = p.id
                    ORDER BY updated_at DESC
                    LIMIT 1
                ) m ON true
                WHERE p.client_id = $1
                ORDER BY p.created_at DESC;
                """,
                user_id
            )

            # If user has client projects, ensure their role is CLIENT
            if len(projects) > 0:
                effective_role = "CLIENT"
                if user["role"] != "CLIENT":
                    await connection.execute(
                        "UPDATE users SET role = 'CLIENT' WHERE id = $1;",
                        user_id
                    )

        projects_data = []
        for p in projects:
            m_status = p.get("meeting_status")
            inp_method = p.get("input_method") or ("meeting" if m_status == "completed" else None)
            if m_status == "ready_for_review":
                analysis_status = "waiting"
            elif m_status == "completed":
                analysis_status = "completed"
            elif m_status == "invited":
                analysis_status = "invited"
            else:
                analysis_status = "invited" if effective_role == "CLIENT" else "idle"

            projects_data.append({
                "id": str(p["id"]),
                "name": p["name"],
                "description": p["description"],
                "product_owner_id": str(p["product_owner_id"]),
                "client_id": str(p["client_id"]),
                "product_owner_name": p.get("product_owner_name") or "Business Analyst",
                "product_owner_email": p.get("product_owner_email") or "",
                "client_name": p.get("client_name") or "Client Partner",
                "client_email": p.get("client_email") or "",
                "room_name": f"proj-{str(p['id'])[:8]}",
                "created_at": p["created_at"].isoformat() if hasattr(p["created_at"], "isoformat") else p["created_at"],
                "latest_meeting_id": str(p["meeting_id"]) if p.get("meeting_id") else str(p["id"]),
                "meeting_id": str(p["meeting_id"]) if p.get("meeting_id") else str(p["id"]),
                "meeting_status": m_status or ("invited" if effective_role == "CLIENT" else "idle"),
                "analysis_status": analysis_status,
                "status": analysis_status,
                "input_method": inp_method,
                "is_invited": True if effective_role == "CLIENT" else False,
            })

    return {
        "role": effective_role,
        "projects": projects_data
    }


async def assign_client_to_project_service(project_id: str, client_id: str, assigned_by_id: str = None):
    async with db.pool.acquire() as connection:
        async with connection.transaction():
            # Check project
            project = await connection.fetchrow(
                "SELECT id, name, product_owner_id FROM projects WHERE id = $1::uuid;",
                project_id
            )
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Check client user
            client = await connection.fetchrow(
                "SELECT id, name, role FROM users WHERE id = $1::uuid;",
                client_id
            )
            if not client:
                raise HTTPException(status_code=404, detail="Client user not found")

            # Update client role to CLIENT
            await connection.execute(
                "UPDATE users SET role = 'CLIENT' WHERE id = $1::uuid;",
                client_id
            )

            # Update project client_id
            await connection.execute(
                "UPDATE projects SET client_id = $1::uuid WHERE id = $2::uuid;",
                client_id,
                project_id
            )

            # Fetch assigner name
            assigner_name = "Product Owner"
            if assigned_by_id:
                assigner = await connection.fetchrow(
                    "SELECT name FROM users WHERE id = $1::uuid;",
                    assigned_by_id
                )
                if assigner and assigner.get("name"):
                    assigner_name = assigner["name"]

            # Create notification
            notif_row = await connection.fetchrow(
                """
                INSERT INTO notifications (
                    id, user_id, title, message, type, project_id, is_read, created_at
                )
                VALUES (gen_random_uuid(), $1::uuid, $2, $3, 'PROJECT_ASSIGNED', $4::uuid, FALSE, now())
                RETURNING id, user_id, title, message, type, project_id, is_read, created_at;
                """,
                client_id,
                "New Project Assigned",
                f"You have been added to project '{project['name']}' by {assigner_name}.",
                project["id"]
            )
            try:
                from services.notification_service import push_notification_to_user
                await push_notification_to_user(str(client_id), notif_row)
            except Exception as e:
                pass

            return {
                "message": "Client assigned successfully",
                "project_id": str(project["id"]),
                "client_id": str(client["id"])
            }