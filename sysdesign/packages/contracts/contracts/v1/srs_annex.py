from typing import Literal, List, Dict, Any
from pydantic import BaseModel, Field


class SRSDesignAnnex(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    job_id: str
    agent: Literal["hld", "lld", "ui"]
    component_responsibility_matrix: List[Dict[str, Any]] = Field(default_factory=list)
    external_interfaces: List[Dict[str, Any]] = Field(default_factory=list)
    nfr_allocation: List[Dict[str, Any]] = Field(default_factory=list)
    design_constraints: List[str] = Field(default_factory=list)
    quality_evidence: Dict[str, Any] = Field(default_factory=dict)        # metric scores as objective evidence
    artifact_uris: Dict[str, str] = Field(default_factory=dict)           # diagrams to embed in the SRS
