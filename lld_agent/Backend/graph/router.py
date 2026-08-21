from langgraph.graph import END
from graph.state import UMLGraphState

def route_after_generate(state: UMLGraphState) -> str:
    """
    After the LLM generates a response, always proceed to parsing.
    """
    return "parse"

def route_after_parse(state: UMLGraphState) -> str:
    """
    If parsing fails, loop back to generate with strict JSON rules.
    If parsing succeeds, proceed to validation.
    Terminates if the max iterations limit is reached.
    """
    if state["parsed_json"] is None:
        if state["iterations_used"] >= state["max_iterations"]:
            return END
        return "generate"
    return "validate"
    
def route_after_validate(state: UMLGraphState) -> str:
    """
    If validation passes, the workflow is complete.
    If validation fails with critical errors, loop back to generate with expert guidance.
    Terminates if the max iterations limit is reached.
    """
    if state["is_successful"] or state["iterations_used"] >= state["max_iterations"]:
        return END
    return "generate"