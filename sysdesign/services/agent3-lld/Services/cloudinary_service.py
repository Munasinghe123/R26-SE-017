import logging
import os

from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def _safe_public_id(project_id: int | str | None, diagram_type: str, suffix: str | None = None) -> str:
    project_segment = f"project_{project_id}" if project_id is not None else "project_unknown"
    diagram_name = (diagram_type or "diagram").strip().lower()
    safe_suffix = "" if not suffix else f"_{suffix.strip().lower()}"
    return f"{diagram_name}{safe_suffix}_{project_segment}"


import base64

def upload_png_to_cloudinary(
    png_bytes: bytes,
    project_id: int | str | None,
    diagram_type: str,
    public_id: str | None = None,
) -> str:
    if not png_bytes:
        return ""

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    api_key = os.getenv("CLOUDINARY_API_KEY", "")
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "")
    base_folder = os.getenv("CLOUDINARY_FOLDER", "LLD")

    # If Cloudinary credentials are not set, return base64 data URL directly
    if not cloud_name or not api_key or not api_secret:
        b64_str = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64_str}"

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )

    folder = f"{base_folder}/{diagram_type.lower()}"
    resolved_public_id = public_id or _safe_public_id(project_id, diagram_type)

    logger.info(
        "cloudinary_upload_started",
        extra={
            "diagram_type": diagram_type,
            "project_id": project_id,
            "folder": folder,
            "public_id": resolved_public_id,
        },
    )

    try:
        result = cloudinary.uploader.upload(
            png_bytes,
            folder=folder,
            public_id=resolved_public_id,
            resource_type="image",
            overwrite=True,
        )
        secure_url = result.get("secure_url")
        if secure_url:
            return secure_url
    except Exception as exc:
        logger.warning(f"Cloudinary upload failed ({exc}), falling back to base64 data URL")

    b64_str = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

