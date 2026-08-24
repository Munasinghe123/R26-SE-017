from langgraph.types import Command
# from services.meetings_service import save_refined_version

from graph.instance import graph

async def refine_endpoint(req):
    result = graph.invoke(
        Command(resume={"status": "rejected", "feedback": req.feedback}),
        config={"configurable": {"thread_id": req.meetingId}}
    )

    # save_refined_version(req.meetingId, result["requirements"], req.feedback)

    return {
        "requirements": result["requirements"],
        "status": "refined"
    }