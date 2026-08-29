import re
from typing import Dict, Any, List
from contracts.v1.requirements import (
    RequirementsPackage,
    FunctionalRequirement,
    NonFunctionalRequirement,
    SourceEvidence,
)

ISO_25010_KEYWORDS = {
    "performance_efficiency": ["performance", "latency", "throughput", "speed", "fast", "ms", "second", "response time"],
    "scalability": ["scale", "concurrent", "users", "load", "capacity", "volume", "flash sale"],
    "security": ["security", "auth", "pci", "encrypt", "jwt", "access", "token", "privacy", "confidential"],
    "availability": ["availability", "uptime", "downtime", "99.", "ha", "redundant", "failover"],
    "maintainability": ["maintainability", "modular", "clean", "decoupled", "extensible", "refactor"],
    "reliability": ["reliability", "fault", "error", "recover", "backup", "resilient", "retry"],
    "usability": ["usability", "ux", "ui", "accessible", "user-friendly", "intuitive"],
    "compatibility": ["compatibility", "interoperable", "integration", "api", "standard"],
    "portability": ["portability", "platform", "cross-platform", "docker", "cloud"],
}

TYPE_MAP = {
    "performance": "performance_efficiency",
    "scalability": "scalability",
    "security": "security",
    "availability": "availability",
    "maintainability": "maintainability",
    "reliability": "reliability",
    "usability": "usability",
    "compatibility": "compatibility",
    "portability": "portability",
}


def synthesise_fr_title(description: str) -> str:
    """Synthesise a short title from the first few words of the FR description."""
    words = re.findall(r'\b\w+\b', description)
    if len(words) >= 3 and words[0].lower() == "the" and words[1].lower() == "system" and words[2].lower() == "shall":
        words = words[3:]
    title_words = words[:6]
    return " ".join(title_words).capitalize() if title_words else "Functional Requirement"


def classify_iso25010(description: str) -> str:
    """Classify NFR description into ISO/IEC 25010 quality characteristic."""
    desc_lower = description.lower()
    scores = {}
    for characteristic, keywords in ISO_25010_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        scores[characteristic] = score

    best_match = max(scores.items(), key=lambda x: x[1])
    if best_match[1] > 0:
        return best_match[0]
    return "performance_efficiency"  # default fallback


def _to_str_list(items: Any) -> List[str]:
    if not items or not isinstance(items, list):
        return []
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            entity = item.get("interacting_external_entity") or item.get("interacting_entity") or item.get("name") or ""
            purpose = item.get("purpose") or item.get("description") or ""
            if entity and purpose:
                result.append(f"{entity}: {purpose}")
            elif entity:
                result.append(entity)
            elif purpose:
                result.append(purpose)
            else:
                result.append(str(item))
        else:
            result.append(str(item))
    return result


def adapt(reqs_raw: Dict[str, Any]) -> RequirementsPackage:
    """
    Adapt raw dictionary or Agent 1 JSON output to valid RequirementsPackage.
    Handles legacy/raw schemas that lack FR titles or NFR ISO classification.
    """
    job_id = reqs_raw.get("job_id", "job-dev")
    project_name = reqs_raw.get("project_name") or reqs_raw.get("project", "Unknown Project")
    tenant_id = reqs_raw.get("tenant_id", "dev")

    raw_frs = reqs_raw.get("functional_requirements", [])
    if isinstance(reqs_raw.get("specified_requirements"), dict):
        raw_frs = reqs_raw["specified_requirements"].get("functional", raw_frs)

    fr_objects: List[FunctionalRequirement] = []
    for item in raw_frs:
        fr_id = item.get("id", f"FR-{len(fr_objects)+1}")
        desc = item.get("description", "")
        title = item.get("title") or synthesise_fr_title(desc)
        evidences = [
            SourceEvidence(speaker=e.get("speaker", "Client"), statement=e.get("statement", ""))
            for e in item.get("source_evidence", [])
        ]
        fr_objects.append(FunctionalRequirement(
            id=fr_id,
            title=title,
            description=desc,
            source_evidence=evidences
        ))

    raw_nfrs = reqs_raw.get("non_functional_requirements", [])
    if isinstance(reqs_raw.get("specified_requirements"), dict):
        raw_nfrs = reqs_raw["specified_requirements"].get("non_functional", raw_nfrs)

    nfr_objects: List[NonFunctionalRequirement] = []
    for item in raw_nfrs:
        nfr_id = item.get("id", f"NFR-{len(nfr_objects)+1}")
        desc = item.get("description") or item.get("target") or ""
        raw_iso = item.get("iso_characteristic") or TYPE_MAP.get(item.get("type"), "") or classify_iso25010(desc)
        iso_char = TYPE_MAP.get(raw_iso, raw_iso)
        evidences = [
            SourceEvidence(speaker=e.get("speaker", "Client"), statement=e.get("statement", ""))
            for e in item.get("source_evidence", [])
        ]
        nfr_objects.append(NonFunctionalRequirement(
            id=nfr_id,
            description=desc,
            iso_characteristic=iso_char,
            source_evidence=evidences
        ))

    return RequirementsPackage(
        schema_version="1.0",
        job_id=job_id,
        tenant_id=tenant_id,
        project_name=project_name,
        purpose=reqs_raw.get("purpose", ""),
        scope=reqs_raw.get("scope", ""),
        functional_requirements=fr_objects,
        non_functional_requirements=nfr_objects,
        design_constraints=_to_str_list(reqs_raw.get("design_constraints", [])),
        external_interfaces=_to_str_list(reqs_raw.get("external_interfaces", [])),
        standards_compliance=_to_str_list(reqs_raw.get("standards_compliance", [])),
        assumptions_and_dependencies=_to_str_list(reqs_raw.get("assumptions_and_dependencies", [])),
        user_characteristics=_to_str_list(reqs_raw.get("user_characteristics", [])),
    )

