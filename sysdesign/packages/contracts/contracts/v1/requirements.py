from typing import Literal, List
from pydantic import BaseModel, Field


class SourceEvidence(BaseModel):
    speaker: str          # "Client" | "Business Analyst"
    statement: str        # verbatim from transcript


class FunctionalRequirement(BaseModel):
    id: str               # "FR-1"
    title: str            # SYNTHESISED by adapter from description
    description: str      # "The system shall ..."
    source_evidence: List[SourceEvidence] = Field(default_factory=list)


class NonFunctionalRequirement(BaseModel):
    id: str               # "NFR-1"
    description: str
    iso_characteristic: str  # CLASSIFIED by adapter via semantic match (e.g. "performance_efficiency")
    source_evidence: List[SourceEvidence] = Field(default_factory=list)


class RequirementsPackage(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    job_id: str
    tenant_id: str = "dev"
    project_name: str
    purpose: str = ""
    scope: str = ""
    functional_requirements: List[FunctionalRequirement]
    non_functional_requirements: List[NonFunctionalRequirement]
    design_constraints: List[str] = Field(default_factory=list)
    external_interfaces: List[str] = Field(default_factory=list)
    standards_compliance: List[str] = Field(default_factory=list)
    assumptions_and_dependencies: List[str] = Field(default_factory=list)
    user_characteristics: List[str] = Field(default_factory=list)
