from datetime import datetime
from typing import Literal, List, Optional
from pydantic import BaseModel, Field


class StageResult(BaseModel):
    stage: Literal["requirements", "hld", "lld", "ui", "srs"]
    status: Literal["pending", "running", "complete", "failed", "skipped"]
    attempt: int = 1
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class JobState(BaseModel):
    job_id: str
    tenant_id: str = "dev"
    project_name: str
    status: Literal[
        "queued",
        "running",
        "needs_review",
        "waiting_for_hld",
        "waiting_for_lld_ui",
        "waiting_for_ui",
        "waiting_for_srs",
        "complete",
        "failed",
    ] | str = "running"
    current_stage: Optional[str] = None
    stages: List[StageResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
