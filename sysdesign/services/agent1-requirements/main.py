from fastapi import FastAPI, UploadFile, File, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from contracts.v1 import RequirementsPackage
from contracts.adapters.req_to_hld import adapt as req_to_hld_adapt


# Core DB config — always needed
try:
    from db.config import connect_db, close_db
    DB_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] DB config failed to load: {e}")
    DB_AVAILABLE = False

# Auth routes — always try to load (depends only on pwdlib, jose)
try:
    from routes.auth.auth_routes import auth_routes
    AUTH_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] auth_routes failed to load: {e}")
    AUTH_AVAILABLE = False

# Search & project routes — always try to load (DB only)
try:
    from routes.search_routes import user_routes
    from routes.project_routes import project_routes
    SEARCH_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] search/project routes failed to load: {e}")
    SEARCH_AVAILABLE = False

# Approve routes — no heavy deps
try:
    from routes.approve_routes import approve_routes
    APPROVE_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] approve_routes failed to load: {e}")
    APPROVE_AVAILABLE = False

# AI-heavy routes — require langgraph
try:
    from routes.input_routes import router
    from routes.refine_routes import refine_routes
    AI_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] AI routes (input/refine) failed to load: {e}")
    AI_AVAILABLE = False

# LiveKit routes — require livekit-api
try:
    from routes.live_kit_routes import live_kit_routes
    LIVEKIT_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] live_kit_routes failed to load: {e}")
    LIVEKIT_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    if DB_AVAILABLE:
        try:
            await connect_db()
        except Exception:
            pass
    yield
    if DB_AVAILABLE:
        try:
            await close_db()
        except Exception:
            pass


app = FastAPI(title="Requirements Intelligence Agent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if AUTH_AVAILABLE:
    app.include_router(auth_routes)

if SEARCH_AVAILABLE:
    app.include_router(user_routes)
    app.include_router(project_routes)

if APPROVE_AVAILABLE:
    app.include_router(approve_routes)

if AI_AVAILABLE:
    app.include_router(router)
    app.include_router(refine_routes)

if LIVEKIT_AVAILABLE:
    app.include_router(live_kit_routes)



@app.get("/health")
async def health():
    return {"ok": True, "agent": "requirements", "schema": "1.0"}


@app.post("/run", response_model=RequirementsPackage)
async def run(payload: Dict[str, Any]) -> RequirementsPackage:
    """
    Standard inter-agent endpoint. Accepts requirements dict or raw input
    and returns validated RequirementsPackage.
    """
    try:
        req_package = req_to_hld_adapt(payload)
        return req_package
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse requirements: {str(e)}")
