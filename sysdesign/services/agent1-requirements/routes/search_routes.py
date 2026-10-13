

from typing import Optional
from fastapi import APIRouter
from services.search_user import search_users_service

user_routes = APIRouter()

@user_routes.get("/users/search")
async def search_users(q: Optional[str] = ""):
    return await search_users_service(q or "")