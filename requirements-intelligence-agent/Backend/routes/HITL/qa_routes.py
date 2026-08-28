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


# ============================================================
# GET QUESTIONS
# ============================================================

@qa_routes.get("/{thread_id}/questions")
async def get_questions(thread_id: str):

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

    project_id = snapshot.values.get("project_id")

    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Project ID not found in workflow"
        )

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

    # Mark this project's analysis as completed.
    async with db.pool.acquire() as connection:

        await connection.execute(
            """
            UPDATE projects
            SET analysis_status = 'completed'
            WHERE id = $1
            """,
            project_id
        )

    return {
        "thread_id": thread_id,
        "project_id": str(project_id),
        "status": "completed"
    }