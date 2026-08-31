from typing import Dict, Any, List
from .compound_detector import detect_compound_requirement


def run_deterministic_rule_checks(requirement_text: str) -> Dict[str, Any]:
    """
    Runs deterministic Python rule-based checks on a requirement statement.
    NO LLM CALLS.

    Checks:
    1. Atomicity / Compound Requirement Detection
    """
    compound_res = detect_compound_requirement(requirement_text)

    has_compound_warning = compound_res.get("status") == "warning"
    overall_status = "warning" if has_compound_warning else "passed"

    findings = []
    if has_compound_warning:
        findings.append({
            "type": "COMPOUND_WARNING",
            "rule": compound_res.get("rule"),
            "message": compound_res.get("message"),
            "evidence": compound_res.get("evidence", []),
            "detected_actions": compound_res.get("detected_actions", [])
        })

    return {
        "text": requirement_text,
        "overall_status": overall_status,
        "compound_check": compound_res,
        "findings": findings
    }


def run_rule_checks_suite(requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs deterministic rule checks across a list of requirement dicts.
    """
    results = []
    for req in requirements:
        req_id = req.get("id", "REQ")
        text = req.get("description") or req.get("text", "")
        req_type = req.get("type", "functional")

        rule_res = run_deterministic_rule_checks(text)
        results.append({
            "id": req_id,
            "type": req_type,
            **rule_res
        })
    return results
