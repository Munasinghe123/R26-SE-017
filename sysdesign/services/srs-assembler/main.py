import os
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env looking upwards from this file's folder to sysdesign and workspace root
_base = Path(__file__).resolve()
for parent in [_base.parent, _base.parents[1], _base.parents[2]]:
    env_file = parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
load_dotenv()

from services.srs_service import SRSService
from utils.logger import log_startup

app = FastAPI(title="SRS Assembler Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

srs_service = SRSService()


@app.on_event("startup")
def on_startup():
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")
    log_startup(port=8005, model=model)


@app.get("/health")
def health():
    return srs_service.get_health_status()


@app.post("/run")
async def run(payload: Dict[str, Any]):
    return await srs_service.process_assembly_request(payload)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=False)

