from typing import TypedDict, Optional, List, Dict, Any
from langgraph.checkpoint.memory import InMemorySaver


class GraphState(TypedDict):

    # routing
    mode: str

    # transcription
    audio_path: Optional[str]
    transcript: Optional[str]
    transcript_segments: Optional[List[Dict]]
    speaker_segments: Optional[List[Dict]]
    speaker_roles: Optional[Dict[str, str]]

    # document
    document_path: Optional[str]

    # requirements
    requirements: Optional[Dict]
    client_view: Optional[Dict]
    feedback: Optional[str]

    # agent state tracking
    previous_requirements: Optional[Dict]
    feedback_history: Optional[List[str]]
    iteration_count: Optional[int]
    convergence_score: Optional[float]

    # HITL — client review interrupt
    review_status: Optional[str]
    client_review: Optional[List[Dict]]     # raw items from interrupt resume
    change_set: Optional[Dict]              # {kept, edited, deleted, added}

    # HITL — change analysis
    change_analysis: Optional[Dict]
    accepted_changes: Optional[Dict]
    clarification_changes: Optional[List]

    # HITL — Q&A interrupt
    clarification_questions: Optional[Dict]
    client_answers: Optional[List[Dict]]
    answer_requirements: Optional[List]

    # HITL — new requirements pipeline
    new_requirements: Optional[List]
    classified_new_requirements: Optional[List]
    requirements_to_rewrite: Optional[List]
    normalized_new_requirements: Optional[List]

    # final output
    final_requirements: Optional[Dict]

    # srs
    srs_text: Optional[Dict]
    pdf_path: Optional[str]

    # identifiers
    meeting_id: Optional[str]
    thread_id: Optional[str]
    project_id: Optional[str]


checkpointer = InMemorySaver()
