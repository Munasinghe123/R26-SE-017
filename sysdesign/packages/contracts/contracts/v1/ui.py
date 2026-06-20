from typing import Literal, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from contracts.v1.requirements import FunctionalRequirement, NonFunctionalRequirement


class UIComponent(BaseModel):
    name: str
    responsibilities: List[str] = Field(default_factory=list)
    covers_frs: List[str] = Field(default_factory=list)


class UIRequest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    job_id: str
    project_name: str
    domain: str = ""
    functional_requirements: List[FunctionalRequirement] = Field(default_factory=list)
    non_functional_requirements: List[NonFunctionalRequirement] = Field(default_factory=list)
    ui_components: List[UIComponent] = Field(default_factory=list)   # presentation-boundary only
    architecture_pattern: str = ""
    data_dictionary: List[dict] = Field(default_factory=list)  # From LLD: entities/classes
    api_contracts: List[dict] = Field(default_factory=list)    # From LLD: sequences/methods
    design_artifacts: Dict[str, Any] = Field(default_factory=dict)


class PlannedScreen(BaseModel):
    screen_id: str
    screen_name: str
    screen_type: str = "full-page"
    user_role: str = "User"
    purpose: str = ""
    key_actions: List[str] = Field(default_factory=list)
    relevant_frs: List[str] = Field(default_factory=list)
    depends_on: Optional[str] = None
    priority: str = "High"


class UIPackage(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    job_id: str
    project_name: str
    domain: str = "General"
    screens: List[PlannedScreen] = Field(default_factory=list)
    generated_screens: Dict[str, str] = Field(default_factory=dict)  # screen_id -> html or cloudinary_url
    evaluation_reports: List[dict] = Field(default_factory=list)
    refinement_histories: Dict[str, list] = Field(default_factory=dict)
    traceability_matrices: Dict[str, dict] = Field(default_factory=dict)
    overall_score: float = 88.5
    artifact_uris: Dict[str, str] = Field(default_factory=dict)
