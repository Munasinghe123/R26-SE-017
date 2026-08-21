

import db.config as db


async def search_users_service(query: str):

    query = query.strip()

    if len(query) < 2:
        return []

    search_query = """
        SELECT
            id,
            name,
            email
        FROM users
        WHERE role IN ( 'USER' ,'CLIENT')
          AND (
              name ILIKE '%' || $1 || '%'
              OR email ILIKE '%' || $1 || '%'
          )
        ORDER BY name
        LIMIT 10;
    """

    async with db.pool.acquire() as connection:
        users = await connection.fetch(search_query, query)

    return [
        {
            "id": str(user["id"]),
            "name": user["name"],
            "email": user["email"],
        }
        for user in users
    ]