"""
Evaluation — Style-Specific Metrics (SSM₁ and SSM₂)

10 metric functions across 5 architectural styles, 2 per style.
The style classifier determines which pair to apply.

Style → SSM₁, SSM₂ Mapping:
    Layered         → LIS (Layer Integrity Score), DDS (Dependency Direction Score)
    Microservices   → SBA (Service Boundary Alignment), ISS (Interface Segregation Score)
    Event-Driven    → EFC (Event Flow Completeness), PSC (Publisher-Subscriber Coverage)
    Modular Monolith→ MCR (Module Cohesion Ratio), DDS (shared with Layered)
    Pipe-and-Filter → PC  (Pipeline Completeness), FIS (Filter Independence Score)

References:
    Richards, M. & Ford, N. (2020). Fundamentals of Software Architecture.
    Newman, S. (2019). Monolith to Microservices.
"""

import logging
from typing import Optional
from evaluation.semantic_engine import get_engine

logger = logging.getLogger(__name__)


# ── Helper functions ──────────────────────────────────

def _get_connectors(architecture: dict) -> list[dict]:
    """Get connectors from architecture, handling both field names."""
    return (
        architecture.get("connectors", [])
        or architecture.get("interactions", [])
        or []
    )


def _get_from_to(connector: dict) -> tuple[str, str]:
    """Extract (from, to) component names from a connector."""
    fc = (connector.get("from_component", "") or connector.get("from", "") or "").strip()
    tc = (connector.get("to_component", "") or connector.get("to", "") or "").strip()
    return fc, tc


def _get_component_layer(comp: dict) -> str:
    """Get layer/boundary name for a component."""
    return (
        comp.get("layer", "")
        or comp.get("boundary", "")
        or ""
    ).strip().lower()


def _build_layer_order(architecture: dict) -> dict[str, int]:
    """Build layer name → order mapping from architecture layers."""
    order_map = {}
    for layer in architecture.get("layers", []):
        name = (layer.get("name", "") or "").strip().lower()
        order = layer.get("order", 99)
        if name:
            order_map[name] = order

    # Default fallback layer ordering
    defaults = {
        "presentation": 1, "ui": 1, "frontend": 1, "client": 1,
        "api gateway": 2, "gateway": 2, "api": 2,
        "application": 3, "business logic": 3, "business": 3, "service": 3,
        "domain": 4,
        "data access": 5, "persistence": 5, "data": 5,
        "database": 6, "infrastructure": 6,
    }
    for k, v in defaults.items():
        if k not in order_map:
            order_map[k] = v

    return order_map


def _build_comp_layer_map(architecture: dict) -> dict[str, str]:
    """Map component name (lowercase) → layer name."""
    mapping = {}
    for comp in architecture.get("components", []):
        name = comp.get("name", "").strip()
        layer = _get_component_layer(comp)
        if name:
            mapping[name.lower()] = layer
    return mapping


def _get_responsibilities(comp: dict) -> list[str]:
    """Get responsibilities from component."""
    resps = []
    if isinstance(comp.get("responsibilities"), list):
        resps.extend(r.strip() for r in comp["responsibilities"] if r.strip())
    if comp.get("responsibility") and isinstance(comp["responsibility"], str):
        r = comp["responsibility"].strip()
        if r and r not in resps:
            resps.append(r)
    return resps


# ══════════════════════════════════════════════════════
# LAYERED ARCHITECTURE
# ══════════════════════════════════════════════════════

def compute_lis(architecture: dict) -> dict:
    """LIS — Layer Integrity Score.

    Fraction of connectors that respect layer ordering
    (i.e., connect between adjacent or same-tier layers).

    Score = valid_connectors / total_connectors
    """
    connectors = _get_connectors(architecture)
    if not connectors:
        return {"score": 1.0, "valid": 0, "total": 0, "violations": []}

    layer_order = _build_layer_order(architecture)
    clm = _build_comp_layer_map(architecture)

    valid = 0
    violations = []

    for conn in connectors:
        fc, tc = _get_from_to(conn)
        fl = clm.get(fc.lower(), "")
        tl = clm.get(tc.lower(), "")

        if not fl or not tl:
            valid += 1  # Can't evaluate → assume valid
            continue

        fo = layer_order.get(fl, 99)
        to = layer_order.get(tl, 99)

        # Valid: same layer, or one layer down (adjacent), or at most 2 layers skip
        if fo <= to and (to - fo) <= 2:
            valid += 1
        else:
            violations.append({
                "from": fc, "to": tc,
                "from_layer": fl, "to_layer": tl,
                "reason": f"Layer skip: {fc}(L{fo}) → {tc}(L{to})",
            })

    total = len(connectors)
    score = valid / total if total > 0 else 1.0

    logger.info(f"LIS: {score:.3f} | Valid: {valid}/{total}")
    return {"score": round(score, 4), "valid": valid, "total": total, "violations": violations}


def compute_dds(architecture: dict) -> dict:
    """DDS — Dependency Direction Score.

    Fraction of connectors following top-down flow
    (from_layer_order <= to_layer_order).

    Score = downward_connectors / total_connectors
    """
    connectors = _get_connectors(architecture)
    if not connectors:
        return {"score": 1.0, "downward": 0, "total": 0, "upward_violations": []}

    layer_order = _build_layer_order(architecture)
    clm = _build_comp_layer_map(architecture)

    downward = 0
    upward_violations = []

    for conn in connectors:
        fc, tc = _get_from_to(conn)
        fl = clm.get(fc.lower(), "")
        tl = clm.get(tc.lower(), "")

        if not fl or not tl:
            downward += 1  # Can't evaluate → assume valid
            continue

        fo = layer_order.get(fl, 99)
        to = layer_order.get(tl, 99)

        if fo <= to:
            downward += 1
        else:
            upward_violations.append({
                "from": fc, "to": tc,
                "reason": f"Upward: {fc}(L{fo}) → {tc}(L{to})",
            })

    total = len(connectors)
    score = downward / total if total > 0 else 1.0

    logger.info(f"DDS: {score:.3f} | Downward: {downward}/{total}")
    return {"score": round(score, 4), "downward": downward, "total": total, "upward_violations": upward_violations}


# ══════════════════════════════════════════════════════
# MICROSERVICES ARCHITECTURE
# ══════════════════════════════════════════════════════

def compute_sba(architecture: dict) -> dict:
    """SBA — Service Boundary Alignment.

    Semantic coherence of each service's responsibilities (bounded context).
    Uses sentence-transformer pairwise similarity.

    Score = mean(cohesion(service_i)) for service-like components
    """
    engine = get_engine()
    components = architecture.get("components", [])

    service_components = [
        c for c in components
        if any(k in c.get("name", "").lower() for k in ["service", "handler", "controller"])
    ]

    if not service_components:
        service_components = components  # Fallback: treat all as services

    if not service_components:
        return {"score": 0.0, "services_evaluated": 0, "details": []}

    details = []
    total_cohesion = 0.0
    count = 0

    for comp in service_components:
        name = comp.get("name", "Unknown")
        resps = _get_responsibilities(comp)

        if len(resps) <= 1:
            cohesion = 1.0
        else:
            cohesion = engine.pairwise_cohesion(resps)

        details.append({"name": name, "cohesion": round(cohesion, 4), "responsibilities": len(resps)})
        total_cohesion += cohesion
        count += 1

    score = total_cohesion / count if count > 0 else 0.0

    logger.info(f"SBA: {score:.3f} | Services: {count}")
    return {"score": round(score, 4), "services_evaluated": count, "details": details}


def compute_iss(architecture: dict) -> dict:
    """ISS — Interface Segregation Score.

    Fraction of service components that have explicitly defined
    provided_interfaces (non-empty).

    Score = services_with_interfaces / total_services
    """
    components = architecture.get("components", [])

    service_components = [
        c for c in components
        if any(k in c.get("name", "").lower() for k in ["service", "handler", "controller", "gateway"])
    ]

    if not service_components:
        service_components = components

    if not service_components:
        return {"score": 0.0, "with_interfaces": 0, "total_services": 0, "details": []}

    with_interfaces = 0
    details = []

    for comp in service_components:
        name = comp.get("name", "Unknown")
        provided = comp.get("provided_interfaces", []) or []
        has_interfaces = len(provided) > 0

        if has_interfaces:
            with_interfaces += 1

        details.append({"name": name, "has_interfaces": has_interfaces, "interface_count": len(provided)})

    total = len(service_components)
    score = with_interfaces / total if total > 0 else 0.0

    logger.info(f"ISS: {score:.3f} | With interfaces: {with_interfaces}/{total}")
    return {"score": round(score, 4), "with_interfaces": with_interfaces, "total_services": total, "details": details}


# ══════════════════════════════════════════════════════
# EVENT-DRIVEN ARCHITECTURE
# ══════════════════════════════════════════════════════

def compute_efc(architecture: dict, requirements: dict) -> dict:
    """EFC — Event Flow Completeness.

    Fraction of FRs traceable through event-based connector chains.
    An FR is "event-covered" if at least one component handling it
    participates in an event-type connector (async_message, event_publish).

    Score = event_covered_frs / total_frs
    """
    frs = requirements.get("functional_requirements", [])
    if not frs:
        return {"score": 1.0, "event_covered": 0, "total": 0, "details": []}

    connectors = _get_connectors(architecture)
    event_types = {"async_message", "event_publish", "event", "message queue"}

    # Components participating in event flows
    event_participants = set()
    for conn in connectors:
        ct = (conn.get("connector_type", "") or conn.get("type", "")).strip().lower()
        if any(et in ct for et in event_types):
            fc, tc = _get_from_to(conn)
            if fc:
                event_participants.add(fc.lower())
            if tc:
                event_participants.add(tc.lower())

    # Check which FRs are traceable to event-participating components
    engine = get_engine()
    components = architecture.get("components", [])
    event_covered = 0
    details = []

    for fr in frs:
        fr_id = fr.get("id", "?")
        fr_desc = fr.get("description", "")
        covered = False

        for comp in components:
            comp_name = comp.get("name", "").strip()
            if comp_name.lower() in event_participants:
                parts = [comp_name]
                parts.extend(_get_responsibilities(comp))
                comp_text = " ".join(parts)
                if fr_desc and engine.cosine_sim(fr_desc, comp_text) >= 0.45:
                    covered = True
                    break

        details.append({"fr_id": fr_id, "event_covered": covered})
        if covered:
            event_covered += 1

    total = len(frs)
    score = event_covered / total if total > 0 else 0.0

    logger.info(f"EFC: {score:.3f} | Event-covered FRs: {event_covered}/{total}")
    return {"score": round(score, 4), "event_covered": event_covered, "total": total, "details": details}


def compute_psc(architecture: dict) -> dict:
    """PSC — Publisher-Subscriber Coverage.

    Fraction of connectors using event-based communication types.

    Score = event_connectors / total_connectors
    """
    connectors = _get_connectors(architecture)
    if not connectors:
        return {"score": 0.0, "event_connectors": 0, "total": 0}

    event_keywords = {"async", "event", "publish", "subscribe", "message", "queue", "topic"}
    event_count = 0

    for conn in connectors:
        ct = (conn.get("connector_type", "") or conn.get("type", "")).strip().lower()
        if any(k in ct for k in event_keywords):
            event_count += 1

    total = len(connectors)
    score = event_count / total if total > 0 else 0.0

    logger.info(f"PSC: {score:.3f} | Event connectors: {event_count}/{total}")
    return {"score": round(score, 4), "event_connectors": event_count, "total": total}


# ══════════════════════════════════════════════════════
# MODULAR MONOLITH
# ══════════════════════════════════════════════════════

def compute_mcr(architecture: dict) -> dict:
    """MCR — Module Cohesion Ratio.

    Ratio of intra-module connectors to total connectors.
    Components in the same layer/boundary are considered the same module.

    Score = intra_module_connectors / total_connectors
    A higher ratio means modules are cohesive (internal communication > cross-module).
    """
    connectors = _get_connectors(architecture)
    if not connectors:
        return {"score": 1.0, "intra_module": 0, "inter_module": 0, "total": 0}

    clm = _build_comp_layer_map(architecture)

    intra = 0
    inter = 0

    for conn in connectors:
        fc, tc = _get_from_to(conn)
        fl = clm.get(fc.lower(), "unknown")
        tl = clm.get(tc.lower(), "unknown")

        if fl == tl and fl != "unknown":
            intra += 1
        else:
            inter += 1

    total = len(connectors)
    score = intra / total if total > 0 else 1.0

    logger.info(f"MCR: {score:.3f} | Intra: {intra}, Inter: {inter}")
    return {"score": round(score, 4), "intra_module": intra, "inter_module": inter, "total": total}


# ══════════════════════════════════════════════════════
# PIPE-AND-FILTER
# ══════════════════════════════════════════════════════

def compute_pc(architecture: dict, requirements: dict) -> dict:
    """PC — Pipeline Completeness.

    Fraction of FRs that have a complete filter chain (at least one path
    from an entry filter to an exit filter passing through the FR-handling
    component).

    Simplified: fraction of FRs traceable to a component that participates
    in a data_flow connector chain.
    """
    frs = requirements.get("functional_requirements", [])
    if not frs:
        return {"score": 1.0, "pipeline_covered": 0, "total": 0}

    connectors = _get_connectors(architecture)
    pipeline_types = {"data_flow", "pipe", "pipeline", "stream"}

    # Components in pipeline chains
    pipeline_participants = set()
    for conn in connectors:
        ct = (conn.get("connector_type", "") or conn.get("type", "")).strip().lower()
        if any(pt in ct for pt in pipeline_types):
            fc, tc = _get_from_to(conn)
            if fc:
                pipeline_participants.add(fc.lower())
            if tc:
                pipeline_participants.add(tc.lower())

    # If no explicit pipeline connectors, fallback: all components in linear chains
    if not pipeline_participants:
        for comp in architecture.get("components", []):
            name = comp.get("name", "").strip().lower()
            if any(k in name for k in ["filter", "processor", "transformer", "stage", "pipe"]):
                pipeline_participants.add(name)

    engine = get_engine()
    covered = 0

    for fr in frs:
        fr_desc = fr.get("description", "")
        fr_covered = False

        for comp in architecture.get("components", []):
            comp_name = comp.get("name", "").strip()
            if comp_name.lower() in pipeline_participants:
                parts = [comp_name]
                parts.extend(_get_responsibilities(comp))
                comp_text = " ".join(parts)
                if fr_desc and engine.cosine_sim(fr_desc, comp_text) >= 0.45:
                    fr_covered = True
                    break

        if fr_covered:
            covered += 1

    total = len(frs)
    score = covered / total if total > 0 else 0.0

    logger.info(f"PC: {score:.3f} | Pipeline-covered FRs: {covered}/{total}")
    return {"score": round(score, 4), "pipeline_covered": covered, "total": total}


def compute_fis(architecture: dict) -> dict:
    """FIS — Filter Independence Score.

    Fraction of filter/processor components that have no shared state
    (i.e., no shared_data connectors to other filters).

    Score = independent_filters / total_filters
    """
    components = architecture.get("components", [])
    connectors = _get_connectors(architecture)

    # Identify filter-like components
    filter_names = set()
    for comp in components:
        name = comp.get("name", "").strip()
        if any(k in name.lower() for k in ["filter", "processor", "transformer", "stage", "handler"]):
            filter_names.add(name.lower())

    if not filter_names:
        # No explicit filters → treat all components as filters
        filter_names = {c.get("name", "").strip().lower() for c in components if c.get("name")}

    if not filter_names:
        return {"score": 1.0, "independent": 0, "total": 0}

    # Find filters with shared_data connectors
    shared_state_participants = set()
    for conn in connectors:
        ct = (conn.get("connector_type", "") or conn.get("type", "")).strip().lower()
        if "shared" in ct or "shared_data" in ct:
            fc, tc = _get_from_to(conn)
            if fc.lower() in filter_names:
                shared_state_participants.add(fc.lower())
            if tc.lower() in filter_names:
                shared_state_participants.add(tc.lower())

    independent = len(filter_names) - len(shared_state_participants)
    total = len(filter_names)
    score = independent / total if total > 0 else 1.0

    logger.info(f"FIS: {score:.3f} | Independent: {independent}/{total}")
    return {"score": round(score, 4), "independent": independent, "total": total}


# ══════════════════════════════════════════════════════
# SSM DISPATCHER
# ══════════════════════════════════════════════════════

# Style → (SSM₁ function, SSM₂ function) mapping
STYLE_SSM_MAP: dict[str, tuple[str, str]] = {
    "layered":          ("LIS", "DDS"),
    "microservices":    ("SBA", "ISS"),
    "event_driven":     ("EFC", "PSC"),
    "modular_monolith": ("MCR", "DDS"),
    "pipe_and_filter":  ("PC",  "FIS"),
    "hybrid":           ("LIS", "DDS"),  # Fallback to layered metrics
}

# Display names for SSMs
SSM_DISPLAY_NAMES: dict[str, str] = {
    "LIS": "Layer Integrity Score",
    "DDS": "Dependency Direction Score",
    "SBA": "Service Boundary Alignment",
    "ISS": "Interface Segregation Score",
    "EFC": "Event Flow Completeness",
    "PSC": "Publisher-Subscriber Coverage",
    "MCR": "Module Cohesion Ratio",
    "PC":  "Pipeline Completeness",
    "FIS": "Filter Independence Score",
}


def compute_style_metrics(
    architecture: dict,
    requirements: dict,
    detected_style: str,
) -> dict:
    """Compute the 2 style-specific metrics for a detected architectural style.

    Args:
        architecture: Parsed architecture dict
        requirements: Requirements dict (needed for EFC, PC)
        detected_style: One of the 5 canonical styles or "hybrid"

    Returns:
        {
            "detected_style": str,
            "ssm1_name": str,
            "ssm2_name": str,
            "ssm1": {"score": float, ...details...},
            "ssm2": {"score": float, ...details...},
        }
    """
    ssm1_name, ssm2_name = STYLE_SSM_MAP.get(detected_style, ("LIS", "DDS"))

    # Dispatch to metric functions
    metric_dispatch = {
        "LIS": lambda: compute_lis(architecture),
        "DDS": lambda: compute_dds(architecture),
        "SBA": lambda: compute_sba(architecture),
        "ISS": lambda: compute_iss(architecture),
        "EFC": lambda: compute_efc(architecture, requirements),
        "PSC": lambda: compute_psc(architecture),
        "MCR": lambda: compute_mcr(architecture),
        "PC":  lambda: compute_pc(architecture, requirements),
        "FIS": lambda: compute_fis(architecture),
    }

    ssm1_result = metric_dispatch[ssm1_name]()
    ssm2_result = metric_dispatch[ssm2_name]()

    logger.info(
        f"Style metrics [{detected_style}]: "
        f"{ssm1_name}={ssm1_result['score']:.3f}, "
        f"{ssm2_name}={ssm2_result['score']:.3f}"
    )

    return {
        "detected_style": detected_style,
        "ssm1_name": ssm1_name,
        "ssm1_display": SSM_DISPLAY_NAMES.get(ssm1_name, ssm1_name),
        "ssm2_name": ssm2_name,
        "ssm2_display": SSM_DISPLAY_NAMES.get(ssm2_name, ssm2_name),
        "ssm1": ssm1_result,
        "ssm2": ssm2_result,
    }
