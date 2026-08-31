import re
import json
import logging
from typing import Dict, Any, List, Optional

from contracts.v1.architecture import (
    Boundary,
    ElementType,
    Component,
    Connector,
    QualityProvision,
    MetricScores,
    ArchitecturePackage,
)
from cam.schema import RawCAMArchitecture, RawCAMComponent, RawCAMConnector

logger = logging.getLogger("cam-parser")


class CAMParseError(Exception):
    """Raised when LLM text output cannot be extracted or validated into a valid CAM."""
    pass


def extract_json_from_text(raw_text: str) -> str:
    """
    Extract JSON string from raw LLM output text.
    Handles ```json fences, ``` code blocks, leading preambles, and trailing commentary.
    """
    if not raw_text or not raw_text.strip():
        raise CAMParseError("Empty response from LLM generation")

    text = raw_text.strip()

    # Strategy 1: ```json ... ``` code fence
    json_fence = re.search(r'```json\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if json_fence:
        return json_fence.group(1).strip()

    # Strategy 2: ``` ... ``` generic fence
    generic_fence = re.search(r'```\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if generic_fence:
        candidate = generic_fence.group(1).strip()
        if candidate.startswith("{"):
            return candidate

    # Strategy 3: Greedy brace matching from first { to last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1]

    return text


def _attempt_json_repair(json_str: str) -> str:
    """Fix common JSON formatting errors emitted by LLMs."""
    fixed = json_str
    # Remove single line comments // ...
    fixed = re.sub(r'//.*?$', '', fixed, flags=re.MULTILINE)
    # Remove trailing commas before } or ] (including across newlines)
    fixed = re.sub(r',\s*([\}\]])', r'\1', fixed)
    fixed = re.sub(r',\s*([\n\r\s]*[\}\]])', r'\1', fixed)
    return fixed


def normalize_boundary(layer_name: Optional[str], boundary_name: Optional[str]) -> Boundary:
    """Normalize layer or boundary string to standard Boundary enum."""
    val = (boundary_name or layer_name or "").lower().strip()
    if any(k in val for k in ["presentation", "ui", "frontend", "client", "web"]):
        return Boundary.PRESENTATION
    elif any(k in val for k in ["data", "db", "persistence", "database", "repository"]):
        return Boundary.DATA
    elif any(k in val for k in ["infra", "external", "integration"]):
        return Boundary.INFRASTRUCTURE
    elif any(k in val for k in ["cross", "common", "shared", "security"]):
        return Boundary.CROSS_CUTTING
    else:
        return Boundary.BUSINESS


def normalize_element_type(name: str, element_type: Optional[str]) -> ElementType:
    """Normalize element type string or deduce from component name."""
    type_str = (element_type or "").lower().strip()
    name_str = name.lower().strip()

    if "controller" in type_str or "controller" in name_str:
        return ElementType.CONTROLLER
    elif "gateway" in type_str or "gateway" in name_str or "api" in name_str:
        return ElementType.GATEWAY
    elif "repository" in type_str or "repo" in name_str or "dao" in name_str:
        return ElementType.REPOSITORY
    elif "broker" in type_str or "broker" in name_str or "bus" in name_str or "queue" in name_str:
        return ElementType.BROKER
    elif "handler" in type_str or "handler" in name_str or "consumer" in name_str:
        return ElementType.HANDLER
    elif "client" in type_str or "client" in name_str:
        return ElementType.CLIENT
    elif "manager" in type_str or "manager" in name_str:
        return ElementType.MANAGER
    elif "engine" in type_str or "engine" in name_str:
        return ElementType.ENGINE
    elif "module" in type_str:
        return ElementType.MODULE
    else:
        return ElementType.SERVICE


def parse_cam(
    raw_text: str,
    job_id: str = "job-dev",
    project_name: str = "SDLC Project",
    tenant_id: str = "dev"
) -> ArchitecturePackage:
    """
    Extract, parse, validate, and normalize raw LLM text into a clean ArchitecturePackage (CAM).

    Args:
        raw_text: Raw response string from LLM
        job_id: Job identifier
        project_name: Name of project
        tenant_id: Tenant identifier

    Returns:
        Validated ArchitecturePackage instance

    Raises:
        CAMParseError: If parsing or validation fails
    """
    json_str = extract_json_from_text(raw_text)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        fixed_str = _attempt_json_repair(json_str)
        try:
            data = json.loads(fixed_str)
        except json.JSONDecodeError as e:
            raise CAMParseError(f"Invalid JSON string from LLM: {e}\nRaw output sample: {raw_text[:300]}")

    if not isinstance(data, dict):
        raise CAMParseError(f"Expected JSON object, got {type(data).__name__}")

    try:
        raw_cam = RawCAMArchitecture(**data)
    except Exception as e:
        raise CAMParseError(f"CAM schema validation failed: {e}")

    # Build Component objects
    components: List[Component] = []
    for i, raw_c in enumerate(raw_cam.components):
        c_id = raw_c.id or f"C{i+1}"
        boundary = normalize_boundary(raw_c.layer, raw_c.boundary)
        element_type = normalize_element_type(raw_c.name, raw_c.element_type)

        resps = []
        if raw_c.responsibilities:
            resps = [r.strip() for r in raw_c.responsibilities if r.strip()]
        if not resps and raw_c.responsibility:
            resps = [raw_c.responsibility.strip()]
        if not resps:
            resps = [f"Handles core operational logic for {raw_c.name}"]

        components.append(Component(
            id=c_id,
            name=raw_c.name.strip(),
            element_type=element_type,
            boundary=boundary,
            responsibilities=resps,
            provided_interfaces=raw_c.provided_interfaces or [],
            required_interfaces=raw_c.required_interfaces or [],
            requirement_ids=raw_c.requirement_ids or [],
        ))

    # Build Connector objects from connectors or interactions
    raw_connectors = raw_cam.connectors or raw_cam.interactions or []
    connectors: List[Connector] = []
    for i, raw_conn in enumerate(raw_connectors):
        conn_id = raw_conn.id or f"conn_{i+1}"
        from_comp = raw_conn.from_component or ""
        to_comp = raw_conn.to_component or ""
        c_type = raw_conn.connector_type or "sync_call"
        if c_type not in ["sync_call", "async_message", "event_publish", "data_flow", "shared_data"]:
            c_type = "sync_call"

        if from_comp and to_comp:
            connectors.append(Connector(
                id=conn_id,
                from_component=from_comp,
                to_component=to_comp,
                connector_type=c_type,
                protocol=raw_conn.protocol or "",
                data_transferred=raw_conn.data_transferred or ""
            ))

    # Build Quality Provisions
    quality_provisions: List[QualityProvision] = []
    for qp in (raw_cam.quality_provisions or []):
        strength = qp.evidence_strength if qp.evidence_strength in ["high", "medium", "low"] else "medium"
        quality_provisions.append(QualityProvision(
            nfr_id=qp.nfr_id,
            iso_characteristic=qp.iso_characteristic or "performance_efficiency",
            responsible_component=qp.responsible_component,
            mechanism=qp.mechanism,
            evidence_strength=strength
        ))

    # Placeholder MetricScores — will be populated by evaluation engine
    initial_scores = MetricScores(
        RTS=0.0, QAC=0.0, CI=0.0, CoS=0.0, SSM1=0.0, SSM2=0.0, CAS=0.0
    )

    return ArchitecturePackage(
        schema_version="1.0",
        job_id=job_id,
        tenant_id=tenant_id,
        project_name=project_name,
        architecture_style=raw_cam.architecture_style,
        style_confidence=raw_cam.style_confidence or 1.0,
        components=components,
        connectors=connectors,
        quality_provisions=quality_provisions,
        scores=initial_scores,
        verdict="marginal",
        rejected_alternatives=[],
        generation_metadata={"parsed": True}
    )
