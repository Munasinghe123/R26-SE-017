from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from pydantic import BaseModel
import db.config as db

from graph.instance import graph


qa_routes = APIRouter(
    prefix="/meetings",
    tags=["Meeting Questions"]
)


class ClientQuestionAnswer(BaseModel):
    question_id: str
    requirement_id: str
    answer: str


class ClientAnswersRequest(BaseModel):
    answers: list[ClientQuestionAnswer]


from services.meetings_service import get_meeting_requirements
from services.HITL.client_view import build_client_view


async def get_or_hydrate_qa_snapshot(thread_id: str):
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


# ============================================================
# GET QUESTIONS
# ============================================================

@qa_routes.get("/{thread_id}/questions")
async def get_questions(thread_id: str):

    snapshot, config = await get_or_hydrate_qa_snapshot(thread_id)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Meeting workflow not found"
        )

    clarification_questions = snapshot.values.get(
        "clarification_questions"
    )

    if not clarification_questions:
        return {
            "thread_id": thread_id,
            "questions": []
        }

    return {
        "thread_id": thread_id,
        "questions": clarification_questions.get(
            "questions",
            []
        )
    }


# ============================================================
# SUBMIT ANSWERS
# ============================================================

@qa_routes.post("/{thread_id}/questions/answers")
async def submit_question_answers(
    thread_id: str,
    request: ClientAnswersRequest
):

    snapshot, config = await get_or_hydrate_qa_snapshot(thread_id)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Meeting workflow not found"
        )

    project_id = snapshot.values.get("project_id") or snapshot.values.get("meeting_id") or thread_id

    # Resume LangGraph.
    #
    # graph.invoke() returns only after the
    # workflow reaches its next interrupt/end.
    graph.invoke(
        Command(
            resume={
                "answers": [
                    answer.model_dump()
                    for answer in request.answers
                ]
            }
        ),
        config=config
    )

    # Mark this project's analysis as completed if DB pool is active.
    if getattr(db, "pool", None) and project_id:
        try:
            async with db.pool.acquire() as connection:
                await connection.execute(
                    """
                    UPDATE projects
                    SET analysis_status = 'completed'
                    WHERE id = $1
                    """,
                    project_id
                )
        except Exception as e:
            print(f"[qa_routes] Warning: Failed to update project analysis_status: {e}")

    return {
        "thread_id": thread_id,
        "project_id": str(project_id),
        "status": "completed"
    }