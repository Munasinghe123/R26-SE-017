
from graph.workflow import build_graph

graph = build_graph()


async def approve_endpoint(req):

    result = graph.invoke({
        "mode": "approved",
        "approval_status": "approved",
        "meeting_id": req.meeting_id
    })

    return {
        "status": "approved",
        "pdf_path": result["pdf_path"]
    }


