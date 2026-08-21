from langgraph.graph import StateGraph, END
from graph.state import UMLGraphState
from graph.nodes import generate_node, parse_node, validate_node
from graph.router import route_after_generate, route_after_parse, route_after_validate

def build_uml_graph():
    """
    Constructs and compiles the LangGraph state machine for UML generation.
    """
    workflow = StateGraph(UMLGraphState)
    
    # 1. Add the processing nodes
    workflow.add_node("generate", generate_node)
    workflow.add_node("parse", parse_node)
    workflow.add_node("validate", validate_node)
    
    # 2. Define the entry point
    workflow.set_entry_point("generate")
    
    # 3. Define the conditional edges (routing)
    workflow.add_conditional_edges(
        "generate", 
        route_after_generate, 
        {"parse": "parse"}
    )
    
    workflow.add_conditional_edges(
        "parse", 
        route_after_parse, 
        {
            "generate": "generate", 
            "validate": "validate", 
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "validate", 
        route_after_validate, 
        {
            "generate": "generate", 
            END: END
        }
    )
    
    # 4. Compile the graph into an executable application
    return workflow.compile()