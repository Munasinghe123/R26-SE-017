from typing import Literal, List
from pydantic import BaseModel, Field
from contracts.v1.requirements import FunctionalRequirement


class ArchitecturalLayer(BaseModel):
    name: str                  # from Component.boundary, grouped
    description: str = ""
    components: List[str]      # component names in this boundary


class HighLevelArchitecture(BaseModel):
    pattern: str
    layers: List[ArchitecturalLayer]
    architectural_constraints: List[str] = Field(default_factory=list)   # interfaces + connectors + NFR alloc


class LLDRequest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    job_id: str
    project_name: str
    project_description: str = ""
    high_level_architecture: HighLevelArchitecture
    functional_requirements: List[FunctionalRequirement]
    export_formats: List[str] = Field(default_factory=lambda: ["png", "puml"])


class ClassAttribute(BaseModel):
    name: str
    type: str
    visibility: str = "private"

class ClassMethod(BaseModel):
    name: str
    params: List[str] = Field(default_factory=list)
    returns: str
    visibility: str = "public"

class ClassRelationship(BaseModel):
    type: str
    target: str
    multiplicity: str = ""

class LLDClass(BaseModel):
    name: str
    package: str = ""
    stereotype: str = "entity"
    attributes: List[ClassAttribute] = Field(default_factory=list)
    methods: List[ClassMethod] = Field(default_factory=list)
    relationships: List[ClassRelationship] = Field(default_factory=list)


class SequenceMessage(BaseModel):
    order: int
    from_actor: str = Field(alias="from")
    to_actor: str = Field(alias="to")
    message: str

class LLDSequence(BaseModel):
    use_case: str
    name: str
    participants: List[str] = Field(default_factory=list)
    messages: List[SequenceMessage] = Field(default_factory=list)


class EntityColumn(BaseModel):
    name: str
    type: str
    pk: bool = False
    fk: str = ""
    nullable: bool = False

class EntityRelationship(BaseModel):
    type: str
    target: str
    fk: str

class LLDEntity(BaseModel):
    name: str
    owning_component: str = ""
    columns: List[EntityColumn] = Field(default_factory=list)
    relationships: List[EntityRelationship] = Field(default_factory=list)


class ConsistencyReportCheck(BaseModel):
    name: str
    passed: bool

class ConsistencyReport(BaseModel):
    passed: bool
    checks: List[ConsistencyReportCheck] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)


class LLDPackage(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    job_id: str
    classes: List[LLDClass] = Field(default_factory=list)
    sequences: List[LLDSequence] = Field(default_factory=list)
    entities: List[LLDEntity] = Field(default_factory=list)
    consistency_report: ConsistencyReport
    consistency_score: float = 0.95
    expert_model: str = "meta-llama/llama-3.3-70b-instruct"
    reconciliation_status: str = "PASSED"
    candidates: List[dict] = Field(default_factory=list)
    diagrams: dict = Field(default_factory=dict)
    plantuml: dict = Field(default_factory=dict)
    artifact_uris: dict = Field(default_factory=dict)
