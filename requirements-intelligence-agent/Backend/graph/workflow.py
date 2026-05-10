from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import (
    transcribe_node,
    diarization_node,
    extraction_node,
    refine_node,
    generate_srs_node,
    generate_srs_pdf_node,
    document_node
)
from graph.router import route_workflow


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("router", lambda state: state)
    builder.add_node("transcribe", transcribe_node)
    builder.add_node("document", document_node)
    builder.add_node("diarize", diarization_node)
    builder.add_node("extract", extraction_node)
    builder.add_node("refine", refine_node)
    builder.add_node("srs", generate_srs_node)
    builder.add_node("generate_pdf", generate_srs_pdf_node)
    
    builder.set_entry_point("router")
    
    builder.add_conditional_edges(
        "router",
        route_workflow
    )
    
    #audio extraction
    builder.add_edge("transcribe", "diarize")
    builder.add_edge("diarize", "extract")
    # builder.add_edge("extract", END)
    
    #document extraction
    builder.add_edge("document", "extract")
    
    builder.add_edge("extract", END)
    
    # refine
    builder.add_edge("refine", END)
    
    #srs
    builder.add_edge("srs", "generate_pdf")
    builder.add_edge("generate_pdf", END)
    
    return builder.compile()
    
    
    
    
    
    
    