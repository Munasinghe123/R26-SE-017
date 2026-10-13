

import db.config as db


async def search_users_service(query: str = ""):
    query = (query or "").strip()

    async with db.pool.acquire() as connection:
        if not query:
            search_query = """
                SELECT
                    id,
                    name,
                    email,
                    role
                FROM users
                WHERE role IN ('USER', 'CLIENT')
                ORDER BY CASE WHEN role = 'CLIENT' THEN 0 ELSE 1 END, created_at DESC
                LIMIT 20;
            """
            users = await connection.fetch(search_query)
        else:
            search_query = """
                SELECT
                    id,
                    name,
                    email,
                    role
                FROM users
                WHERE role IN ('USER', 'CLIENT')
                  AND (
                      name ILIKE '%' || $1 || '%'
                      OR email ILIKE '%' || $1 || '%'
                  )
                ORDER BY CASE WHEN role = 'CLIENT' THEN 0 ELSE 1 END, name
                LIMIT 20;
            """
            users = await connection.fetch(search_query, query)

    return [
        {
            "id": str(user["id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        }
        for user in users
    ]