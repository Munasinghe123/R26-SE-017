
from fastapi import APIRouter, Depends
from services.auth.auth_service import register_ba
from services.auth.auth_service import login_user
from pydantic import BaseModel

auth_routes = APIRouter()

class BARegisterRequest(BaseModel):
    email: str
    name: str
    password: str

@auth_routes.post("/register")
async def register_ba_route(data: BARegisterRequest):
    return await register_ba(
        data.email,
        data.name,
        data.password
    )
    
    
class LoginRequest(BaseModel):
    email: str
    password: str

@auth_routes.post("/login")
async def login_route(data: LoginRequest):
    return await login_user(
        data.email,
        data.password
    )
