import concurrent.futures
from typing import Dict, Any, List
from .evaluate_requirement import evaluate_requirement
from .definitions import QUALITY_CHARACTERISTICS


def extract_requirements_list(requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts all functional and non-functional requirements into a flat list.
    """
    req_list = []
    
    # 1. Check sections (from final_requirements format)
    if "sections" in requirements and isinstance(requirements["sections"], list):
        for section in requirements["sections"]:
            stitle = section.get("title", "").lower()
            rtype = "non_functional" if "non" in stitle else "functional"
            for item in section.get("items", []):
                req_list.append({
                    "id": item.get("id", "REQ"),
                    "type": item.get("type", rtype),
                    "description": item.get("text") or item.get("description", "")
                })
        if req_list:
            return req_list

    # 2. Check specified_requirements dict
    spec = requirements.get("specified_requirements", {})
    if isinstance(spec, dict):
        for f in spec.get("functional", []):
            req_list.append({
                "id": f.get("id", "FR"),
                "type": "functional",
                "description": f.get("description") or f.get("text", "")
            })
        for nf in spec.get("non_functional", []):
            req_list.append({
                "id": nf.get("id", "NFR"),
                "type": "non_functional",
                "description": nf.get("description") or nf.get("text", "")
            })
        if req_list:
            return req_list

    # 3. Direct functional / non_functional keys
    for f in requirements.get("functional", []):
        req_list.append({
            "id": f.get("id", "FR") if isinstance(f, dict) else "FR",
            "type": "functional",
            "description": f.get("description") or f.get("text", "") if isinstance(f, dict) else str(f)
        })
    for nf in requirements.get("non_functional", []):
        req_list.append({
            "id": nf.get("id", "NFR") if isinstance(nf, dict) else "NFR",
            "type": "non_functional",
            "description": nf.get("description") or nf.get("text", "") if isinstance(nf, dict) else str(nf)
        })

    return req_list


def evaluate_requirements_suite(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates the full set of requirements against the 9 ISO/IEC/IEEE 29148 quality characteristics.

    Returns:
    {
        "cleaned_requirements": {
            "purpose": str,
            "scope": str,
            "specified_requirements": {
                "functional": [...],
                "non_functional": [...]
            },
            "functional": [...],
            "non_functional": [...]
        },
        "quality_report": {
            "summary": {
                "total_requirements": int,
                "overall_quality_score": float, # 0 - 100%
                "passed_all_characteristics": int,
                "needs_improvement": int,
                "characteristic_pass_rates": { ... }
            },
            "detailed_evaluations": [ ... ],
            "improvements_applied": [ ... ]
        }
    }
    """
    scope = requirements.get("scope", "")
    purpose = requirements.get("purpose", "")

    flat_reqs = extract_requirements_list(requirements)
    if not flat_reqs:
        return {
            "cleaned_requirements": requirements,
            "quality_report": {
                "summary": {
                    "total_requirements": 0,
                    "overall_quality_score": 100.0,
                    "passed_all_characteristics": 0,
                    "needs_improvement": 0,
                    "characteristic_pass_rates": {}
                },
                "detailed_evaluations": [],
                "improvements_applied": []
            }
        }

    print(f"\n========== EVALUATING {len(flat_reqs)} REQUIREMENTS AGAINST 9 QUALITY CHARACTERISTICS ==========")

    detailed_evaluations = []
    cleaned_functional = []
    cleaned_non_functional = []
    improvements_applied = []

    # Evaluate all requirements
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_req = {
            executor.submit(evaluate_requirement, req, project_scope=scope): req
            for req in flat_reqs
        }

        for future in concurrent.futures.as_completed(future_to_req):
            eval_result = future.result()
            detailed_evaluations.append(eval_result)

            # Build cleaned requirements
            cleaned_item = {
                "id": eval_result["id"],
                "description": eval_result["cleaned_text"],
                "type": eval_result["type"],
                "quality_score": eval_result["compliance_percentage"]
            }

            if eval_result["type"] == "non_functional":
                cleaned_non_functional.append(cleaned_item)
            else:
                cleaned_functional.append(cleaned_item)

            # Record improvements
            if eval_result["issues_found"]:
                improvements_applied.append({
                    "id": eval_result["id"],
                    "original_text": eval_result["original_text"],
                    "improved_text": eval_result["cleaned_text"],
                    "resolved_issues": eval_result["issues_found"]
                })

    # Sort items by original order / ID
    detailed_evaluations.sort(key=lambda x: (x["type"], x["id"]))
    cleaned_functional.sort(key=lambda x: x["id"])
    cleaned_non_functional.sort(key=lambda x: x["id"])

    # Calculate global report metrics
    total_reqs = len(detailed_evaluations)
    total_evals = total_reqs * len(QUALITY_CHARACTERISTICS)
    total_satisfies = sum(e["score"] for e in detailed_evaluations)

    overall_score = round((total_satisfies / total_evals) * 100, 1) if total_evals > 0 else 100.0
    passed_all = sum(1 for e in detailed_evaluations if len(e["issues_found"]) == 0)
    needs_imp = total_reqs - passed_all

    # Characteristic breakdown
    char_pass_counts = {c: 0 for c in QUALITY_CHARACTERISTICS}
    for e in detailed_evaluations:
        for char_name, c_eval in e["evaluations"].items():
            if c_eval.get("satisfies", True):
                char_pass_counts[char_name] += 1

    char_pass_rates = {
        c: round((count / total_reqs) * 100, 1) if total_reqs > 0 else 100.0
        for c, count in char_pass_counts.items()
    }

    quality_report = {
        "summary": {
            "total_requirements": total_reqs,
            "overall_quality_score": overall_score,
            "passed_all_characteristics": passed_all,
            "needs_improvement": needs_imp,
            "characteristic_pass_rates": char_pass_rates
        },
        "detailed_evaluations": detailed_evaluations,
        "improvements_applied": improvements_applied
    }

    cleaned_requirements = {
        **requirements,
        "purpose": purpose,
        "scope": scope,
        "specified_requirements": {
            "functional": cleaned_functional,
            "non_functional": cleaned_non_functional
        },
        "functional": cleaned_functional,
        "non_functional": cleaned_non_functional
    }

    return {
        "cleaned_requirements": cleaned_requirements,
        "quality_report": quality_report
    }
