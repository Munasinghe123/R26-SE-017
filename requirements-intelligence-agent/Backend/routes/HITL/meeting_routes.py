from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from pydantic import BaseModel
from typing import Literal, Optional

from graph.instance import graph

meeting_routes = APIRouter(
    prefix="/meetings",
    tags=["Meetings"]
)


class ClientRequirementReview(BaseModel):
    id: str
    action: Literal["keep", "edit", "delete","add"]
    text: Optional[str] = None


class ClientReviewRequest(BaseModel):
    items: list[ClientRequirementReview]


@meeting_routes.get("/{thread_id}/review")
async def get_meeting_review(thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    snapshot = graph.get_state(config)

    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Meeting workflow not found"
        )

    return {
        "thread_id": thread_id,
        "project_id": snapshot.values.get("project_id"),
        "client_view": snapshot.values.get("client_view"),
    }


@meeting_routes.post("/{thread_id}/review")
async def submit_meeting_review(
    thread_id: str,
    review: ClientReviewRequest
):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    snapshot = graph.get_state(config)

    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Meeting workflow not found"
        )

    result = graph.invoke(
        Command(
            resume={
                "status": "submitted",
                "items": [
                    item.model_dump()
                    for item in review.items
                ]
            }
        ),
        config=config
    )

    return {
        "thread_id": thread_id,
        "status": "submitted"
    }