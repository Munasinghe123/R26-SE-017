import logging
import os
import base64
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

logger = logging.getLogger(__name__)


def get_cloudinary_config():
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    api_key = os.getenv("CLOUDINARY_API_KEY", "")
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "")
    base_folder = os.getenv("CLOUDINARY_FOLDER", "UI")

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
    return cloud_name, api_key, api_secret, base_folder


def upload_html_to_cloudinary(html_content: str, project_id: str | int | None, screen_id: str) -> str:
    """
    Uploads raw HTML content or raw text to Cloudinary as raw file.
    Returns secure HTTPS Cloudinary URL.
    """
    if not html_content:
        return ""

    cloud_name, api_key, api_secret, base_folder = get_cloudinary_config()
    if not cloud_name or not api_key or not api_secret:
        return ""

    folder = f"{base_folder}/screens"
    public_id = f"{screen_id}_{project_id or 'sdlc'}"

    try:
        html_bytes = html_content.encode("utf-8")
        result = cloudinary.uploader.upload(
            html_bytes,
            folder=folder,
            public_id=public_id,
            resource_type="raw",
            overwrite=True,
        )
        return result.get("secure_url") or ""
    except Exception as exc:
        logger.warning(f"Cloudinary HTML upload error: {exc}")
        return ""


def upload_image_to_cloudinary(image_bytes: bytes, project_id: str | int | None, screen_id: str) -> str:
    """
    Uploads screenshot/render image to Cloudinary.
    """
    if not image_bytes:
        return ""

    cloud_name, api_key, api_secret, base_folder = get_cloudinary_config()
    if not cloud_name or not api_key or not api_secret:
        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64_str}"

    folder = f"{base_folder}/screenshots"
    public_id = f"screenshot_{screen_id}_{project_id or 'sdlc'}"

    try:
        result = cloudinary.uploader.upload(
            image_bytes,
            folder=folder,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
        )
        return result.get("secure_url") or ""
    except Exception as exc:
        logger.warning(f"Cloudinary image upload error: {exc}")
        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64_str}"
