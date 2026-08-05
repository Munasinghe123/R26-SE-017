from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import (
    transcribe_node,
    diarization_node,
    extraction_node,
    refine_node,
    generate_srs_node,
    generate_srs_pdf_node,
    document_node,
    await_client_node,
    speech_enhancement_node,
    speaker_alignment_node
)
from graph.router import route_workflow
from graph.router import route_after_client
from langgraph.checkpoint.memory import InMemorySaver


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("router", lambda state: state)
    builder.add_node("enhance", speech_enhancement_node)
    builder.add_node("speaker_alignment", speaker_alignment_node)
    builder.add_node("transcribe", transcribe_node)
    builder.add_node("document", document_node)
    builder.add_node("diarize", diarization_node)
    builder.add_node("extract", extraction_node)
    builder.add_node("refine", refine_node)
    builder.add_node("srs", generate_srs_node)
    builder.add_node("generate_pdf", generate_srs_pdf_node)
    builder.add_node("await_client", await_client_node)
    
    builder.set_entry_point("router")
    
    builder.add_conditional_edges(
        "router",
        route_workflow
    )
    
    # enhance quality of the audio
    builder.add_edge("enhance","transcribe")
    
    #audio extraction
    builder.add_edge("transcribe", "diarize")
    builder.add_edge("diarize", "speaker_alignment")
    builder.add_edge("speaker_alignment", "extract")
    # builder.add_edge("extract", END)
    builder.add_edge("extract", "await_client")
    
    #document extraction
    builder.add_edge("document", "extract")
    
    builder.add_conditional_edges(
           "await_client",
           route_after_client
    )
    
    # refine
    builder.add_edge("refine", "await_client")
    
    #srs
    builder.add_edge("srs", "generate_pdf")
    builder.add_edge("generate_pdf", END)
    
   
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)
    
        
    
    
    
    