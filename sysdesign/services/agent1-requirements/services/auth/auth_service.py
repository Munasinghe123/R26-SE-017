import os
import uuid
from datetime import datetime, timedelta, timezone

import db.config as db
from pwdlib import PasswordHash
from jose import jwt


password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


async def register_ba(
    email: str,
    name: str,
    password: str
):
    email = email.strip().lower()
    name = name.strip()

    # Basic validation
    if not email:
        raise ValueError("Email is required")

    if not name:
        raise ValueError("Name is required")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    # Hash password
    hashed_password = password_hash.hash(password)

    user_id = uuid.uuid4()

    query = """
        INSERT INTO users (
            id,
            name,
            email,
            password_hash,
            role
        )
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (email) DO NOTHING
        RETURNING id, name, email, role;
    """

    async with db.pool.acquire() as connection:
        user = await connection.fetchrow(
            query,
            user_id,
            name,
            email,
            hashed_password,
            "USER"
        )

    if user is None:
        raise ValueError("A user with this email already exists")

    return {
        "id": str(user["id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }
    
async def login_user(email: str, password: str):

    email = email.strip().lower()

    query = """
        SELECT id, name, email, password_hash, role
        FROM users
        WHERE email = $1
    """

    async with db.pool.acquire() as connection:
        user = await connection.fetchrow(query, email)

    if user is None:
        raise ValueError("Invalid email or password")

    if not password_hash.verify(password, user["password_hash"]):
        raise ValueError("Invalid email or password")

    return {
        "user": {
            "id": str(user["id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }