from __future__ import annotations

import logging
import os
import re
from typing import Optional
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# Ensure local .env is loaded
load_dotenv()

logger = logging.getLogger("srs-assembler.cloudinary")


def get_cloudinary_config() -> tuple[str, str, str, str]:
    """
    Retrieves isolated Cloudinary credentials for SRS Assembler.
    Defaults folder to 'SRS_Documents'.
    """
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
    folder = os.getenv("CLOUDINARY_SRS_FOLDER", "SRS_Documents").strip()

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
    return cloud_name, api_key, api_secret, folder


def is_cloudinary_configured() -> bool:
    """Returns True if Cloudinary credentials are fully provided."""
    cloud_name, api_key, api_secret, _ = get_cloudinary_config()
    return bool(cloud_name and api_key and api_secret)


def upload_srs_pdf_to_cloudinary(
    pdf_bytes: bytes,
    job_id: str,
    project_name: str = "Software System",
) -> Optional[str]:
    """
    Uploads the compiled SRS PDF bytes directly to Cloudinary CDN storage as a raw PDF document.
    Returns the permanent secure HTTPS URL or None if upload fails.
    """
    if not pdf_bytes:
        logger.warning("[Cloudinary] No PDF bytes provided for upload.")
        return None

    cloud_name, api_key, api_secret, folder = get_cloudinary_config()
    if not (cloud_name and api_key and api_secret):
        logger.warning("[Cloudinary] Credentials not configured. Skipping cloud upload.")
        return None

    safe_job_id = re.sub(r"[^\w\-]", "_", job_id)
    public_id = f"SRS_{safe_job_id}.pdf"

    try:
        logger.info(f"[Cloudinary] Uploading SRS PDF for job '{job_id}' to folder '{folder}'...")
        result = cloudinary.uploader.upload(
            pdf_bytes,
            folder=folder,
            public_id=public_id,
            resource_type="raw",
            overwrite=True,
        )
        secure_url = result.get("secure_url")
        if secure_url:
            logger.info(f"[Cloudinary] Successfully uploaded SRS PDF: {secure_url}")
            return secure_url
        logger.warning("[Cloudinary] Upload succeeded but secure_url was missing in response.")
        return None
    except Exception as exc:
        logger.error(f"[Cloudinary] Failed to upload SRS PDF: {exc}")
        return None
