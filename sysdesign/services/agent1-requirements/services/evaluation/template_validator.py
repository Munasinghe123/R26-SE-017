import re
from typing import Dict, Any, List

# Standard accepted subjects and modals
APPROVED_PREFIXES = [
    r"the\s+system\s+shall",
    r"the\s+platform\s+shall",
    r"the\s+software\s+shall",
    r"the\s+application\s+shall",
    r"the\s+service\s+shall"
]

WEAK_MODALS = ["should", "can", "could", "may", "might", "will", "must"]


def validate_requirement_structure(requirement_text: str) -> Dict[str, Any]:
    """
    Python rule-based validation for requirement structure & standard IEEE template.
    Template: The system shall + <action_verb> + <object/details> + [condition]

    NO LLM CALLS.
    """
    text = (requirement_text or "").strip()
    if not text:
        return {
            "rule": "REQUIREMENT_STRUCTURE_VALIDATION",
            "status": "failed",
            "valid_template": False,
            "message": "Requirement is empty."
        }

    # 1. Check for standard prefix: "The system shall"
    prefix_matched = None
    for prefix_pat in APPROVED_PREFIXES:
        match = re.match(r"^(" + prefix_pat + r")\s+(.*)", text, re.IGNORECASE)
        if match:
            prefix_matched = match.group(1)
            remainder = match.group(2).strip()
            break

    if not prefix_matched:
        # Check if weak modals were used instead
        weak_found = []
        for wm in WEAK_MODALS:
            if re.search(r"\b" + wm + r"\b", text, re.IGNORECASE):
                weak_found.append(wm)

        msg = "Does not follow the standard defined structure ('The system shall <action> <object>')."
        if weak_found:
            msg += f" Found non-standard modal verbs: {', '.join(weak_found)}."

        return {
            "rule": "REQUIREMENT_STRUCTURE_VALIDATION",
            "status": "failed",
            "valid_template": False,
            "prefix": None,
            "action_clause": None,
            "evidence": weak_found,
            "message": msg
        }

    # 2. Check if an action verb immediately follows the modal
    # Example action verbs or patterns like "allow", "provide", "display", "process", "authenticate", etc.
    words = remainder.split()
    if not words:
        return {
            "rule": "REQUIREMENT_STRUCTURE_VALIDATION",
            "status": "failed",
            "valid_template": False,
            "prefix": prefix_matched,
            "action_clause": None,
            "message": "Requirement has prefix but lacks an action verb or capability description."
        }

    # Extract action clause and check for minimum viable length
    action_verb = words[0].lower()
    if len(words) < 3:
        return {
            "rule": "REQUIREMENT_STRUCTURE_VALIDATION",
            "status": "failed",
            "valid_template": False,
            "prefix": prefix_matched,
            "action_clause": remainder,
            "message": "Requirement statement is too brief to form a complete functional specification."
        }

    return {
        "rule": "REQUIREMENT_STRUCTURE_VALIDATION",
        "status": "passed",
        "valid_template": True,
        "prefix": prefix_matched,
        "action_verb": action_verb,
        "action_clause": remainder,
        "message": "Valid requirement structure conforming to standard template."
    }
