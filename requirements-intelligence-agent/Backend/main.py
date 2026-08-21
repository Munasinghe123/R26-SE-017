from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from routes.input_routes import router
from routes.refine_routes import refine_routes
from routes.approve_routes import approve_routes
from routes.live_kit_routes import live_kit_routes
from routes.auth.auth_routes import auth_routes
from routes.search_routes import user_routes
from routes.project_routes import project_routes
from db.config import connect_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs when the application starts
    await connect_db()

    yield

    # Runs when the application shuts down
    await close_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("requirements intelligence agent running")

app.include_router(router)
app.include_router(refine_routes)
app.include_router(approve_routes)
app.include_router(live_kit_routes)
app.include_router(auth_routes)
app.include_router(user_routes)
app.include_router(project_routes)
