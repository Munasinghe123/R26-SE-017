import asyncio
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from services.notification_service import (
    get_user_notifications_service,
    mark_notification_read_service,
    mark_all_read_service,
    create_notification_service,
    notify_product_owner_review_complete_service,
    register_connection,
    unregister_connection,
)

notification_routes = APIRouter()


class CreateNotificationRequest(BaseModel):
    user_id: UUID
    title: str
    message: str
    project_id: Optional[UUID] = None
    type: Optional[str] = "PROJECT_ASSIGNED"


@notification_routes.get("/notifications/user/{user_id}")
async def get_user_notifications(user_id: str):
    try:
        return await get_user_notifications_service(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@notification_routes.patch("/notifications/{notification_id}/read")
@notification_routes.post("/notifications/{notification_id}/read")
@notification_routes.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    try:
        return await mark_notification_read_service(notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@notification_routes.post("/notifications/user/{user_id}/read-all")
async def mark_all_read(user_id: str):
    try:
        return await mark_all_read_service(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@notification_routes.post("/notifications", status_code=201)
async def create_notification(data: CreateNotificationRequest):
    try:
        return await create_notification_service(
            user_id=data.user_id,
            title=data.title,
            message=data.message,
            project_id=data.project_id,
            notification_type=data.type or "PROJECT_ASSIGNED",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@notification_routes.post("/notifications/project/{project_id}/client-reviewed")
async def notify_client_reviewed(project_id: str):
    try:
        return await notify_product_owner_review_complete_service(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@notification_routes.get("/notifications/stream/{user_id}")
async def stream_notifications(user_id: str, request: Request):
    queue = await register_connection(user_id)

    async def event_generator():
        try:
            # 1. Immediately send current snapshot so client has latest data upon connecting
            initial_data = await get_user_notifications_service(user_id)
            yield f"event: init\ndata: {json.dumps(initial_data)}\n\n"

            # 2. Wait for live notifications or send 20s keepalive pings
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield f"event: notification\ndata: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive comment to prevent socket timeout in proxies/browsers
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await unregister_connection(user_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


