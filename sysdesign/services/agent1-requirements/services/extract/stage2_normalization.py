"""
Stage 2: Requirement Normalization

Goal:
Receives atomic evidence candidates from Stage 1 and converts each candidate
into a clear, atomic software requirement without altering its meaning.

Critical Rules:
1. Preserve original stakeholder intent.
2. Do NOT introduce new capabilities, constraints, metrics, or details not present in evidence.
3. Convert informal wording into clear requirement language (typically "The system shall...").
4. If an evidence candidate contains multiple independent requirements, split them into separate
   normalized requirements, each linking back to the source evidence ID.
5. If the statement is vague (e.g., "The system should be reliable enough"), DO NOT invent numbers
   (e.g., "99.9% uptime"). Instead, preserve the intent and set `requires_clarification: true`
   with a clear `clarification_reason`.
6. Maintain traceability via `source_evidence_ids`.
7. Do NOT classify as FR or NFR at this stage.
"""

import json
import re
from typing import Dict, Any, List
from services.llm import llm
from .extract_guidelines import SPECIFIED_REQUIREMENTS_GUIDELINES

STAGE2_NORMALIZATION_PROMPT = """
You are a senior requirements engineer conducting the SECOND STAGE of requirements extraction: Requirement Normalization.

You will receive a list of stakeholder evidence candidates extracted from a meeting or document.
Your task is to convert each valid candidate into a clear, testable, atomic software requirement statement adhering to the official extraction guidelines.

OFFICIAL SPECIFIED REQUIREMENTS GUIDELINES:
""" + SPECIFIED_REQUIREMENTS_GUIDELINES + """

CRITICAL NORMALIZATION RULES:
1. Preserve the original stakeholder intent without hallucinating or adding missing details.
2. Formulate each requirement in standard software requirement language (e.g., "The system shall...").
3. Each requirement must describe ONE independently identifiable, independently TESTABLE system behavior.
4. NEVER invent specific technical thresholds or metrics that the stakeholder did not state!
   Example:
   If evidence says: "The system should be fast and reliable enough."
   DO NOT invent: "The system shall respond within 200ms and maintain 99.99% uptime."
   INSTEAD: Formulate "The system shall provide high-speed and reliable operation."
   And set:
     "requires_clarification": true
     "clarification_reason": "Stakeholder did not specify measurable performance or reliability criteria."
5. If one evidence candidate contains multiple independent requirements, split them into separate requirement candidates,
   each referencing the source evidence ID.
6. Maintain strict traceability: each normalized requirement must include the exact list of `source_evidence_ids` it was derived from.
7. Do NOT classify as functional or non-functional at this stage.

STATEMENTS TO REJECT (do NOT normalize these into requirements):
- High-level project vision or mission statements (e.g., "We are looking for a solution that helps our team manage requirements")
- Business objectives or expected outcomes (e.g., "We expect the system to reduce manual work")
- Summary/concluding statements that merely re-state goals already covered by specific requirements
- Statements that describe WHAT THE PROJECT HOPES TO ACHIEVE rather than WHAT THE SYSTEM MUST DO

ATOMICITY RULES:
- If a statement lists multiple distinct system behaviors in a single sentence (e.g., "The system shall detect unclear, incomplete, duplicated, contradictory, and ambiguous requirements"), split each distinct behavior into its own separate requirement candidate.
- Each requirement candidate must be independently testable — you should be able to write one test case for it.
- If a statement describes a broad capability AND a specific mechanism, extract the specific mechanism as the requirement.

OUTPUT SCHEMA:
Return ONLY a valid JSON object matching this exact structure:
{
  "normalized_requirements": [
    {
      "requirement_candidate_id": "RC-001",
      "description": "The system shall ...",
      "source_evidence_ids": ["EV-001"],
      "requires_clarification": false,
      "clarification_reason": null
    }
  ]
}

EVIDENCE CANDIDATES:
"""


def parse_json_response(content: str) -> Dict[str, Any]:
    content = content.strip()
    content = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"```\s*", "", content)

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise json.JSONDecodeError("No JSON object found in response", content, 0)

    json_str = content[start:end + 1]

    try:
        return json.loads(json_str, strict=False)
    except json.JSONDecodeError:
        try:
            import json_repair
            return json_repair.loads(json_str)
        except Exception:
            pass
        cleaned = re.sub(r",\s*([\]}])", r"\1", json_str)
        return json.loads(cleaned, strict=False)


def normalize_requirements(evidence_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executes Stage 2 Requirement Normalization.
    Transforms raw evidence candidates into normalized atomic requirements
    with traceability and clarification flags.
    """
    print("\n========== STAGE 2: REQUIREMENT NORMALIZATION ==========")
    if not evidence_candidates:
        print("[Stage 2] No evidence candidates received. Returning 0 normalized requirements.")
        return []

    evidence_input = [
        {
            "evidence_id": e.get("evidence_id"),
            "source_text": e.get("source_text"),
            "speaker": e.get("speaker"),
            "context": e.get("context"),
            "candidate_category": e.get("candidate_category"),
        }
        for e in evidence_candidates
    ]

    prompt = f"{STAGE2_NORMALIZATION_PROMPT}\n{json.dumps(evidence_input, indent=2, ensure_ascii=False)}"
    print(f"[Stage 2] Invoking LLM to normalize {len(evidence_candidates)} evidence candidate(s)...")

    response = llm.invoke(prompt)
    raw_content = response.content.strip()

    try:
        parsed = parse_json_response(raw_content)
        normalized = parsed.get("normalized_requirements", [])
        if not isinstance(normalized, list):
            normalized = []
    except Exception as exc:
        print(f"[Stage 2 WARNING] Failed to parse JSON response: {exc}")
        normalized = []

    # Post-process and ensure consistent IDs and traceability
    valid_evidence_ids = {e.get("evidence_id") for e in evidence_candidates if e.get("evidence_id")}
    cleaned_normalized = []

    for idx, item in enumerate(normalized, start=1):
        if not isinstance(item, dict):
            continue

        rc_id = item.get("requirement_candidate_id") or f"RC-{idx:03d}"
        desc = (item.get("description") or "").strip()
        if not desc:
            continue

        raw_ev_ids = item.get("source_evidence_ids", [])
        if isinstance(raw_ev_ids, str):
            raw_ev_ids = [raw_ev_ids]
        elif not isinstance(raw_ev_ids, list):
            raw_ev_ids = []

        # Filter to valid known evidence IDs where possible; if empty, link to first evidence candidate as fallback
        matched_ev_ids = [eid for eid in raw_ev_ids if eid in valid_evidence_ids]
        if not matched_ev_ids and evidence_candidates:
            matched_ev_ids = [evidence_candidates[min(idx - 1, len(evidence_candidates) - 1)].get("evidence_id", "EV-001")]

        req_clarification = bool(item.get("requires_clarification", False))
        clarification_reason = item.get("clarification_reason")
        if req_clarification and not clarification_reason:
            clarification_reason = "Statement contains ambiguity or unmeasurable quality criteria that require client clarification."
        elif not req_clarification:
            clarification_reason = None

        cleaned_normalized.append({
            "requirement_candidate_id": rc_id,
            "description": desc,
            "source_evidence_ids": matched_ev_ids,
            "requires_clarification": req_clarification,
            "clarification_reason": clarification_reason,
        })

    print(f"[Stage 2] Successfully normalized into {len(cleaned_normalized)} atomic requirement candidate(s).")
    return cleaned_normalized
