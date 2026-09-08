import json
import re
from typing import Dict, List, Optional, Tuple


ARBITRATE_CONTRADICTION_PROMPT = """You are a principal software requirements governance arbiter.
Two software requirements in the final specification are in direct contradiction with each other:

Requirement A ({id_a}): "{text_a}"
Requirement B ({id_b}): "{text_b}"

Conflict Context / Reason: {reason}

GOVERNANCE ARBITRATION PRINCIPLES:
1. Active Business Capability / Structured Workflow > Blanket Negative Prohibition (e.g. structured cancellation or refund policy takes precedence over a blanket zero-refund ban).
2. Security, Integrity & Administrative Governance > Unmoderated / Unrestricted Access (e.g. administrator approval requirement takes precedence over unmoderated instant publishing).
3. Specific Defined Capability > Broad Generic Statement.

Determine which requirement should be RETAINED and which should be DROPPED to make the software specification safe and consistent.

Return ONLY valid JSON with this exact structure:
{{
  "keep_id": "{id_a}",
  "drop_id": "{id_b}",
  "rationale": "Clear 1-sentence explanation of why this requirement was selected based on governance principles."
}}
"""


def arbitrate_contradiction(
    id_a: str,
    text_a: str,
    id_b: str,
    text_b: str,
    reason: str
) -> Tuple[str, str, str]:
    """
    Dynamically arbitrates a contradiction between any two requirements using LLM governance reasoning
    with semantic fallback. NO HARDCODED IDS.
    """
    prompt = ARBITRATE_CONTRADICTION_PROMPT.format(
        id_a=id_a,
        text_a=text_a,
        id_b=id_b,
        text_b=text_b,
        reason=reason
    )

    try:
        from services.llm import llm
        response = llm.invoke(prompt)
        content = (response.content or "").strip()

        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL | re.IGNORECASE)
        json_str = match.group(1) if match else content
        start = json_str.find("{")
        end = json_str.rfind("}")
        if start != -1 and end != -1:
            data = json.loads(json_str[start:end + 1])
            keep_id = data.get("keep_id")
            drop_id = data.get("drop_id")
            rationale = data.get("rationale") or "Resolved via software engineering governance principles."

            if keep_id in (id_a, id_b) and drop_id in (id_a, id_b) and keep_id != drop_id:
                return keep_id, drop_id, rationale
    except Exception as exc:
        print(f"[arbitrate_contradiction WARNING] Dynamic LLM arbitration fallback: {exc}")

    # Deterministic Semantic Governance Fallback (Domain-agnostic heuristics)
    # Principle 1: Active business workflow vs blanket prohibition
    is_a_prohibition = bool(re.search(r"\b(no\s+refund|never|cannot\s+be\s+refunded|prohibit|disallow)\b", text_a, re.I))
    is_b_prohibition = bool(re.search(r"\b(no\s+refund|never|cannot\s+be\s+refunded|prohibit|disallow)\b", text_b, re.I))
    if is_a_prohibition and not is_b_prohibition:
        return id_b, id_a, "Retained active business capability and dropped opposing blanket negative prohibition."
    if is_b_prohibition and not is_a_prohibition:
        return id_a, id_b, "Retained active business capability and dropped opposing blanket negative prohibition."

    # Principle 2: Administrative governance/security vs unmoderated access
    is_a_gov = bool(re.search(r"\b(admin|approval|review|moderation|verify|authorized)\b", text_a, re.I))
    is_b_gov = bool(re.search(r"\b(admin|approval|review|moderation|verify|authorized)\b", text_b, re.I))
    if is_a_gov and not is_b_gov:
        return id_a, id_b, "Enforced administrative governance/approval requirement over unmoderated access."
    if is_b_gov and not is_a_gov:
        return id_b, id_a, "Enforced administrative governance/approval requirement over unmoderated access."

    # Principle 3: Greater specificity
    if len(text_a) >= len(text_b):
        return id_a, id_b, "Retained more detailed requirement statement."
    return id_b, id_a, "Retained more detailed requirement statement."



def get_requirement_type(requirement_id: str):

    if requirement_id.startswith("FR-"):
        return "functional"

    if requirement_id.startswith("NFR-"):
        return "non_functional"

    return None


def extract_original_requirements(
    requirements: Dict
) -> List[Dict]:

    original_items = []
    requirements = requirements or {}

    specified_requirements = requirements.get(
        "specified_requirements",
        {}
    )

    # =========================================================
    # Functional requirements
    # =========================================================

    for item in specified_requirements.get(
        "functional",
        []
    ):
        text = item.get("description") or item.get("text", "")
        original_items.append({
            "id": item["id"],
            "text": text,
            "type": "functional",
            "source_evidence": item.get("source_evidence", [])
        })

    # =========================================================
    # Non-functional requirements
    # =========================================================

    for item in specified_requirements.get(
        "non_functional",
        []
    ):
        text = item.get("description") or item.get("text", "")
        original_items.append({
            "id": item["id"],
            "text": text,
            "type": "non_functional",
            "quality_attribute": item.get("quality_attribute"),
            "source_evidence": item.get("source_evidence", [])
        })

    # Fallback if specified_requirements was not keyed
    if not original_items:
        for item in requirements.get("functional", []):
            original_items.append({
                "id": item["id"],
                "text": item.get("description") or item.get("text", ""),
                "type": "functional",
                "source_evidence": item.get("source_evidence", [])
            })
        for item in requirements.get("non_functional", []):
            original_items.append({
                "id": item["id"],
                "text": item.get("description") or item.get("text", ""),
                "type": "non_functional",
                "quality_attribute": item.get("quality_attribute"),
                "source_evidence": item.get("source_evidence", [])
            })

    return original_items


def reconcile_requirements(
    original_requirements: Dict,
    accepted_changes: Dict,
    answer_requirements: Dict,
    normalized_new_requirements: List[Dict],
    requirement_analysis: Optional[Dict] = None
) -> Dict:

    if requirement_analysis is None and isinstance(original_requirements, dict):
        requirement_analysis = original_requirements.get("requirement_analysis")

    print(
        "\n========== RECONCILING REQUIREMENTS =========="
    )

    # =========================================================
    # 1. Load original requirements
    # =========================================================

    original_items = extract_original_requirements(
        original_requirements
    )

    print(
        f"\nORIGINAL REQUIREMENTS COUNT: "
        f"{len(original_items)}"
    )

    print(
        "ORIGINAL REQUIREMENT IDS:"
    )

    print(
        [
            requirement["id"]
            for requirement in original_items
        ]
    )

    requirements_by_id = {
        item["id"]: item
        for item in original_items
    }

    print(
        f"\nINITIAL REQUIREMENTS BY ID COUNT: "
        f"{len(requirements_by_id)}"
    )

    # =========================================================
    # 2. Apply client review changes
    # =========================================================

       # =========================================================
    # 2. Apply client review changes
    # =========================================================

    kept_changes = accepted_changes.get(
        "kept",
        []
    )

    edited_changes = accepted_changes.get(
        "edited",
        []
    )

    deleted_changes = accepted_changes.get(
        "deleted",
        []
    )

    added_changes = accepted_changes.get(
        "added",
        []
    )

    print(
        f"\nCLIENT REVIEW KEPT COUNT: "
        f"{len(kept_changes)}"
    )

    print(
        f"CLIENT REVIEW EDITED COUNT: "
        f"{len(edited_changes)}"
    )

    print(
        f"CLIENT REVIEW DELETED COUNT: "
        f"{len(deleted_changes)}"
    )

    print(
        f"CLIENT REVIEW ADDED COUNT: "
        f"{len(added_changes)}"
    )

    # ---------------------------------------------------------
    # KEEP
    # ---------------------------------------------------------

    # Kept requirements already exist in requirements_by_id.
    # Nothing needs to be changed.

    # ---------------------------------------------------------
    # EDIT
    # ---------------------------------------------------------

    for change in edited_changes:

        requirement_id = change["id"]

        if requirement_id not in requirements_by_id:

            raise ValueError(
                f"Cannot edit unknown requirement: "
                f"{requirement_id}"
            )

        new_text = change.get("new_text") or change.get("text", "")
        requirements_by_id[requirement_id]["text"] = new_text

        # Append audit trail to source_evidence
        existing_ev = requirements_by_id[requirement_id].get("source_evidence", [])
        audit_entry = {
            "speaker": "Client (HITL Review)",
            "statement": f"Client edited requirement to: \"{new_text}\""
        }
        requirements_by_id[requirement_id]["source_evidence"] = [*existing_ev, audit_entry]

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    for change in deleted_changes:

        requirement_id = change["id"]

        requirements_by_id.pop(
            requirement_id,
            None
        )

    # ---------------------------------------------------------
    # ADD
    # ---------------------------------------------------------

    for change in added_changes:

        requirement_id = change["id"]
        add_text = change.get("new_text") or change.get("text", "")

        requirements_by_id[
            requirement_id
        ] = {
            "id": requirement_id,
            "text": add_text,
            "type": None,
            "source_evidence": [
                {
                    "speaker": "Client (HITL Review)",
                    "statement": f"Client added new requirement: \"{add_text}\""
                }
            ]
        }


    print(
        f"\nAFTER CLIENT REVIEW COUNT: "
        f"{len(requirements_by_id)}"
    )

    print(
        "REQUIREMENT IDS AFTER CLIENT REVIEW:"
    )

    print(
        list(
            requirements_by_id.keys()
        )
    )

    # =========================================================
    # 3. Apply requirements generated from clarification
    # =========================================================

    # This is important:
    #
    # FR-12 may have been deleted during the first review,
    # but the client can later answer a clarification question
    # saying that FR-12 should remain.
    #
    # Therefore answer_requirements overrides the previous
    # deletion.
    #
    # =========================================================

    if isinstance(answer_requirements, dict):
        answer_items = answer_requirements.get(
            "requirements",
            []
        )
    elif isinstance(answer_requirements, list):
        answer_items = answer_requirements
    else:
        answer_items = []

    print(
        f"\nCLARIFICATION GENERATED REQUIREMENTS COUNT: "
        f"{len(answer_items)}"
    )

    for requirement in answer_items:

        requirement_id = requirement["id"]

        existing = requirements_by_id.get(
            requirement_id
        )

        requirement_type = (
            existing.get("type")
            if existing
            else get_requirement_type(
                requirement_id
            )
        )

        requirements_by_id[
            requirement_id
        ] = {
            "id": requirement_id,
            "text": requirement["text"],
            "type": requirement_type
        }

    print(
        f"\nAFTER CLARIFICATION ANSWERS COUNT: "
        f"{len(requirements_by_id)}"
    )

    print(
        "REQUIREMENT IDS AFTER CLARIFICATION:"
    )

    print(
        list(
            requirements_by_id.keys()
        )
    )

    # =========================================================
    # 4. Apply normalized NEW requirements
    # =========================================================

    # These have already gone through:
    #
    # collect
    #     ↓
    # classification
    #     ↓
    # format check
    #     ↓
    # normalization
    #
    # So reconciliation simply accepts them.
    #
    # =========================================================

    print(
        f"\nNORMALIZED NEW REQUIREMENTS COUNT: "
        f"{len(normalized_new_requirements)}"
    )

    for requirement in normalized_new_requirements:

        requirement_id = requirement["id"]
        existing = requirements_by_id.get(requirement_id, {})
        source_ev = existing.get("source_evidence") or [
            {
                "speaker": "Client (HITL Review)",
                "statement": f"Client added new requirement: \"{requirement['text']}\""
            }
        ]

        requirements_by_id[
            requirement_id
        ] = {
            "id": requirement_id,
            "text": requirement["text"],
            "type": requirement.get("type", "functional"),
            "source_evidence": source_ev
        }

    print(
        f"\nAFTER NEW REQUIREMENTS COUNT: "
        f"{len(requirements_by_id)}"
    )

    print(
        "REQUIREMENT IDS AFTER NEW REQUIREMENTS:"
    )

    print(
        list(
            requirements_by_id.keys()
        )
    )

    # =========================================================
    # 5. Recover classification for any existing FR/NFR
    # =========================================================

    for requirement_id, requirement in (
        requirements_by_id.items()
    ):

        if requirement.get("type") is None:

            recovered = get_requirement_type(requirement_id)
            requirement["type"] = recovered or "functional"

    # =========================================================
    # 5.5 Canonical sequential ID assignment for new additions
    # =========================================================

    # Prevent ID collision: Do not recycle deleted requirement IDs for new additions
    all_seen_fr_nums = [
        int(m.group(1)) for r in list(requirements_by_id.values()) + original_items
        if (m := re.match(r"^FR-(\d+)$", str(r.get("id", ""))))
    ]
    next_fr_num = max(all_seen_fr_nums, default=0) + 1

    all_seen_nfr_nums = [
        int(m.group(1)) for r in list(requirements_by_id.values()) + original_items
        if (m := re.match(r"^NFR-(\d+)$", str(r.get("id", ""))))
    ]
    next_nfr_num = max(all_seen_nfr_nums, default=0) + 1

    updated_requirements_by_id = {}
    for req_id, requirement in list(requirements_by_id.items()):
        if str(req_id).startswith("new-") or not (str(req_id).startswith("FR-") or str(req_id).startswith("NFR-")):
            if requirement.get("type") == "non_functional":
                canonical_id = f"NFR-{next_nfr_num}"
                next_nfr_num += 1
            else:
                canonical_id = f"FR-{next_fr_num}"
                next_fr_num += 1
            print(f"[Reconciliation] Assigned canonical ID '{canonical_id}' to addition (was '{req_id}')")
            requirement["id"] = canonical_id
            updated_requirements_by_id[canonical_id] = requirement
        else:
            updated_requirements_by_id[req_id] = requirement

    requirements_by_id = updated_requirements_by_id

    # =========================================================
    # 5.6 Automated Dynamic Contradiction Resolution Safety Net (Layer 2)
    # =========================================================
    # Dynamically detects and resolves any contradictory pairs that survived client review.
    # Uses governance arbitration principles without hardcoded requirement IDs.
    if requirement_analysis and isinstance(requirement_analysis, dict):
        flagged = requirement_analysis.get("flagged_requirements", [])
        edited_ids = {c.get("id") for c in accepted_changes.get("edited", []) if c.get("id")}
        resolved_conflicts = set()

        for item in flagged:
            if item.get("issue_type") != "contradictory":
                continue
            r1_id = str(item.get("id"))
            conflicts = item.get("conflicting_with") or item.get("conflicts_with") or []
            if isinstance(conflicts, str):
                conflicts = [conflicts]

            for r2_id_raw in conflicts:
                r2_id = str(r2_id_raw)
                pair_key = tuple(sorted([r1_id, r2_id]))
                if pair_key in resolved_conflicts:
                    continue

                if r1_id in requirements_by_id and r2_id in requirements_by_id:
                    resolved_conflicts.add(pair_key)
                    r1_obj = requirements_by_id[r1_id]
                    r2_obj = requirements_by_id[r2_id]
                    r1_text = r1_obj.get("text") or r1_obj.get("description", "")
                    r2_text = r2_obj.get("text") or r2_obj.get("description", "")
                    reason = item.get("reason", "Direct conflict between business rules")

                    # Check client explicit edit intent
                    if r1_id in edited_ids and r2_id not in edited_ids:
                        keep_id, drop_id = r1_id, r2_id
                        rationale = f"Client explicitly edited {r1_id}, confirming intent over conflicting {r2_id}."
                    elif r2_id in edited_ids and r1_id not in edited_ids:
                        keep_id, drop_id = r2_id, r1_id
                        rationale = f"Client explicitly edited {r2_id}, confirming intent over conflicting {r1_id}."
                    else:
                        # Dynamic Semantic & Governance Arbitration
                        keep_id, drop_id, rationale = arbitrate_contradiction(
                            r1_id, r1_text, r2_id, r2_text, reason
                        )

                    # Apply resolution
                    requirements_by_id.pop(drop_id, None)
                    surviving = requirements_by_id.get(keep_id)
                    if surviving:
                        ev = surviving.get("source_evidence") or []
                        surviving["source_evidence"] = [
                            *ev,
                            {
                                "speaker": "System (Contradiction Safety Net)",
                                "statement": f"Automatically resolved direct conflict: dropped {drop_id}. Rationale: {rationale}"
                            }
                        ]
                    print(f"[Dynamic Safety Net] Resolved contradiction between {r1_id} and {r2_id}: kept {keep_id}, dropped {drop_id}. Rationale: {rationale}")

    print(
        f"\nAFTER CLASSIFICATION RECOVERY, CANONICAL NUMBERING & SAFETY NET COUNT: "
        f"{len(requirements_by_id)}"
    )

    # =========================================================
    # 6. Validate classification
    # =========================================================

    validate_final_requirements(
        list(
            requirements_by_id.values()
        )
    )

    print(
        "\nFINAL REQUIREMENT VALIDATION: SUCCESS"
    )

    # =========================================================
    # 7. Preserve original ordering
    # =========================================================

    final_items = []

    processed_ids = set()

    for original in original_items:

        requirement_id = original["id"]

        if requirement_id in requirements_by_id:

            final_items.append(
                requirements_by_id[
                    requirement_id
                ]
            )

            processed_ids.add(
                requirement_id
            )

    print(
        f"\nAFTER PRESERVING ORIGINAL ORDER COUNT: "
        f"{len(final_items)}"
    )

    # =========================================================
    # 8. Append genuinely new requirements
    # =========================================================

    appended_new_count = 0

    for requirement_id, requirement in (
        requirements_by_id.items()
    ):

        if requirement_id not in processed_ids:

            final_items.append(
                requirement
            )

            appended_new_count += 1

    print(
        f"\nGENUINELY NEW REQUIREMENTS APPENDED: "
        f"{appended_new_count}"
    )

    print(
        f"FINAL RECONCILIATION INPUT COUNT: "
        f"{len(final_items)}"
    )

    print(
        "FINAL REQUIREMENT IDS:"
    )

    print(
        [
            requirement["id"]
            for requirement in final_items
        ]
    )

    # =========================================================
    # 9. Separate FRs and NFRs
    # =========================================================

    functional_requirements = []
    non_functional_requirements = []

    for requirement in final_items:

        if requirement["type"] == "functional":

            functional_requirements.append(
                requirement
            )

        elif requirement["type"] == "non_functional":

            non_functional_requirements.append(
                requirement
            )

    print(
        f"\nFINAL FUNCTIONAL REQUIREMENTS COUNT: "
        f"{len(functional_requirements)}"
    )

    print(
        f"FINAL NON-FUNCTIONAL REQUIREMENTS COUNT: "
        f"{len(non_functional_requirements)}"
    )

    # =========================================================
    # 10. Build final result
    # =========================================================

    canonical_frs = []
    for req in functional_requirements:
        canonical_frs.append({
            "id": req["id"],
            "description": req.get("description") or req.get("text", ""),
            "source_evidence": req.get("source_evidence") or [
                {"speaker": "Client", "statement": req.get("description") or req.get("text", "")}
            ]
        })

    canonical_nfrs = []
    for req in non_functional_requirements:
        canonical_nfrs.append({
            "id": req["id"],
            "description": req.get("description") or req.get("text", ""),
            "source_evidence": req.get("source_evidence") or [
                {"speaker": "Client", "statement": req.get("description") or req.get("text", "")}
            ]
        })

    final_result = {
        "specified_requirements": {
            "functional": canonical_frs,
            "non_functional": canonical_nfrs
        },
        "functional": canonical_frs,
        "non_functional": canonical_nfrs,
        "sections": [
            {
                "title": "Functional Requirements",
                "items": functional_requirements
            },
            {
                "title": "Non-Functional Requirements",
                "items": non_functional_requirements
            }
        ]
    }

    # =========================================================
    # 11. Debug output
    # =========================================================

    print(
        "\n========== FINAL FUNCTIONAL REQUIREMENTS =========="
    )

    print(
        json.dumps(
            functional_requirements,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\n========== FINAL NON-FUNCTIONAL REQUIREMENTS =========="
    )

    print(
        json.dumps(
            non_functional_requirements,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\n========== FINAL REQUIREMENTS =========="
    )

    print(
        json.dumps(
            final_result,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "=========================================="
    )

    return final_result


def validate_final_requirements(
    requirements: List[Dict]
):

    seen_ids = set()

    for requirement in requirements:

        requirement_id = requirement.get(
            "id"
        )

        text = requirement.get(
            "text"
        )

        requirement_type = requirement.get(
            "type"
        )

        # -----------------------------------------------------
        # ID validation
        # -----------------------------------------------------

        if not isinstance(
            requirement_id,
            str
        ):

            raise ValueError(
                "Every final requirement must have "
                "a string ID."
            )

        if requirement_id in seen_ids:

            raise ValueError(
                f"Duplicate requirement ID: "
                f"{requirement_id}"
            )

        seen_ids.add(
            requirement_id
        )

        # -----------------------------------------------------
        # Text validation
        # -----------------------------------------------------

        if not isinstance(
            text,
            str
        ) or not text.strip():

            raise ValueError(
                f"Requirement {requirement_id} "
                f"has invalid text."
            )

        # -----------------------------------------------------
        # Type validation
        # -----------------------------------------------------

        if requirement_type not in {
            "functional",
            "non_functional"
        }:

            raise ValueError(
                f"Requirement {requirement_id} "
                f"does not have a valid classification."
            )

    return True