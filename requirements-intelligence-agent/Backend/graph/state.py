from typing import TypedDict, Optional, List, Dict

class GraphState(TypedDict):
    
    # agent state tracking
    previous_requirements: Optional[Dict]
    feedback_history: Optional[List[str]]
    iteration_count: Optional[int]
    convergence_score: Optional[float]
    
    # routing
    mode:str
    
    # transcription
    audio_path: Optional[str]
    transcript: Optional[str]
    transcript_segments: Optional[List[Dict]]
    speaker_segments: Optional[List[Dict]]
    speaker_roles: Optional[Dict[str, str]]
    
    #document
    document_path: Optional[str]
    
    # requirments 
    requirements: Optional[Dict]
    feedback: Optional[str]
    
    client_decision: Optional[Dict]
    client_view: Optional[Dict]
    client_review: Optional[List[Dict]]
    change_set: Optional[Dict]
    change_analysis: Optional[Dict]
    clarification_questions: Optional[Dict]
    client_answers: Optional[List[Dict]]
    answer_requirements: Optional[Dict]
    accepted_changes: dict
    clarification_changes: dict
    
    new_requirements: Optional[List[Dict]]
    classified_new_requirements: Optional[List[Dict]]
    requirements_to_rewrite: Optional[List[Dict]]
    normalized_new_requirements: Optional[List[Dict]]
    
    final_requirements: Optional[Dict]
    
    # approval
    review_status: Optional[str]
    
    # srs
    srs_text: Optional[Dict]
    pdf_path: Optional[str]
    
    thread_id: Optional[str]
    project_id:Optional[str]
    