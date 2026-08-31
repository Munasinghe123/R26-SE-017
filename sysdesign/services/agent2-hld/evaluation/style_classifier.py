"""
Evaluation — Style Classifier

Rule-based architectural style detection from a parsed CAM architecture.
Implements 5 style detectors for: Layered, Microservices, Event-Driven,
Modular Monolith, and Pipe-and-Filter.

Each detector returns a confidence score [0.0, 1.0] based on structural
indicators in the component graph. The style with the highest confidence
is selected. If no style exceeds 0.40 confidence, "hybrid" is returned.

References:
    Richards, M. & Ford, N. (2020). Fundamentals of Software Architecture.
    Newman, S. (2019). Monolith to Microservices.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Structural Indicator Keywords ─────────────────────

_LAYER_INDICATORS = {
    "presentation", "ui", "frontend", "client", "web",
    "application", "business", "business_logic", "service",
    "domain", "data_access", "persistence", "database",
    "infrastructure", "api", "gateway",
}

_MICROSERVICE_INDICATORS = {
    "api gateway", "gateway", "service registry", "discovery",
    "consul", "eureka", "load balancer", "circuit breaker",
    "sidecar", "mesh",
}

_EVENT_INDICATORS = {
    "event bus", "message broker", "broker", "kafka", "rabbitmq",
    "queue", "topic", "publisher", "subscriber", "consumer",
    "producer", "event store", "stream",
}

_MODULAR_MONOLITH_INDICATORS = {
    "module", "bounded context", "package", "namespace",
    "internal", "facade", "public api",
}

_PIPE_FILTER_INDICATORS = {
    "filter", "pipe", "pipeline", "transformer", "processor",
    "stage", "step", "chain", "stream processor",
}


def _get_component_names_lower(architecture: dict) -> list[str]:
    """Extract lowercase component names."""
    return [
        c.get("name", "").strip().lower()
        for c in architecture.get("components", [])
        if c.get("name", "").strip()
    ]


def _get_responsibilities_text(architecture: dict) -> str:
    """Concatenate all component responsibilities into searchable text."""
    parts = []
    for c in architecture.get("components", []):
        # Handle both singular 'responsibility' and plural 'responsibilities'
        if isinstance(c.get("responsibilities"), list):
            parts.extend(c["responsibilities"])
        if c.get("responsibility"):
            parts.append(c["responsibility"])
        parts.append(c.get("name", ""))
    return " ".join(parts).lower()


def _get_connector_types(architecture: dict) -> list[str]:
    """Extract connector types from connectors or interactions."""
    connectors = architecture.get("connectors", []) or architecture.get("interactions", []) or []
    types = []
    for conn in connectors:
        ct = conn.get("connector_type", "") or conn.get("type", "") or ""
        types.append(ct.strip().lower())
    return types


def _count_indicators(text: str, names: list[str], indicators: set[str]) -> int:
    """Count how many indicator keywords appear in component names or text."""
    count = 0
    search_text = text + " " + " ".join(names)
    for indicator in indicators:
        if indicator in search_text:
            count += 1
    return count


def _detect_layered(architecture: dict, names: list[str], text: str) -> float:
    """Detect Layered Architecture.

    Signals: explicit layer definitions, layer-like component names,
    top-down dependency flow.
    """
    confidence = 0.0

    # Has explicit layers defined?
    layers = architecture.get("layers", [])
    if layers and len(layers) >= 2:
        confidence += 0.35

    # Layer-like component names/boundaries
    layer_hits = _count_indicators(text, names, _LAYER_INDICATORS)
    if layer_hits >= 3:
        confidence += 0.25
    elif layer_hits >= 1:
        confidence += 0.10

    # Check for boundary fields
    boundaries = set()
    for c in architecture.get("components", []):
        b = (c.get("boundary", "") or c.get("layer", "") or "").strip().lower()
        if b:
            boundaries.add(b)
    if len(boundaries) >= 3:
        confidence += 0.20
    elif len(boundaries) >= 2:
        confidence += 0.10

    # Negative signal: microservice/event indicators suggest NOT layered
    ms_hits = _count_indicators(text, names, _MICROSERVICE_INDICATORS)
    ev_hits = _count_indicators(text, names, _EVENT_INDICATORS)
    if ms_hits >= 2 or ev_hits >= 2:
        confidence -= 0.15

    return max(0.0, min(1.0, confidence))


def _detect_microservices(architecture: dict, names: list[str], text: str) -> float:
    """Detect Microservices Architecture.

    Signals: API gateway, service registry, independently deployable services,
    inter-service communication patterns.
    """
    confidence = 0.0

    ms_hits = _count_indicators(text, names, _MICROSERVICE_INDICATORS)
    if ms_hits >= 3:
        confidence += 0.40
    elif ms_hits >= 2:
        confidence += 0.25
    elif ms_hits >= 1:
        confidence += 0.10

    # Count service-named components
    service_count = sum(1 for n in names if n.endswith("service") or " service" in n)
    if service_count >= 4:
        confidence += 0.25
    elif service_count >= 2:
        confidence += 0.15

    # Gateway present?
    has_gateway = any("gateway" in n for n in names)
    if has_gateway:
        confidence += 0.15

    # Connector types: REST, gRPC between services
    conn_types = _get_connector_types(architecture)
    rest_grpc = sum(1 for ct in conn_types if any(k in ct for k in ["rest", "grpc", "http", "sync_call"]))
    if rest_grpc >= 3:
        confidence += 0.10

    return max(0.0, min(1.0, confidence))


def _detect_event_driven(architecture: dict, names: list[str], text: str) -> float:
    """Detect Event-Driven Architecture.

    Signals: message broker/event bus, publisher/subscriber components,
    async_message/event_publish connector types.
    """
    confidence = 0.0

    ev_hits = _count_indicators(text, names, _EVENT_INDICATORS)
    if ev_hits >= 3:
        confidence += 0.40
    elif ev_hits >= 2:
        confidence += 0.25
    elif ev_hits >= 1:
        confidence += 0.10

    # Broker/bus component?
    has_broker = any(
        any(k in n for k in ["broker", "bus", "kafka", "rabbitmq", "queue"])
        for n in names
    )
    if has_broker:
        confidence += 0.20

    # Async connector types
    conn_types = _get_connector_types(architecture)
    async_count = sum(
        1 for ct in conn_types
        if any(k in ct for k in ["async", "event", "publish", "subscribe", "message"])
    )
    if async_count >= 3:
        confidence += 0.20
    elif async_count >= 1:
        confidence += 0.10

    return max(0.0, min(1.0, confidence))


def _detect_modular_monolith(architecture: dict, names: list[str], text: str) -> float:
    """Detect Modular Monolith Architecture.

    Signals: module/package groupings, bounded contexts, facade components,
    absence of distributed infrastructure (no gateway/registry).
    """
    confidence = 0.0

    mm_hits = _count_indicators(text, names, _MODULAR_MONOLITH_INDICATORS)
    if mm_hits >= 3:
        confidence += 0.35
    elif mm_hits >= 2:
        confidence += 0.20
    elif mm_hits >= 1:
        confidence += 0.10

    # Has layers but no distributed infra → likely modular monolith
    layers = architecture.get("layers", [])
    if layers and len(layers) >= 2:
        confidence += 0.10

    # No gateway/registry → not microservices
    ms_hits = _count_indicators(text, names, _MICROSERVICE_INDICATORS)
    if ms_hits == 0:
        confidence += 0.15

    # Module-like naming
    module_count = sum(1 for n in names if "module" in n or "package" in n)
    if module_count >= 2:
        confidence += 0.15

    return max(0.0, min(1.0, confidence))


def _detect_pipe_and_filter(architecture: dict, names: list[str], text: str) -> float:
    """Detect Pipe-and-Filter (Pipeline) Architecture.

    Signals: filter/processor/stage components, linear chain topology,
    data_flow connector types.
    """
    confidence = 0.0

    pf_hits = _count_indicators(text, names, _PIPE_FILTER_INDICATORS)
    if pf_hits >= 3:
        confidence += 0.40
    elif pf_hits >= 2:
        confidence += 0.25
    elif pf_hits >= 1:
        confidence += 0.10

    # Check for linear chain topology: most components have fan-in=1, fan-out=1
    connectors = architecture.get("connectors", []) or architecture.get("interactions", []) or []
    if connectors:
        fan_out: dict[str, int] = {}
        fan_in: dict[str, int] = {}
        for conn in connectors:
            fc = conn.get("from_component", "") or conn.get("from", "") or ""
            tc = conn.get("to_component", "") or conn.get("to", "") or ""
            if fc:
                fan_out[fc] = fan_out.get(fc, 0) + 1
            if tc:
                fan_in[tc] = fan_in.get(tc, 0) + 1

        all_comps = set(fan_out.keys()) | set(fan_in.keys())
        if all_comps:
            linear_count = sum(
                1 for c in all_comps
                if fan_out.get(c, 0) <= 1 and fan_in.get(c, 0) <= 1
            )
            linearity = linear_count / len(all_comps)
            if linearity >= 0.70:
                confidence += 0.25
            elif linearity >= 0.50:
                confidence += 0.10

    # data_flow connector types
    conn_types = _get_connector_types(architecture)
    data_flow_count = sum(1 for ct in conn_types if "data_flow" in ct or "pipe" in ct)
    if data_flow_count >= 2:
        confidence += 0.15

    return max(0.0, min(1.0, confidence))


# ── Style alias normalization ────────────────────────

STYLE_ALIASES: dict[str, str] = {
    "layered architecture": "layered",
    "layered": "layered",
    "n-tier": "layered",
    "n-tier architecture": "layered",
    "microservices architecture": "microservices",
    "microservice architecture": "microservices",
    "microservices": "microservices",
    "event-driven architecture": "event_driven",
    "event driven architecture": "event_driven",
    "event-driven": "event_driven",
    "event driven": "event_driven",
    "modular monolith": "modular_monolith",
    "modular monolith architecture": "modular_monolith",
    "pipe-and-filter": "pipe_and_filter",
    "pipe and filter": "pipe_and_filter",
    "pipe-and-filter architecture": "pipe_and_filter",
    "pipeline": "pipe_and_filter",
    "pipeline architecture": "pipe_and_filter",
    # Legacy aliases (from old config)
    "microkernel architecture": "modular_monolith",
    "microkernel": "modular_monolith",
    "space-based architecture": "layered",
    "space-based": "layered",
}


def normalize_style_name(style: str) -> str:
    """Normalize a style name string to canonical form."""
    return STYLE_ALIASES.get((style or "").strip().lower(), "layered")


# ── Style display names ─────────────────────────────

STYLE_DISPLAY_NAMES: dict[str, str] = {
    "layered": "Layered Architecture",
    "microservices": "Microservices Architecture",
    "event_driven": "Event-Driven Architecture",
    "modular_monolith": "Modular Monolith",
    "pipe_and_filter": "Pipe-and-Filter Architecture",
    "hybrid": "Hybrid Architecture",
}


def classify_style(architecture: dict) -> tuple[str, dict[str, float]]:
    """Classify the architectural style of a parsed architecture.

    Args:
        architecture: Parsed architecture dict with components, connectors, layers

    Returns:
        Tuple of (detected_style, confidence_dict)
        detected_style: one of "layered", "microservices", "event_driven",
                        "modular_monolith", "pipe_and_filter", "hybrid"
        confidence_dict: {style_name: confidence_score} for all 5 styles
    """
    names = _get_component_names_lower(architecture)
    text = _get_responsibilities_text(architecture)

    confidences = {
        "layered": _detect_layered(architecture, names, text),
        "microservices": _detect_microservices(architecture, names, text),
        "event_driven": _detect_event_driven(architecture, names, text),
        "modular_monolith": _detect_modular_monolith(architecture, names, text),
        "pipe_and_filter": _detect_pipe_and_filter(architecture, names, text),
    }

    # Select the style with highest confidence
    best_style = max(confidences, key=confidences.get)
    best_confidence = confidences[best_style]

    # If no style exceeds threshold, classify as hybrid
    if best_confidence < 0.40:
        detected = "hybrid"
    else:
        detected = best_style

    # Also consider the LLM-declared style as a tiebreaker
    declared_style = normalize_style_name(
        architecture.get("architecture_style", "")
    )

    # If declared style confidence is within 0.10 of the best detected,
    # prefer the declared style (LLM had intent)
    if declared_style in confidences:
        declared_conf = confidences[declared_style]
        if declared_conf >= best_confidence - 0.10 and declared_conf >= 0.30:
            detected = declared_style

    logger.info(
        f"Style classification: detected={detected} "
        f"(confidences: {', '.join(f'{k}={v:.2f}' for k, v in confidences.items())})"
    )

    return detected, confidences
