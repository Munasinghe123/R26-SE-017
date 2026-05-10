
from graph.state import GraphState
from langgraph.graph import StateGraph, END 

def route_workflow(state):
    
    if state["mode"] == "extract":
        return "transcribe"
    
    if state["mode"] == "document_extract":
        return "document"
    
    if state["mode"] == "refine":
        return "refine"
    
    if state["mode"] == "approved":
        return "srs"
    