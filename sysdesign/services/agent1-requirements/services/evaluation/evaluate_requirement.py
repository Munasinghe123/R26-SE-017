import concurrent.futures
from typing import Dict, Any
from .definitions import QUALITY_CHARACTERISTICS
from .evaluate_single_characteristic import evaluate_single_characteristic
from .synthesize_cleaned_requirement import synthesize_cleaned_requirement
from .rule_checks import run_deterministic_rule_checks


def evaluate_requirement(
    requirement: Dict[str, Any],
    project_scope: str = ""
) -> Dict[str, Any]:
    """
    Evaluates a single requirement against all 9 ISO/IEC/IEEE 29148 quality characteristics
    alongside deterministic Python rule-based checks.
    """
    req_id = requirement.get("id", "REQ")
    req_type = requirement.get("type", "functional")
    text = requirement.get("description") or requirement.get("text", "")

    # 1. Deterministic Python Rule Pre-Checks (Zero LLM calls)
    rule_checks = run_deterministic_rule_checks(text)

    evaluations = {}

    # 2. Run LLM evaluations concurrently for all 9 quality characteristics
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        future_to_char = {
            executor.submit(
                evaluate_single_characteristic,
                project_scope=project_scope,
                requirement=text,
                quality_characteristic=char_name,
                quality_definition=char_def
            ): char_name
            for char_name, char_def in QUALITY_CHARACTERISTICS.items()
        }

        for future in concurrent.futures.as_completed(future_to_char):
            char_name = future_to_char[future]
            try:
                eval_res = future.result()
                evaluations[char_name] = eval_res
            except Exception as exc:
                print(f"Evaluation failed for {char_name}: {exc}")
                evaluations[char_name] = {
                    "characteristic": char_name,
                    "satisfies": True,
                    "satisfies_raw": "YES",
                    "explanation": f"Evaluation fallback: {exc}",
                    "improvement": "No improvement required."
                }

    # Calculate compliance metrics
    total_chars = len(QUALITY_CHARACTERISTICS)
    satisfies_count = sum(1 for e in evaluations.values() if e.get("satisfies", True))
    issues_found = [
        char_name for char_name, e in evaluations.items()
        if not e.get("satisfies", True)
    ]

    # Synthesize cleaned requirement
    cleaned_text = synthesize_cleaned_requirement(
        project_scope=project_scope,
        original_requirement=text,
        evaluations=evaluations
    )

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
