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


def upload_png_to_cloudinary(
    png_bytes: bytes,
    project_id: int | str | None,
    diagram_type: str,
    public_id: str | None = None,
) -> str:
    if not png_bytes:
        raise ValueError("PNG bytes are empty; Cloudinary upload aborted.")

    folder = f"LLD-Agent/project_{project_id}/{diagram_type.lower()}" if project_id is not None else f"LLD-Agent/{diagram_type.lower()}"
    resolved_public_id = public_id or _safe_public_id(project_id, diagram_type)

    logger.info(
        "cloudinary_upload_started",
        extra={
            "diagram_type": diagram_type,
            "project_id": project_id,
            "folder": folder,
        },
    )

    try:
        result = cloudinary.uploader.upload(
            png_bytes,
            folder=folder,
            public_id=resolved_public_id,
            resource_type="image",
            overwrite=False,
        )
    except Exception as exc:  # pragma: no cover - network/service failure path
        logger.exception("cloudinary_upload_failed", extra={"diagram_type": diagram_type, "project_id": project_id})
        raise RuntimeError(f"Cloudinary upload failed for {diagram_type} diagram.") from exc

    secure_url = result.get("secure_url")
    if not secure_url:
        logger.error("cloudinary_upload_missing_secure_url", extra={"diagram_type": diagram_type, "project_id": project_id})
        raise RuntimeError(f"Cloudinary upload for {diagram_type} diagram did not return a secure URL.")

    logger.info(
        "cloudinary_upload_successful",
        extra={
            "diagram_type": diagram_type,
            "project_id": project_id,
            "secure_url": secure_url,
        },
    )
    return secure_url
