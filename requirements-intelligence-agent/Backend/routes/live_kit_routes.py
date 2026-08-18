
from fastapi import APIRouter
from services.live_kit import create_participant_token
import os
import uuid

live_kit_routes = APIRouter()

@live_kit_routes.get("/test/livekit-token")
async def test_livekit_token():

    token = create_participant_token(
        identity="user"+ str(uuid.uuid4()),
        name="Test User",
        room_name="test-room",
    )

    return {
        "token": token,
        "room_name": "test-room",
        "server_url": os.environ["LIVEKIT_URL"],
    }