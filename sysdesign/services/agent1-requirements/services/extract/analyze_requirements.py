"""
Requirement Quality Analysis Service

Goal:
Inspect all extracted specified requirements (functional and non-functional)
to detect requirement defects before human review:
1. Vague requirements (subjective, ambiguous, unmeasurable criteria)
2. Incomplete requirements (missing actors, inputs, outputs, conditions, or triggers)
3. Contradictory requirements (direct or subtle conflicts between requirements)

Output:
A structured dictionary with flagged requirements, issue types, and detailed reasons.
"""

import json
import re
from typing import Dict, Any, List
from services.llm import llm

REQUIREMENT_ANALYSIS_PROMPT = """
You are a principal software requirements quality auditor.
Your job is to inspect a set of extracted software requirements (functional and non-functional)
and identify any requirements that suffer from quality defects:

1. "vague":
   The requirement uses subjective terms, unquantified adjectives, or ambiguous language without measurable thresholds.
   Examples:
   - "The system shall provide fast response times." (Vague: no latency/throughput specified)
   - "The system shall be easy to use and user-friendly." (Vague: no usability criteria)
   - "The system shall be reliable enough for daily use." (Vague: no uptime/MTBF specified)
   - "The system shall understand the context of discussion." (Vague: subjective concept without concrete boundaries)

2. "incomplete":
   The requirement lacks essential context such as the actor, the trigger, specific inputs, target outputs, or operational boundaries.
   Examples:
   - "The system shall process submitted meeting information." (Incomplete: does not specify what processing occurs or what outputs are produced)
   - "The system shall store data." (Incomplete: does not specify what data or storage constraints)

3. "contradictory":
   Two or more requirements express conflicting capabilities, conflicting permissions, or conflicting business rules.
   Examples:
   - Req A allows all guest users access, while Req B mandates login for all access.
   - Req A says data is permanently deleted immediately, while Req B says data is retained for 30 days.

CRITICAL CLIENT-FACING RULE FOR REASON WRITING:
- The explanation in `reason` will be read DIRECTLY by non-technical client stakeholders.
- NEVER, under any circumstance, mention internal technical IDs like "FR-1", "FR-12", "NFR-2", or "requirement ID" in the `reason` text!
- Instead of saying "conflicts with FR-12", write:
  "another requirement states that ..." or "while another requirement prohibits ..."
- Examples:
  * WRONG: "FR-3 allows cancellation, while FR-12 prohibits refunds after a ticket has been purchased, creating a conflict."
  * CORRECT: "This allows cancellation with a full refund before the event begins, while another requirement prohibits refunds after a ticket has been purchased, creating a direct conflict."
  * WRONG: "FR-6 is vague."
  * CORRECT: "The requirement uses the subjective phrase 'understand the context of the discussion' without defining measurable criteria."

CRITICAL INSTRUCTIONS:
- Analyze ALL requirements provided.
- Only flag requirements that legitimately have one of these defects.
- For each flagged requirement:
  - Specify the requirement ID exactly as given in the `id` field (e.g., "FR-1", "NFR-3").
  - Specify the `issue_type`: "vague" | "incomplete" | "contradictory".
  - Provide a clear, actionable `reason` in natural language WITHOUT mentioning any internal IDs (like FR-12).
  - If "contradictory", provide `conflicting_with` as a list of requirement IDs it conflicts with.
- If a requirement is clear, complete, and non-contradictory, DO NOT flag it.
- Return ONLY valid JSON with no extra commentary or markdown fences.

OUTPUT SCHEMA:
{
  "flagged_requirements": [
    {
      "id": "FR-1",
      "issue_type": "vague",
      "reason": "The requirement uses the subjective phrase 'turn information into clear requirements' without defining measurable clarity criteria or expected output structures.",
      "conflicting_with": []
    },
    {
      "id": "FR-6",
      "issue_type": "vague",
      "reason": "The requirement states 'understand the context of the discussion' which is subjective and lacks measurable technical boundaries.",
      "conflicting_with": []
    }
  ],
  "summary": "High-level summary of defects found."
}

REQUIREMENTS TO ANALYZE:
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


def sanitize_client_facing_reason(reason: str, current_id: str, req_map: Dict[str, str]) -> str:
    """
    Guarantees that no internal IDs (FR-*, NFR-*, RC-*) leak to the client.
    Replaces ID references with natural language like 'another requirement' or
    quotes the conflicting requirement context.
    """
    if not reason:
        return reason

    def replace_id(match):
        mid = match.group(0).upper()
        if mid == current_id.upper():
            return "this requirement"
        return "another requirement"

    # Replace specific patterns like "with FR-12", "FR-12", "while FR-11" -> "another requirement"
    cleaned = re.sub(r"\b(FR|NFR|RC)-\d+\b", replace_id, reason, flags=re.IGNORECASE)
    # Clean up double phrases if any like "another requirement another requirement"
    cleaned = re.sub(r"\banother requirement\s+another requirement\b", "another requirement", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def analyze_extracted_requirements(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes functional and non-functional requirements to detect
    vague, incomplete, or contradictory requirements.
    """
    print("\n========== REQUIREMENT QUALITY DEFECT ANALYSIS ==========")
    if not requirements:
        print("[Analysis] No requirements provided. Skipping defect analysis.")
        return {"flagged_requirements": [], "summary": "No requirements provided."}

    specified = requirements.get("specified_requirements", {})
    functional = specified.get("functional") or requirements.get("functional") or []
    non_functional = specified.get("non_functional") or requirements.get("non_functional") or []

    all_reqs = []
    for f in functional:
        all_reqs.append({
            "id": f.get("id"),
            "type": "functional",
            "description": f.get("description") or f.get("text", "")
        })
    for nf in non_functional:
        all_reqs.append({
            "id": nf.get("id"),
            "type": "non_functional",
            "quality_attribute": nf.get("quality_attribute", ""),
            "description": nf.get("description") or nf.get("text", "")
        })

    if not all_reqs:
        print("[Analysis] Empty requirements list. Skipping defect analysis.")
        return {"flagged_requirements": [], "summary": "Empty requirements list."}

    req_map = {r["id"]: r.get("description", "") for r in all_reqs if r.get("id")}

    prompt = f"{REQUIREMENT_ANALYSIS_PROMPT}\n{json.dumps(all_reqs, indent=2, ensure_ascii=False)}"
    print(f"[Analysis] Invoking LLM to analyze {len(all_reqs)} requirements for defects...")

    try:
        response = llm.invoke(prompt)
        raw_content = response.content.strip()
        parsed = parse_json_response(raw_content)
    except Exception as exc:
        print(f"[Analysis WARNING] LLM analysis call failed or could not parse JSON: {exc}. Using fallback.")
        parsed = {"flagged_requirements": [], "summary": f"Analysis failed: {exc}"}

    raw_flagged = parsed.get("flagged_requirements", [])
    if not isinstance(raw_flagged, list):
        raw_flagged = []

    valid_req_ids = {r["id"] for r in all_reqs if r.get("id")}
    cleaned_flagged = []

    for item in raw_flagged:
        if not isinstance(item, dict):
            continue
        req_id = item.get("id")
        if not req_id or req_id not in valid_req_ids:
            continue
        
        issue_type = str(item.get("issue_type", "vague")).lower().strip()
        if issue_type not in ["vague", "incomplete", "contradictory"]:
            issue_type = "vague"

        reason = (item.get("reason") or "Requirement requires clarification.").strip()
        conflicts = item.get("conflicting_with", [])
        if isinstance(conflicts, str):
            conflicts = [conflicts]
        elif not isinstance(conflicts, list):
            conflicts = []

        # Client-facing safety: scrub any accidental internal IDs (FR-*, NFR-*) from reason
        reason = sanitize_client_facing_reason(reason, req_id, req_map)

        cleaned_flagged.append({
            "id": req_id,
            "issue_type": issue_type,
            "reason": reason,
            "conflicting_with": conflicts
        })

    result = {
        "flagged_requirements": cleaned_flagged,
        "total_flagged": len(cleaned_flagged),
        "total_requirements": len(all_reqs),
        "summary": parsed.get("summary", f"Identified {len(cleaned_flagged)} requirements requiring review.")
    }

    print(f"[Analysis Complete] Flagged {len(cleaned_flagged)} of {len(all_reqs)} requirements:")
    for flag in cleaned_flagged:
        conf_str = f" (conflicts with {flag['conflicting_with']})" if flag["conflicting_with"] else ""
        print(f"  * [{flag['id']}] [{flag['issue_type'].upper()}]{conf_str}: {flag['reason']}")
    print("=========================================================\n")

    return result
