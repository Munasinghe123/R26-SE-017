from enum import Enum
from typing import Literal, List, Dict, Any
from pydantic import BaseModel, Field


class Boundary(str, Enum):
    PRESENTATION = "presentation"
    BUSINESS = "business_logic"
    DATA = "data_access"
    INFRASTRUCTURE = "infrastructure"
    CROSS_CUTTING = "cross_cutting"


class ElementType(str, Enum):
    SERVICE = "service"
    MODULE = "module"
    HANDLER = "handler"
    GATEWAY = "gateway"
    REPOSITORY = "repository"
    BROKER = "broker"
    CONTROLLER = "controller"
    CLIENT = "client"


class Component(BaseModel):
    id: str                            # "C1"
    name: str                          # "OrderService"
    element_type: ElementType
    boundary: Boundary
    responsibilities: List[str] = Field(min_length=1)
    provided_interfaces: List[str] = Field(default_factory=list)   # ["POST /orders", "GET /orders/{id}"]
    required_interfaces: List[str] = Field(default_factory=list)   # ["OrderRepository"]
    requirement_ids: List[str] = Field(default_factory=list)       # ["FR-1", "FR-3"]


class Connector(BaseModel):
    id: str
    from_component: str
    to_component: str
    connector_type: Literal["sync_call", "async_message", "event_publish", "data_flow", "shared_data"]
    protocol: str = ""                 # "REST" | "gRPC" | "AMQP"
    data_transferred: str = ""         # "OrderRequest, OrderResponse"


class QualityProvision(BaseModel):
    nfr_id: str
    iso_characteristic: str
    responsible_component: str
    mechanism: str                     # "Redis read-through cache"
    evidence_strength: Literal["high", "medium", "low"]


class MetricScores(BaseModel):
    RTS: float
    QAC: float
    CI: float
    CoS: float
    SSM1: float
    SSM2: float
    CAS: float


class ArchitecturePackage(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    job_id: str
    tenant_id: str = "dev"
    project_name: str
    architecture_style: str            # detected, not LLM-claimed
    style_confidence: float = 1.0
    components: List[Component]
    connectors: List[Connector]
    quality_provisions: List[QualityProvision] = Field(default_factory=list)
    scores: MetricScores
    verdict: Literal["accepted", "marginal", "rejected"]
    rejected_alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)
    artifact_uris: Dict[str, str] = Field(default_factory=dict)
