from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from contracts.v1.architecture import Boundary, ElementType


class RawCAMComponent(BaseModel):
    id: Optional[str] = None
    name: str = Field(description="Component name in PascalCase with role suffix")
    layer: Optional[str] = Field(default=None, description="Layer or boundary name")
    element_type: Optional[str] = Field(default=None, description="Element type e.g. service, repository, gateway")
    boundary: Optional[str] = Field(default=None, description="Boundary e.g. presentation, business_logic, data_access")
    responsibility: Optional[str] = Field(default="", description="Description of component responsibility")
    responsibilities: Optional[List[str]] = Field(default_factory=list, description="List of responsibility statements")
    provided_interfaces: Optional[List[str]] = Field(default_factory=list)
    required_interfaces: Optional[List[str]] = Field(default_factory=list)
    requirement_ids: Optional[List[str]] = Field(default_factory=list)


class RawCAMConnector(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None
    from_component: Optional[str] = Field(default=None, alias="from")
    to_component: Optional[str] = Field(default=None, alias="to")
    connector_type: Optional[str] = Field(default="sync_call", alias="type")
    protocol: Optional[str] = Field(default="")
    data_transferred: Optional[str] = Field(default="")


class RawCAMQualityProvision(BaseModel):
    nfr_id: str
    iso_characteristic: Optional[str] = "performance_efficiency"
    responsible_component: str
    mechanism: str
    evidence_strength: Optional[str] = "medium"


class RawCAMArchitecture(BaseModel):
    architecture_style: str = Field(default="Layered Architecture")
    style_confidence: Optional[float] = 1.0
    pros_and_cons: Optional[str] = ""
    layers: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    components: List[RawCAMComponent] = Field(min_length=1)
    interactions: Optional[List[RawCAMConnector]] = Field(default_factory=list)
    connectors: Optional[List[RawCAMConnector]] = Field(default_factory=list)
    quality_provisions: Optional[List[RawCAMQualityProvision]] = Field(default_factory=list)
