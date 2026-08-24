
from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from pydantic import BaseModel
from typing import Literal, Optional

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
    

@qa_routes.post("/{meeting_id}/questions/answers")
async def submit_question_answers(
    meeting_id: str,
    request: ClientAnswersRequest
):

    config = {
        "configurable": {
            "thread_id": meeting_id
        }
    }

    snapshot = graph.get_state(config)

    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Meeting workflow not found"
        )

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

    return {
        "meeting_id": meeting_id,
        "status": "answers_submitted"
    }