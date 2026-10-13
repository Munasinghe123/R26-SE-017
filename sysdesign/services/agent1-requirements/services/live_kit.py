import os
import json
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

# Load .env looking upwards
_base = Path(__file__).resolve()
for parent in [_base.parent, _base.parents[1], _base.parents[2], _base.parents[3]]:
    env_file = parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
load_dotenv()


def create_participant_token(
    identity: str,
    room_name: str,
    name: str,
    metadata: dict = None,
) -> str:
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("LIVEKIT_API_KEY or LIVEKIT_API_SECRET environment variables are missing.")

    token = (
        api.AccessToken(
            api_key,
            api_secret,
        )
        .with_identity(identity)
        .with_name(name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
    )

    if metadata:
        meta_str = json.dumps(metadata) if isinstance(metadata, dict) else str(metadata)
        token = token.with_metadata(meta_str)

    return token.to_jwt()