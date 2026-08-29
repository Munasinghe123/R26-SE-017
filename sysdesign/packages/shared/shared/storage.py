"""
shared.storage — Artifact storage abstraction.

Dev: writes files to ARTIFACT_ROOT (D:/AgentOutputs)
Prod: uploads to Cloudflare R2 or Cloudinary (set STORAGE_BACKEND)

Usage:
    from shared.storage import save_artifact

    uri = await save_artifact(
        job_id="abc123",
        stage="lld",
        kind="class_diagram",
        filename="class.png",
        content=png_bytes,
        mime_type="image/png",
    )
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv

_here = os.path.dirname(__file__)
_root = os.path.abspath(os.path.join(_here, "..", ".."))
load_dotenv(os.path.join(_root, ".env"))

logger = logging.getLogger("shared.storage")

ARTIFACT_ROOT = Path(os.getenv("ARTIFACT_ROOT", "D:/AgentOutputs"))
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")


async def save_artifact(
    job_id: str,
    stage: str,
    kind: str,
    filename: str,
    content: Union[bytes, str],
    mime_type: str = "application/octet-stream",
) -> str:
    """
    Save an artifact and return its URI.
    In dev: returns a local file:// path.
    In prod: returns a https:// URL (R2 or Cloudinary).
    """
    if STORAGE_BACKEND == "local":
        return await _save_local(job_id, stage, kind, filename, content)
    elif STORAGE_BACKEND == "r2":
        return await _save_r2(job_id, stage, kind, filename, content, mime_type)
    else:
        raise ValueError(f"Unknown STORAGE_BACKEND: {STORAGE_BACKEND}")


async def _save_local(
    job_id: str,
    stage: str,
    kind: str,
    filename: str,
    content: Union[bytes, str],
) -> str:
    """Write file to ARTIFACT_ROOT/{stage}/{job_id}/{filename}."""
    dest_dir = ARTIFACT_ROOT / stage / job_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    if isinstance(content, str):
        dest.write_text(content, encoding="utf-8")
    else:
        dest.write_bytes(content)

    # Normalise path separators for cross-platform display
    uri = dest.as_posix()
    logger.info(f"[storage] Saved {stage}/{kind}: {uri}")
    return uri


async def _save_r2(
    job_id: str,
    stage: str,
    kind: str,
    filename: str,
    content: Union[bytes, str],
    mime_type: str,
) -> str:
    """Upload to Cloudflare R2 and return the public URL."""
    import boto3  # type: ignore  # pip install boto3

    account_id = os.getenv("R2_ACCOUNT_ID", "")
    access_key = os.getenv("R2_ACCESS_KEY_ID", "")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")
    bucket = os.getenv("R2_BUCKET", "sdlc-artifacts")
    public_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")

    client = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    key = f"{job_id}/{stage}/{filename}"
    body = content.encode() if isinstance(content, str) else content
    client.put_object(Bucket=bucket, Key=key, Body=body, ContentType=mime_type)

    return f"{public_url}/{key}" if public_url else f"r2://{bucket}/{key}"


def local_path(job_id: str, stage: str, filename: str) -> Path:
    """Return the expected local path for a saved artifact."""
    return ARTIFACT_ROOT / stage / job_id / filename
