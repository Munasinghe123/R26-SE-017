

def route_workflow(state):
    
    if state["mode"] == "audio_extract":
        return "transcribe"
    
    if state["mode"] == "document_extract":
        return "document"
    
    

