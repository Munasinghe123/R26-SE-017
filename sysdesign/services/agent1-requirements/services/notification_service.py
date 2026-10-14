import db.config as db
from uuid import UUID
from typing import Optional, Dict, Any, List


async def create_notification_service(
    user_id: UUID,
    title: str,
    message: str,
    project_id: Optional[UUID] = None,
    notification_type: str = "PROJECT_ASSIGNED"
) -> Dict[str, Any]:
    async with db.pool.acquire() as connection:
        row = await connection.fetchrow(
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
                $4,
                $5,
                FALSE,
                now()
            )
            RETURNING id, user_id, title, message, type, project_id, is_read, created_at;
            """,
            user_id,
            title,
            message,
            notification_type,
            project_id
        )

        return {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "title": row["title"],
            "message": row["message"],
            "type": row["type"],
            "project_id": str(row["project_id"]) if row["project_id"] else None,
            "is_read": row["is_read"],
            "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
        }


async def get_user_notifications_service(user_id: str) -> Dict[str, Any]:
    async with db.pool.acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT
                n.id,
                n.user_id,
                n.title,
                n.message,
                n.type,
                n.project_id,
                n.is_read,
                n.created_at,
                p.name AS project_name
            FROM notifications n
            LEFT JOIN projects p ON n.project_id = p.id
            WHERE n.user_id = $1::uuid
            ORDER BY n.created_at DESC
            LIMIT 50;
            """,
            user_id
        )

        unread_row = await connection.fetchrow(
            """
            SELECT COUNT(*) AS count
            FROM notifications
            WHERE user_id = $1::uuid AND is_read = FALSE;
            """,
            user_id
        )

        unread_count = unread_row["count"] if unread_row else 0

        notifications = [
            {
                "id": str(r["id"]),
                "user_id": str(r["user_id"]),
                "title": r["title"],
                "message": r["message"],
                "type": r["type"],
                "project_id": str(r["project_id"]) if r["project_id"] else None,
                "project_name": r["project_name"] or "",
                "is_read": r["is_read"],
                "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
            }
            for r in rows
        ]

        return {
            "notifications": notifications,
            "unread_count": unread_count
        }


async def mark_notification_read_service(notification_id: str) -> Dict[str, Any]:
    async with db.pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = $1::uuid;
            """,
            notification_id
        )

        return {"message": "Notification marked as read", "id": notification_id}


async def mark_all_read_service(user_id: str) -> Dict[str, Any]:
    async with db.pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE user_id = $1::uuid;
            """,
            user_id
        )

        return {"message": "All notifications marked as read"}


async def notify_product_owner_review_complete_service(project_id: str) -> Dict[str, Any]:
    if not project_id:
        return {"ok": False, "message": "Project ID is required"}

    import uuid
    try:
        p_uuid = uuid.UUID(str(project_id))
    except Exception:
        return {"ok": False, "message": "Invalid project UUID"}

    async with db.pool.acquire() as connection:
        project = await connection.fetchrow(
            """
            SELECT p.id, p.name, p.product_owner_id, p.client_id, u.name AS client_name
            FROM projects p
            LEFT JOIN users u ON p.client_id = u.id
            WHERE p.id = $1;
            """,
            p_uuid
        )

        if not project:
            return {"ok": False, "message": "Project not found"}

        product_owner_id = project["product_owner_id"]
        if not product_owner_id:
            return {"ok": False, "message": "No product owner assigned to project"}

        proj_name = project["name"] or "Project"

        # Check if an unread notification already exists for this PO & project
        existing = await connection.fetchrow(
            """
            SELECT id FROM notifications
            WHERE user_id = $1 AND project_id = $2 AND type = 'CLIENT_REVIEW_COMPLETED' AND is_read = FALSE;
            """,
            product_owner_id,
            p_uuid
        )

        # Mark any pending client review notifications as read now that client review is complete
        await connection.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE project_id = $1 AND type = 'REVIEW_REQUIREMENTS';
            """,
            p_uuid
        )

        # Ensure meeting status is updated to completed
        await connection.execute(
            """
            UPDATE meetings
            SET status = 'completed', updated_at = now()
            WHERE project_id = $1 OR id = $1;
            """,
            p_uuid
        )

        if existing:
            return {
                "ok": True,
                "message": "Notification already exists",
                "id": str(existing["id"]),
                "product_owner_id": str(product_owner_id)
            }

        row = await connection.fetchrow(
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
                'Client Review Completed',
                $2,
                'CLIENT_REVIEW_COMPLETED',
                $3,
                FALSE,
                now()
            )
            RETURNING id, user_id, title, message, type, project_id, is_read, created_at;
            """,
            product_owner_id,
            f"Client review done for '{proj_name}'. You may proceed.",
            p_uuid
        )

        return {
            "ok": True,
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "title": row["title"],
            "message": row["message"],
            "type": row["type"],
            "project_id": str(row["project_id"]),
        }
