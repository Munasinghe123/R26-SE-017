"""
Evaluation — QAC: Quality Attribute Coverage

Formula:
    QAC = |{NFR_k : has_provision(NFR_k, architecture)}| / |NFR|

Each non-functional requirement is checked for architectural provision using
4 evidence paths (in priority order):
    1. Component name indicators (e.g., "CacheService" → performance)
    2. Semantic responsibility match (cosine_sim >= θ_qa with NFR description)
    3. Declared architectural patterns (e.g., "circuit breaker" in responsibilities)
    4. Explicit quality_provisions references (structured CAM field)

NFRs are mapped to ISO/IEC 25010 quality characteristics for structured evaluation.

The threshold θ_qa should be calibrated using evaluation/calibration.py.
Default: 0.50 (preliminary, to be justified via F1-score calibration).
"""

import logging
from evaluation.semantic_engine import get_engine

logger = logging.getLogger(__name__)

DEFAULT_QAC_THRESHOLD = 0.50


# ── ISO/IEC 25010 Quality Characteristic Mapping ─────

ISO_25010_MAP: dict[str, str] = {
    # Performance efficiency
    "performance": "performance_efficiency",
    "speed": "performance_efficiency",
    "latency": "performance_efficiency",
    "throughput": "performance_efficiency",
    "response time": "performance_efficiency",
    # Reliability
    "reliability": "reliability",
    "availability": "reliability",
    "fault tolerance": "reliability",
    "recoverability": "reliability",
    # Security
    "security": "security",
    "confidentiality": "security",
    "integrity": "security",
    "authentication": "security",
    "authorization": "security",
    # Maintainability
    "maintainability": "maintainability",
    "modularity": "maintainability",
    "reusability": "maintainability",
    "modifiability": "maintainability",
    "testability": "maintainability",
    # Scalability (mapped to performance_efficiency sub-char)
    "scalability": "performance_efficiency",
    # Portability
    "portability": "portability",
    "adaptability": "portability",
    "installability": "portability",
    # Usability
    "usability": "usability",
    "accessibility": "usability",
    "learnability": "usability",
    # Compatibility
    "compatibility": "compatibility",
    "interoperability": "compatibility",
}


# ── Evidence Indicators per ISO 25010 Characteristic ──

EVIDENCE_INDICATORS: dict[str, list[str]] = {
    "performance_efficiency": [
        "cache", "redis", "cdn", "index", "in-memory", "read replica",
        "async", "queue", "batch", "connection pool", "pagination",
        "compress", "lazy load", "buffer", "optimize", "throughput",
        "low latency", "fast response",
    ],
    "reliability": [
        "retry", "circuit breaker", "failover", "redundant", "backup",
        "health check", "monitoring", "watchdog", "graceful degradation",
        "hot standby", "high availability", "replica", "idempotent",
        "transaction", "saga", "dead letter", "rollback", "data integrity",
        "fault tolerance", "recovery",
    ],
    "security": [
        "encryption", "tls", "ssl", "oauth", "jwt", "rbac", "mfa",
        "auth", "token", "audit", "validate", "permission", "access control",
        "firewall", "hash", "sanitize", "certificate", "input validation",
        "secure", "authorization", "authentication",
    ],
    "maintainability": [
        "modular", "plugin", "interface", "abstraction", "factory",
        "repository pattern", "dependency injection", "loosely coupled",
        "separation of concerns", "clean code", "adapter", "port",
        "hexagonal", "layered", "testable", "decouple",
    ],
    "portability": [
        "container", "docker", "kubernetes", "cloud-native", "platform",
        "cross-platform", "portable", "deployment", "ci/cd",
    ],
    "usability": [
        "user interface", "ux", "responsive", "accessibility",
        "notification", "dashboard", "feedback",
    ],
    "compatibility": [
        "api", "rest", "grpc", "webhook", "integration", "interop",
        "standard", "protocol", "format",
    ],
}


def _normalize_nfr_type(nfr_type: str) -> str:
    """Normalize NFR type to ISO 25010 characteristic."""
    key = (nfr_type or "").strip().lower()
    return ISO_25010_MAP.get(key, key)


def _build_architecture_text(architecture: dict) -> str:
    """Build searchable text from all components and connectors."""
    parts = []
    for comp in architecture.get("components", []):
        parts.append(comp.get("name", ""))
        if isinstance(comp.get("responsibilities"), list):
            parts.extend(comp["responsibilities"])
        if comp.get("responsibility"):
            parts.append(comp["responsibility"])
    for conn in (architecture.get("connectors", []) or architecture.get("interactions", []) or []):
        parts.append(conn.get("connector_type", "") or conn.get("type", ""))
        parts.append(conn.get("protocol", ""))
    return " ".join(parts).lower()


def _check_component_indicators(arch_text: str, iso_char: str) -> bool:
    """Path 1: Check if component names/responsibilities contain evidence indicators."""
    indicators = EVIDENCE_INDICATORS.get(iso_char, [])
    for indicator in indicators:
        if indicator.lower() in arch_text:
            return True
    return False


def _check_semantic_match(nfr_desc: str, architecture: dict, threshold: float) -> bool:
    """Path 2: Semantic similarity between NFR description and component responsibilities."""
    engine = get_engine()

    for comp in architecture.get("components", []):
        # Build component text
        parts = [comp.get("name", "")]
        if isinstance(comp.get("responsibilities"), list):
            parts.extend(comp["responsibilities"])
        if comp.get("responsibility"):
            parts.append(comp["responsibility"])
        comp_text = " ".join(p for p in parts if p).strip()

        if comp_text and engine.cosine_sim(nfr_desc, comp_text) >= threshold:
            return True

    return False


def _check_declared_patterns(nfr_desc: str, arch_text: str) -> bool:
    """Path 3: Check if NFR-specific architectural patterns are declared."""
    # Extract key concepts from NFR description
    nfr_lower = nfr_desc.lower()
    pattern_indicators = []

    if any(k in nfr_lower for k in ["scale", "scalab", "load"]):
        pattern_indicators.extend(["load balancer", "auto-scale", "horizontal", "replica"])
    if any(k in nfr_lower for k in ["secur", "auth", "encrypt"]):
        pattern_indicators.extend(["encryption", "jwt", "oauth", "rbac", "tls"])
    if any(k in nfr_lower for k in ["perform", "speed", "latency", "fast"]):
        pattern_indicators.extend(["cache", "redis", "async", "in-memory"])
    if any(k in nfr_lower for k in ["reliab", "avail", "fault"]):
        pattern_indicators.extend(["circuit breaker", "retry", "failover", "health check"])
    if any(k in nfr_lower for k in ["maintain", "modular", "extensi"]):
        pattern_indicators.extend(["modular", "plugin", "dependency injection"])

    return any(p in arch_text for p in pattern_indicators)


def _check_quality_provisions(nfr_id: str, architecture: dict) -> bool:
    """Path 4: Check explicit quality_provisions in the CAM."""
    for qp in architecture.get("quality_provisions", []):
        if qp.get("nfr_id") == nfr_id:
            return True
    return False


def compute_qac(architecture: dict, requirements: dict,
                threshold: float = DEFAULT_QAC_THRESHOLD) -> dict:
    """Compute Quality Attribute Coverage.

    Args:
        architecture: Parsed architecture dict
        requirements: Requirements dict with 'non_functional_requirements'
        threshold: Semantic similarity threshold for Path 2

    Returns:
        {
            "score": float (0.0 - 1.0),
            "covered": int,
            "total": int,
            "threshold": float,
            "coverage_map": {
                nfr_id: {
                    "type": str, "iso_characteristic": str,
                    "covered": bool, "evidence_path": str,
                    "details": dict
                }
            },
            "uncovered": [nfr_ids]
        }
    """
    nfrs = requirements.get("non_functional_requirements", [])

    if not nfrs:
        return {
            "score": 1.0, "covered": 0, "total": 0,
            "threshold": threshold,
            "coverage_map": {}, "uncovered": [],
        }

    arch_text = _build_architecture_text(architecture)
    coverage_map = {}
    uncovered = []
    covered_count = 0

    for nfr in nfrs:
        nfr_id = nfr.get("id", "?")
        nfr_type = nfr.get("type", "")
        nfr_desc = nfr.get("target", "") or nfr.get("description", "")
        iso_char = _normalize_nfr_type(nfr_type)

        evidence_path = None
        details = {
            "nfr_type": nfr_type,
            "iso_characteristic": iso_char,
        }

        # Path 1: Component name indicators
        if _check_component_indicators(arch_text, iso_char):
            evidence_path = "component_indicators"

        # Path 2: Semantic responsibility match
        elif nfr_desc and _check_semantic_match(nfr_desc, architecture, threshold):
            evidence_path = "semantic_match"

        # Path 3: Declared architectural patterns
        elif nfr_desc and _check_declared_patterns(nfr_desc, arch_text):
            evidence_path = "declared_patterns"

        # Path 4: Explicit quality provisions
        elif _check_quality_provisions(nfr_id, architecture):
            evidence_path = "quality_provisions"

        is_covered = evidence_path is not None
        coverage_map[nfr_id] = {
            "type": nfr_type,
            "iso_characteristic": iso_char,
            "covered": is_covered,
            "evidence_path": evidence_path,
            "details": details,
        }

        if is_covered:
            covered_count += 1
        else:
            uncovered.append(nfr_id)

    total = len(nfrs)
    score = covered_count / total if total > 0 else 0.0

    logger.info(f"QAC: {covered_count}/{total} = {score:.3f} (θ={threshold}) | Uncovered: {uncovered}")

    return {
        "score": round(score, 4),
        "covered": covered_count,
        "total": total,
        "threshold": threshold,
        "coverage_map": coverage_map,
        "uncovered": uncovered,
    }
