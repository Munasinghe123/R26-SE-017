from langgraph.types import Command

from graph.instance import graph

async def approve_endpoint(req):
    result = graph.invoke(
        Command(resume={"status": "approved", "feedback": None}),
        config={"configurable": {"thread_id": req.meeting_id}}
    )

    return {
        "status": "approved",
        "pdf_path": result.get("pdf_path")
    }