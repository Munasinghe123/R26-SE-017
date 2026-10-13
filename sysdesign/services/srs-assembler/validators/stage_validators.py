from __future__ import annotations

import re
from typing import Any

SHALL_MODAL_RE = re.compile(r"\b(shall|must)\b", re.IGNORECASE)
VAGUE_QUALITATIVE_RE = re.compile(
    r"\b(fast|scalable|robust|user-friendly|intuitive|quick|efficient|seamless)\b",
    re.IGNORECASE,
)

VALID_ISO_25010_CHARACTERISTICS = {
    "functional_suitability",
    "performance_efficiency",
    "compatibility",
    "usability",
    "reliability",
    "security",
    "maintainability",
    "portability",
}

VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_VERIFICATION_METHODS = {"Test", "Inspection", "Demonstration", "Analysis"}


def _result(
    errors: list[dict],
    warnings: list[dict],
    total_checks: int,
    stage: str,
) -> dict:
    passed = len(errors) == 0
    return {
        "passed": passed,
        "valid": passed,
        "stage": stage,
        "errors": errors,
        "warnings": warnings,
        "total_checks": total_checks,
        "passed_checks": max(total_checks - len(errors), 0),
    }


def _error(
    rule_id: str,
    message: str,
    severity: str = "high",
    *,
    code: str | None = None,
    path: str = "",
    details: dict | None = None,
) -> dict:
    return {
        "rule_id": rule_id,
        "code": code or rule_id,
        "severity": severity,
        "path": path,
        "message": message,
        "details": details or {},
    }


def _warning(
    rule_id: str,
    message: str,
    *,
    code: str | None = None,
    path: str = "",
    details: dict | None = None,
) -> dict:
    return {
        "rule_id": rule_id,
        "code": code or rule_id,
        "severity": "warning",
        "path": path,
        "message": message,
        "details": details or {},
    }


def validate_overview_section(overview: dict | None) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    if not isinstance(overview, dict):
        errors.append(_error("OVERVIEW-TYPE", "Overview section must be a JSON object.", "critical", path="overview"))
        return _result(errors, warnings, 1, "overview")

    # Purpose check
    total_checks += 1
    purpose = str(overview.get("purpose", "")).strip()
    if not purpose or len(purpose) < 20:
        errors.append(_error(
            "OVERVIEW-PURPOSE",
            "System purpose statement must be defined and sufficiently descriptive (>20 chars).",
            path="purpose"
        ))

    # Scope check
    total_checks += 1
    scope = str(overview.get("scope", "")).strip()
    if not scope or len(scope) < 20:
        errors.append(_error(
            "OVERVIEW-SCOPE",
            "System scope statement must clearly define system boundaries and objectives.",
            path="scope"
        ))

    # Product perspective check
    total_checks += 1
    perspective = str(overview.get("product_perspective", "")).strip()
    if not perspective:
        warnings.append(_warning(
            "OVERVIEW-PERSPECTIVE",
            "Product perspective is empty; recommend specifying system context or interfaces.",
            path="product_perspective"
        ))

    # User characteristics check
    total_checks += 1
    users = overview.get("user_characteristics", [])
    if not isinstance(users, list) or len(users) == 0:
        errors.append(_error(
            "OVERVIEW-USERS",
            "user_characteristics must contain at least one target user persona or stakeholder group.",
            path="user_characteristics"
        ))

    # External interfaces check (optional, but must be a list if present)
    if "external_interfaces" in overview and overview["external_interfaces"] is not None:
        total_checks += 1
        if not isinstance(overview["external_interfaces"], list):
            errors.append(_error(
                "OVERVIEW-INTERFACES",
                "external_interfaces must be a list of external system or API interface specifications.",
                path="external_interfaces"
            ))

    # Acronyms and glossary check (optional, but must be a list if present)
    if "acronyms_and_glossary" in overview and overview["acronyms_and_glossary"] is not None:
        total_checks += 1
        if not isinstance(overview["acronyms_and_glossary"], list):
            errors.append(_error(
                "OVERVIEW-GLOSSARY",
                "acronyms_and_glossary must be a list of term definitions.",
                path="acronyms_and_glossary"
            ))

    # Standards compliance check (optional, but must be a list if present)
    if "standards_compliance" in overview and overview["standards_compliance"] is not None:
        total_checks += 1
        if not isinstance(overview["standards_compliance"], list):
            errors.append(_error(
                "OVERVIEW-STANDARDS",
                "standards_compliance must be a list of regulatory and engineering standards.",
                path="standards_compliance"
            ))

    return _result(errors, warnings, total_checks, "overview")


def validate_functional_requirements(
    functional_specs: list[dict] | None,
    input_requirement_ids: list[str] | None = None,
) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    specs = functional_specs or []
    if not isinstance(specs, list):
        errors.append(_error("FR-STRUCTURE", "Functional requirements must be a list.", "critical", path="functional"))
        return _result(errors, warnings, 1, "functional")

    expected_ids = set(input_requirement_ids or [])
    observed_ids = set()

    for idx, fr in enumerate(specs):
        total_checks += 1
        if not isinstance(fr, dict):
            errors.append(_error("FR-OBJECT", f"Requirement at index {idx} must be a dictionary.", path=f"functional[{idx}]"))
            continue

        req_id = str(fr.get("id", "")).strip()
        title = str(fr.get("title", "")).strip()
        statement = str(fr.get("statement", fr.get("description", ""))).strip()
        priority = str(fr.get("priority", "Medium")).strip().capitalize()
        criteria = fr.get("acceptance_criteria", [])

        if not req_id:
            errors.append(_error("FR-ID-MISSING", f"Requirement at index {idx} is missing an ID.", path=f"functional[{idx}].id"))
        else:
            observed_ids.add(req_id)

        if not title:
            warnings.append(_warning("FR-TITLE-EMPTY", f"Requirement '{req_id}' has an empty title.", path=f"functional[{idx}].title"))

        # IEEE 29148 Normative Phrasing: Must contain 'shall' or 'must'
        if not statement or not SHALL_MODAL_RE.search(statement):
            errors.append(_error(
                "FR-NORMATIVE-PHRASING",
                f"Requirement '{req_id}' must use normative standard phrasing (e.g., 'The system shall...').",
                path=f"functional[{idx}].statement",
                details={"statement": statement}
            ))

        # Acceptance Criteria check
        if not isinstance(criteria, list) or len(criteria) == 0:
            errors.append(_error(
                "FR-ACCEPTANCE-CRITERIA",
                f"Requirement '{req_id}' must specify at least one verifiable acceptance criterion.",
                path=f"functional[{idx}].acceptance_criteria"
            ))

        # Priority Check
        if priority not in VALID_PRIORITIES:
            warnings.append(_warning(
                "FR-PRIORITY",
                f"Requirement '{req_id}' priority '{priority}' is non-standard. Expected: High, Medium, or Low.",
                path=f"functional[{idx}].priority"
            ))

    # Requirement Preservation Check (No dropped inputs)
    if expected_ids:
        missing_ids = expected_ids - observed_ids
        if missing_ids:
            errors.append(_error(
                "FR-PRESERVATION-DROPPED",
                f"The following input requirement IDs were omitted from the formal specification: {sorted(missing_ids)}",
                "critical",
                path="functional",
                details={"missing_ids": sorted(missing_ids)}
            ))

    return _result(errors, warnings, total_checks, "functional")


def validate_non_functional_requirements(
    non_functional_specs: list[dict] | None,
    input_nfr_ids: list[str] | None = None,
) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    specs = non_functional_specs or []
    if not isinstance(specs, list):
        errors.append(_error("NFR-STRUCTURE", "Non-functional requirements must be a list.", "critical", path="non_functional"))
        return _result(errors, warnings, 1, "non_functional")

    expected_ids = set(input_nfr_ids or [])
    observed_ids = set()

    for idx, nfr in enumerate(specs):
        total_checks += 1
        if not isinstance(nfr, dict):
            errors.append(_error("NFR-OBJECT", f"NFR at index {idx} must be a dictionary.", path=f"non_functional[{idx}]"))
            continue

        req_id = str(nfr.get("id", "")).strip()
        iso_cat = str(nfr.get("iso_characteristic", "")).strip().lower()
        desc = str(nfr.get("description", "")).strip()
        metric = str(nfr.get("target_metric", "")).strip()

        if not req_id:
            errors.append(_error("NFR-ID-MISSING", f"NFR at index {idx} is missing an ID.", path=f"non_functional[{idx}].id"))
        else:
            observed_ids.add(req_id)

        # ISO 25010 Taxonomy Check
        if not iso_cat or iso_cat not in VALID_ISO_25010_CHARACTERISTICS:
            errors.append(_error(
                "NFR-ISO-CHARACTERISTIC",
                f"NFR '{req_id}' has invalid ISO/IEC 25010 category '{iso_cat}'. Valid: {sorted(VALID_ISO_25010_CHARACTERISTICS)}",
                path=f"non_functional[{idx}].iso_characteristic",
                details={"iso_characteristic": iso_cat}
            ))

        # Quantifiability Check (Metric should be defined)
        if not metric:
            if VAGUE_QUALITATIVE_RE.search(desc):
                errors.append(_error(
                    "NFR-UNMEASURABLE-SPEC",
                    f"NFR '{req_id}' uses subjective terms without defining a measurable 'target_metric'.",
                    path=f"non_functional[{idx}].target_metric",
                    details={"description": desc}
                ))
            else:
                warnings.append(_warning(
                    "NFR-METRIC-RECOMMENDED",
                    f"NFR '{req_id}' does not have a formal target metric.",
                    path=f"non_functional[{idx}].target_metric"
                ))

    if expected_ids:
        missing_ids = expected_ids - observed_ids
        if missing_ids:
            errors.append(_error(
                "NFR-PRESERVATION-DROPPED",
                f"The following input NFR IDs were omitted from specification: {sorted(missing_ids)}",
                "critical",
                path="non_functional",
                details={"missing_ids": sorted(missing_ids)}
            ))

    return _result(errors, warnings, total_checks, "non_functional")


def validate_traceability_matrix(
    traceability_matrix: list[dict] | None,
    functional_ids: list[str] | None = None,
) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    total_checks = 0

    matrix = traceability_matrix or []
    if not isinstance(matrix, list):
        errors.append(_error("RTM-STRUCTURE", "Traceability matrix must be a list.", "critical", path="traceability"))
        return _result(errors, warnings, 1, "traceability")

    expected_ids = set(functional_ids or [])
    mapped_ids = set()

    for idx, item in enumerate(matrix):
        total_checks += 1
        if not isinstance(item, dict):
            errors.append(_error("RTM-ITEM", f"RTM row at index {idx} must be a dictionary.", path=f"traceability[{idx}]"))
            continue

        req_id = str(item.get("requirement_id", "")).strip()
        comp = str(item.get("allocated_component", "")).strip()
        v_method = str(item.get("verification_method", "Test")).strip().capitalize()

        if not req_id:
            errors.append(_error("RTM-REQ-ID", f"RTM row {idx} is missing requirement_id.", path=f"traceability[{idx}].requirement_id"))
        else:
            mapped_ids.add(req_id)

        if not comp:
            errors.append(_error("RTM-COMPONENT", f"Requirement '{req_id}' has no allocated architectural component.", path=f"traceability[{idx}].allocated_component"))

        if v_method not in VALID_VERIFICATION_METHODS:
            warnings.append(_warning(
                "RTM-VERIFICATION-METHOD",
                f"Verification method '{v_method}' is non-standard. Standard: {sorted(VALID_VERIFICATION_METHODS)}",
                path=f"traceability[{idx}].verification_method"
            ))

    if expected_ids:
        unmapped = expected_ids - mapped_ids
        if unmapped:
            errors.append(_error(
                "RTM-COVERAGE-INCOMPLETE",
                f"Traceability matrix lacks coverage for requirements: {sorted(unmapped)}",
                "high",
                path="traceability",
                details={"unmapped_ids": sorted(unmapped)}
            ))

    return _result(errors, warnings, total_checks, "traceability")
