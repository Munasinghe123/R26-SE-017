from pydantic import BaseModel, Field


class RequirementRequest(BaseModel):
    requirements: str


class ArchitecturalLayer(BaseModel):
    name: str = ""
    description: str = ""
    components: list[str] = Field(default_factory=list)


class HighLevelArchitecture(BaseModel):
    pattern: str = ""
    layers: list[ArchitecturalLayer] = Field(default_factory=list)
    architectural_constraints: list[str] = Field(default_factory=list)


class FunctionalRequirement(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""


class GenerateRequest(BaseModel):
    project_name: str = ""
    project_description: str = ""
    high_level_architecture: HighLevelArchitecture = Field(default_factory=HighLevelArchitecture)
    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    export_formats: list[str] = Field(default_factory=lambda: ["png"])