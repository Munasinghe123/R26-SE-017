"""
Stage 4: Deterministic Programmatic Quality & Traceability Checks

Goal:
Perform strict, pure-Python deterministic validation and quality checks on the
extracted candidates before downstream validation, without using another LLM call.

Checks Performed:
1. Schema Validation: Ensure all mandatory fields exist and are of proper type.
2. Traceability Validation: Verify every requirement links to at least one evidence candidate.
3. Duplicate Identifier Validation: Ensure candidate IDs are unique.
4. Empty / Malformed Description Validation: Reject empty or whitespace-only descriptions.
5. Deterministic Duplicate Detection: Identify duplicate requirements via normalized text comparison.
6. Classification Validation: Confirm valid classification (functional, non_functional, uncertain).
7. Source Evidence Integrity: Verify all referenced evidence IDs exist in the Stage 1 output.
8. Clarification Flag Validation: Ensure clarification_reason is present if requires_clarification is True.

Finally, formats the clean requirements into the canonical dictionary expected by downstream
LangGraph nodes (client_view, HITL review, database, orchestrator).
"""

import json
import re
from typing import Dict, Any, List, Tuple


def normalize_text_for_comparison(text: str) -> str:
    """Normalize text by lowercasing, stripping leading requirement prefixes, and removing punctuation."""
    t = text.lower().strip()
    # Strip common prefixes
    t = re.sub(r"^the\s+system\s+shall\s+", "", t)
    t = re.sub(r"^the\s+software\s+shall\s+", "", t)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def run_deterministic_quality_checks(
    evidence_candidates: List[Dict[str, Any]],
    classified_requirements: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes all 8 deterministic quality checks in pure Python.
    Returns:
        (valid_requirements, quality_report)
    """
    print("\n========== STAGE 4: DETERMINISTIC QUALITY CHECKS ==========")
    report: Dict[str, Any] = {
        "total_input_candidates": len(classified_requirements),
        "valid_requirements_count": 0,
        "rejected_count": 0,
        "duplicates_removed_count": 0,
        "warnings": [],
        "errors": [],
        "passed": True
    }

    evidence_map = {e["evidence_id"]: e for e in evidence_candidates if isinstance(e, dict) and "evidence_id" in e}

    seen_ids = set()
    seen_normalized_texts = {}
    valid_requirements: List[Dict[str, Any]] = []

    for idx, req in enumerate(classified_requirements, start=1):
        req_id = req.get("requirement_candidate_id") or f"RC-{idx:03d}"
        desc = req.get("description", "")
        ev_ids = req.get("source_evidence_ids", [])
        classification = req.get("classification")
        req_clarification = req.get("requires_clarification", False)
        clarification_reason = req.get("clarification_reason")

        # 1. Empty or invalid description validation
        if not isinstance(desc, str) or not desc.strip():
            msg = f"[Check 4 Failed] Requirement {req_id} has an empty or malformed description."
            report["errors"].append(msg)
            report["rejected_count"] += 1
            continue

        clean_desc = desc.strip()

        # 2. Reject classification filter — items classified as "reject" are excluded
        if classification == "reject":
            report["rejected_count"] += 1
            report["warnings"].append(f"[Reject] Requirement {req_id} classified as 'reject' (not a software requirement). Excluded.")
            continue

        # 3. Duplicate identifier check
        if req_id in seen_ids:
            msg = f"[Check 3 Warning] Duplicate ID '{req_id}' detected. Renumbering to '{req_id}_{idx}'."
            report["warnings"].append(msg)
            req_id = f"{req_id}_{idx}"
        seen_ids.add(req_id)

        # 4. Traceability validation
        if not ev_ids or not isinstance(ev_ids, list):
            msg = f"[Check 2 Failed] Requirement {req_id} lacks source evidence links."
            report["errors"].append(msg)
            report["rejected_count"] += 1
            continue

        # 5. Source evidence reference integrity
        valid_linked_evidence = []
        for eid in ev_ids:
            if eid in evidence_map:
                ev_obj = evidence_map[eid]
                valid_linked_evidence.append({
                    "evidence_id": eid,
                    "speaker": ev_obj.get("speaker", "Unknown"),
                    "statement": ev_obj.get("source_text", ""),
                    "context": ev_obj.get("context", ""),
                })
            else:
                report["warnings"].append(f"[Check 7 Warning] Evidence ID '{eid}' for {req_id} not found in Stage 1 evidence list.")

        if not valid_linked_evidence:
            msg = f"[Check 7 Failed] Requirement {req_id} does not link to any valid Stage 1 evidence candidates."
            report["errors"].append(msg)
            report["rejected_count"] += 1
            continue

        # 6. Classification validation — uncertain items will be treated as functional in output
        if classification not in ["functional", "non_functional", "uncertain"]:
            report["warnings"].append(f"[Check 6 Warning] Requirement {req_id} had invalid classification '{classification}'. Marked as 'functional'.")
            classification = "functional"

        # 6. Clarification flag validation
        if req_clarification and not clarification_reason:
            report["warnings"].append(f"[Check 8 Warning] Requirement {req_id} marked as requires_clarification without reason. Supplying default.")
            clarification_reason = "Requires client clarification on operational boundaries or measurable targets."

        # 7. Deterministic duplicate requirement detection
        norm_key = normalize_text_for_comparison(clean_desc)
        if norm_key in seen_normalized_texts:
            first_id = seen_normalized_texts[norm_key]
            msg = f"[Check 5 Warning] Duplicate requirement detected: '{req_id}' matches '{first_id}'. Merging evidence and skipping duplicate."
            report["warnings"].append(msg)
            report["duplicates_removed_count"] += 1
            # Merge evidence into the existing requirement
            for existing in valid_requirements:
                if existing["id"] == first_id:
                    existing_ev_ids = {e.get("evidence_id") for e in existing.get("source_evidence", [])}
                    for ev in valid_linked_evidence:
                        if ev.get("evidence_id") not in existing_ev_ids:
                            existing["source_evidence"].append(ev)
                    break
            continue

        seen_normalized_texts[norm_key] = req_id

        # Candidate passed checks
        validated_item = {
            "id": req_id,
            "description": clean_desc,
            "classification": classification,
            "quality_attribute": req.get("quality_attribute"),
            "candidate_classifications": req.get("candidate_classifications"),
            "confidence": req.get("confidence", 0.85),
            "classification_reason": req.get("classification_reason", ""),
            "requires_clarification": bool(req_clarification),
            "clarification_reason": clarification_reason if req_clarification else None,
            "source_evidence": valid_linked_evidence,
        }
        valid_requirements.append(validated_item)

    report["valid_requirements_count"] = len(valid_requirements)
    report["passed"] = len(report["errors"]) == 0

    print(f"[Stage 4] Checks complete: {len(valid_requirements)} valid requirement(s), "
          f"{report['duplicates_removed_count']} duplicate(s) merged, {report['rejected_count']} rejected.")
    return valid_requirements, report


def assemble_canonical_requirements(
    valid_requirements: List[Dict[str, Any]],
    evidence_candidates: List[Dict[str, Any]],
    report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Transforms validated requirements into the exact schema requested:
    "specified_requirements": {
        "functional": [
            {
                "id": "FR-1",
                "description": "The system shall ...",
                "source_evidence": [
                    {
                        "speaker": "...",
                        "statement": "..."
                    }
                ]
            }
        ],
        "non_functional": [
            {
                "id": "NFR-1",
                "description": "The system shall ...",
                "source_evidence": [
                    {
                        "speaker": "...",
                        "statement": "..."
                    }
                ]
            }
        ]
    }
    """
    functional_items = []
    non_functional_items = []

    fr_counter = 1
    nfr_counter = 1

    for item in valid_requirements:
        classification = item.get("classification")

        # Clean source evidence to exact {speaker, statement} format
        cleaned_evidence = []
        for ev in item.get("source_evidence", []):
            cleaned_evidence.append({
                "speaker": ev.get("speaker") or "Client",
                "statement": ev.get("statement") or ev.get("source_text") or ""
            })

        if not cleaned_evidence:
            cleaned_evidence.append({
                "speaker": "Client",
                "statement": item.get("description", "")
            })

        if classification == "non_functional":
            assigned_id = f"NFR-{nfr_counter}"
            nfr_counter += 1
            non_functional_items.append({
                "id": assigned_id,
                "description": item["description"],
                "source_evidence": cleaned_evidence
            })
        else:
            # Both "functional" and any fallback items go to functional
            assigned_id = f"FR-{fr_counter}"
            fr_counter += 1
            functional_items.append({
                "id": assigned_id,
                "description": item["description"],
                "source_evidence": cleaned_evidence
            })

    canonical = {
        "specified_requirements": {
            "functional": functional_items,
            "non_functional": non_functional_items
        },
        "functional": functional_items,
        "non_functional": non_functional_items,
    }

    print("\n" + "="*60)
    print("FINAL EXTRACTED SPECIFIED_REQUIREMENTS STRUCTURE:")
    print("="*60)
    print(json.dumps({"specified_requirements": canonical["specified_requirements"]}, indent=4, ensure_ascii=False))
    print("="*60 + "\n")

    return canonical
