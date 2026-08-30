

def route_workflow(state):
    
    if state["mode"] == "audio_extract":
        return "transcribe"
    
    if state["mode"] == "document_extract":
        return "document"
    
def route_after_client(state):
    
    print("Approval:", state["approval_status"])
    
    if state["approval_status"] == "approved":
        return "srs"
    return "refine"

