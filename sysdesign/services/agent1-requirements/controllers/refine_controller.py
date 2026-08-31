from langgraph.types import Command
from starlette.concurrency import run_in_threadpool
from graph.instance import graph

async def refine_endpoint(req):
    cmd = Command(resume={"status": "rejected", "feedback": req.feedback})
    config = {"configurable": {"thread_id": req.meetingId}}

    result = await run_in_threadpool(graph.invoke, cmd, config)

    try:
        from services.meetings_service import save_meeting_requirements
        reqs = result.get("requirements") if isinstance(result, dict) else None
        if not reqs:
            state = graph.get_state(config)
            if state and state.values:
                reqs = state.values.get("requirements")
        cview = result.get("client_view") if isinstance(result, dict) else None
        if not cview:
            state = graph.get_state(config)
            if state and state.values:
                cview = state.values.get("client_view")
        iter_count = (result.get("iteration_count") if isinstance(result, dict) else None) or 1
        await save_meeting_requirements(req.meetingId, reqs, client_view=cview, version=iter_count + 1)
    except Exception as exc:
        print(f"Warning: could not persist refined requirements: {exc}")

    return {
        "requirements": result.get("requirements", {}),
        "client_view": result.get("client_view", {}),
        "status": "refined"
    }