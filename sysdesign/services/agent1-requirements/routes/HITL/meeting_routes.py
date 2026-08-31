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
    action: Literal["keep", "edit", "delete", "add"]
    text: Optional[str] = None


class ClientReviewRequest(BaseModel):
    items: list[ClientRequirementReview]


from services.meetings_service import get_meeting_requirements
from services.HITL.client_view import build_client_view


async def get_or_hydrate_snapshot(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)

    if not snapshot or not snapshot.values:
        persisted = await get_meeting_requirements(thread_id)
        if persisted and persisted.get("requirements"):
            reqs = persisted.get("requirements")
            cview = persisted.get("client_view") or build_client_view(reqs)
            graph.update_state(
                config,
                {
                    "mode": "audio_extract",
                    "thread_id": thread_id,
                    "meeting_id": thread_id,
                    "project_id": persisted.get("project_id"),
                    "requirements": reqs,
                    "client_view": cview,
                },
                as_node="client_view"
            )
            snapshot = graph.get_state(config)

    return snapshot, config


@meeting_routes.get("/{thread_id}/review")
async def get_meeting_review(thread_id: str):

    snapshot, config = await get_or_hydrate_snapshot(thread_id)

    if not snapshot or not snapshot.values:
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

    snapshot, config = await get_or_hydrate_snapshot(thread_id)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Meeting workflow not found"
        )

    # Resume graph from await_client
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

    # Check updated state after executing up to next interrupt / end
    new_snapshot = graph.get_state(config)
    questions = []
    if new_snapshot and new_snapshot.values:
        clarification_q = new_snapshot.values.get("clarification_questions")
        if isinstance(clarification_q, dict):
            questions = clarification_q.get("questions", [])
        elif isinstance(clarification_q, list):
            questions = clarification_q

    return {
        "thread_id": thread_id,
        "status": "questions_ready" if questions else "completed",
        "questions": questions
    }


@meeting_routes.get("/{thread_id}/final-requirements")
async def get_final_requirements(thread_id: str):

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

    final_requirements = snapshot.values.get(
        "final_requirements"
    )

    if not final_requirements:
        return {
            "thread_id": thread_id,
            "ready": False,
            "final_requirements": None
        }

    return {
        "thread_id": thread_id,
        "ready": True,
        "final_requirements": final_requirements
    }
