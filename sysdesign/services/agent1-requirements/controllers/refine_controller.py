from langgraph.types import Command
from starlette.concurrency import run_in_threadpool
from graph.instance import graph

async def refine_endpoint(req):
    cmd = Command(resume={"status": "rejected", "feedback": req.feedback})
    config = {"configurable": {"thread_id": req.meetingId}}

    result = await run_in_threadpool(graph.invoke, cmd, config)

    try:
        from services.meetings_service import save_refined_version
        save_refined_version(req.meetingId, result["requirements"], req.feedback)
    except Exception:
        pass

    return {
        "requirements": result.get("requirements", {}),
        "status": "refined"
    }