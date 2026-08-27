from typing import TypedDict, Optional

class UMLGraphState(TypedDict):
    """
    Represents the state of our LangGraph execution for UML generation.
    """
    requirements: str
    requirement_ids: list[str]
    extra_rules: str
    llm_response: str
    parsed_json: Optional[dict]
    validation_result: Optional[dict]
    iterations_used: int
    max_iterations: int
    is_successful: bool