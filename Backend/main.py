from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.audio_routes import router
from routes.refine_routes import refine_routes
from routes.approve_routes import approve_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("backend running")

app.include_router(router)
app.include_router(refine_routes)
app.include_router(approve_routes)