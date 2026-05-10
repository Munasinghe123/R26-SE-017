from graph.workflow import build_graph
from services.meetings_service import save_refined_version

graph = build_graph()

async def refine_endpoint(req):
    
    print("returned requirements", req.requirements)
    print("returned feedback", req.feedback)
    
    result = graph.invoke({
        "mode": "refine",
        "requirements": req.requirements,
        "feedback": req.feedback,
        "approval_status": "rejected",
        "meeting_id": req.meetingId
    })
    
    save_refined_version(req.meetingId,result["requirements"],req.feedback)    

    return {
        "requirements": result["requirements"],
        "status": "refined"
    }