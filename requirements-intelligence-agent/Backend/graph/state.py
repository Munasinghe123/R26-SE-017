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
    
    # approval
    approval_status: Optional[str]
    
    # srs
    srs_text: Optional[Dict]
    pdf_path: Optional[str]
    
    meeting_id: Optional[str]
    project_id:Optional[str]
    