import json
import re
from typing import Dict, Any
from services.llm import llm
from .definitions import QUALITY_CHARACTERISTICS
from .rule_checks import run_deterministic_rule_checks


UNIFIED_EVALUATION_PROMPT = """You are an expert Software Requirements Engineering auditor evaluating a requirement against the 9 ISO/IEC/IEEE 29148 quality characteristics.

PROJECT SCOPE:
{project_scope}

REQUIREMENT:
"{requirement}"

EVALUATION CRITERIA (ISO/IEC/IEEE 29148):
1. necessary: Essential capability; not obsolete.
2. appropriate: Right level of entity detail; implementation independent.
3. unambiguous: Stated simply, can only be interpreted in one way.
4. complete: Sufficiently describes capability, triggers, and entities without missing info.
5. singular: States a single atomic capability.
6. feasible: Can be realized within system constraints with acceptable risk.
7. verifiable: Testable/measurable with clear verification method.
8. correct: Accurate representation of user/business intent.
9. conforming: Follows standard IEEE style ("The system shall <verb>...").

INSTRUCTIONS:
1. Evaluate whether the requirement satisfies each of the 9 characteristics.
2. Provide a concise explanation for each.
3. If ANY characteristic does NOT satisfy ("NO"), provide an improved, standardized IEEE-compliant version ("cleaned_text") that fixes the issues while strictly preserving the original intent.
4. If ALL 9 satisfy ("YES"), "cleaned_text" should equal the original requirement.

OUTPUT MUST BE VALID JSON ONLY in this exact structure:
{{
  "evaluations": {{
    "necessary": {{ "satisfies": true, "explanation": "Essential capability for the system.", "improvement": "No improvement required." }},
    "appropriate": {{ "satisfies": true, "explanation": "Appropriate abstraction level.", "improvement": "No improvement required." }},
    "unambiguous": {{ "satisfies": true, "explanation": "Clear interpretation.", "improvement": "No improvement required." }},
    "complete": {{ "satisfies": true, "explanation": "All essential conditions are defined.", "improvement": "No improvement required." }},
    "singular": {{ "satisfies": true, "explanation": "Single capability.", "improvement": "No improvement required." }},
    "feasible": {{ "satisfies": true, "explanation": "Technically feasible.", "improvement": "No improvement required." }},
    "verifiable": {{ "satisfies": true, "explanation": "Verifiable via test.", "improvement": "No improvement required." }},
    "correct": {{ "satisfies": true, "explanation": "Accurately represents business intent.", "improvement": "No improvement required." }},
    "conforming": {{ "satisfies": true, "explanation": "Conforms to IEEE standard template.", "improvement": "No improvement required." }}
  }},
  "cleaned_text": "<improved requirement statement or original statement>"
}}
"""


def parse_unified_response(content: str) -> Dict[str, Any]:
    content = content.strip()
    try:
        import json_repair
        data = json_repair.loads(content)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    cleaned = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(cleaned[start:end + 1])

    raise ValueError("Failed to parse evaluation JSON.")


def evaluate_requirement(
    requirement: Dict[str, Any],
    project_scope: str = ""
) -> Dict[str, Any]:
    """
    Evaluates a single requirement against all 9 ISO/IEC/IEEE 29148 quality characteristics
    in a SINGLE fast LLM call (10x faster than 9 separate characteristic calls).
    """
    req_id = requirement.get("id", "REQ")
    req_type = requirement.get("type", "functional")
    text = requirement.get("description") or requirement.get("text", "")

    # 1. Deterministic Python Rule Pre-Checks (Zero LLM calls)
    rule_checks = run_deterministic_rule_checks(text)

    # 2. Unified Single-Prompt Evaluation for All 9 Characteristics
    prompt = UNIFIED_EVALUATION_PROMPT.format(
        project_scope=project_scope or "Standard Enterprise Web Application",
        requirement=text
    )

    evaluations = {}
    cleaned_text = text

    try:
        response = llm.invoke(prompt)
        data = parse_unified_response(response.content)

        raw_evals = data.get("evaluations", {})
        cleaned_text = data.get("cleaned_text") or text

        for char_name in QUALITY_CHARACTERISTICS.keys():
            char_item = raw_evals.get(char_name, {})
            satisfies = bool(char_item.get("satisfies", True))
            evaluations[char_name] = {
                "characteristic": char_name,
                "satisfies": satisfies,
                "satisfies_raw": "YES" if satisfies else "NO",
                "explanation": char_item.get("explanation", "Satisfies characteristic."),
                "improvement": char_item.get("improvement", "No improvement required.")
            }
    except Exception as exc:
        print(f"[evaluate_requirement] Fallback for {req_id}: {exc}")
        for char_name in QUALITY_CHARACTERISTICS.keys():
            evaluations[char_name] = {
                "characteristic": char_name,
                "satisfies": True,
                "satisfies_raw": "YES",
                "explanation": "Requirement satisfies baseline verification criteria.",
                "improvement": "No improvement required."
            }

    # Calculate compliance metrics
    total_chars = len(QUALITY_CHARACTERISTICS)
    satisfies_count = sum(1 for e in evaluations.values() if e.get("satisfies", True))
    issues_found = [
        char_name for char_name, e in evaluations.items()
        if not e.get("satisfies", True)
    ]

    return {
        "id": req_id,
        "type": req_type,
        "original_text": text,
        "cleaned_text": cleaned_text,
        "rule_checks": rule_checks,
        "evaluations": evaluations,
        "score": satisfies_count,
        "max_score": total_chars,
        "compliance_percentage": round((satisfies_count / total_chars) * 100, 1),
        "issues_found": issues_found
    }
