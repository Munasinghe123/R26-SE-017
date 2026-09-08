"""
Stage 3: Independent Requirement Classification

Goal:
Classify normalized requirement candidates into functional, non-functional, or uncertain,
providing quality attributes, confidence scores, and reasoning.

Critical Rules:
1. Classify ONLY the normalized requirement statements provided.
2. Do NOT rewrite or modify the requirement descriptions.
3. Do NOT invent additional information.
4. Support classifications:
   - "functional"
   - "non_functional" (with ISO 25010 quality attribute: security, reliability, performance,
      usability, maintainability, scalability, availability, recoverability, etc.)
   - "uncertain" (when a requirement could be reasonably treated as either FR or NFR)
5. Provide a confidence score (0.0 to 1.0) and explicit classification reason.
6. Support explicit uncertainty rather than forcing an arbitrary choice.
"""

import json
import re
from typing import Dict, Any, List
from services.llm import llm
from .extract_guidelines import SPECIFIED_REQUIREMENTS_GUIDELINES

STAGE3_CLASSIFICATION_PROMPT = """
You are a senior software architect and requirements engineer conducting the THIRD STAGE of requirements extraction: Independent Classification.

You will receive a list of normalized requirement candidates.
Your task is to classify EACH requirement candidate independently strictly following the official extraction guidelines.

OFFICIAL SPECIFIED REQUIREMENTS GUIDELINES:
""" + SPECIFIED_REQUIREMENTS_GUIDELINES + """

CLASSIFICATION DEFINITIONS:
1. "functional":
   The requirement describes WHAT the system must do (a specific action, behavior, capability, calculation, workflow, or data transformation).
   Examples: "The system shall allow users to reset their password.", "The system shall generate monthly invoices."

2. "non_functional":
   The requirement specifies HOW WELL, under what constraints, or with what quality attributes the system must perform (without introducing an entirely new standalone capability).
   Quality Attributes:
   - "security" (authentication, encryption, authorization, audit logging)
   - "performance" (latency, throughput, response time)
   - "reliability" (fault tolerance, uptime, MTBF)
   - "scalability" (concurrency, horizontal growth, data volume)
   - "usability" (accessibility, UI simplicity, ease of use)
   - "availability" (system uptime, failover)
   - "maintainability" (modularity, technical documentation)
   - "recoverability" (disaster recovery, backup restoration)
   - "other"

3. "uncertain":
   The requirement contains mixed characteristics or could legitimately be modeled as either a functional capability or a non-functional constraint (e.g., automated failover, session timeout enforcement).
   In this case, explicitly classify as "uncertain", list candidate classifications, and provide the rationale.

4. "reject":
   The statement is NOT a software requirement at all. Use this classification for:
   - Business objectives or expected business outcomes (e.g., "reduce manual work", "improve productivity")
   - High-level project vision statements that are not independently testable
   - Summary/concluding statements that merely re-state goals already covered by other requirements
   Items classified as "reject" will be EXCLUDED from the final output.

CRITICAL CLASSIFICATION RULES FROM GUIDELINES:
- Information about the PROJECT is NOT a software requirement. Do NOT classify deadlines, delivery dates, schedules, or priorities as non-functional requirements!
- Business objectives (e.g., "reduce manual work", "improve efficiency") are NOT non-functional requirements.
- Do NOT infer non-functional requirements from common software engineering practice.
- If a requirement contains both action and quality constraint, classify based on whether a new action is introduced (functional) vs pure quality constraint (non_functional).

CRITICAL RULES:
1. Do NOT rewrite, change, or edit the requirement description!
2. Do NOT invent new requirements or fields.
3. Provide a realistic confidence score (0.0 to 1.0).
4. Provide a clear classification reason.

OUTPUT SCHEMA:
Return ONLY a valid JSON object matching this exact structure:
{
  "classified_requirements": [
    {
      "requirement_candidate_id": "RC-001",
      "classification": "functional",
      "quality_attribute": null,
      "candidate_classifications": null,
      "confidence": 0.95,
      "classification_reason": "The requirement describes a distinct user-facing capability and action."
    },
    {
      "requirement_candidate_id": "RC-002",
      "classification": "non_functional",
      "quality_attribute": "reliability",
      "candidate_classifications": null,
      "confidence": 0.90,
      "classification_reason": "The requirement specifies an operational reliability constraint on system services."
    },
    {
      "requirement_candidate_id": "RC-003",
      "classification": "reject",
      "quality_attribute": null,
      "candidate_classifications": null,
      "confidence": 0.95,
      "classification_reason": "This is a business objective, not a testable software requirement."
    }
  ]
}

NORMALIZED REQUIREMENTS:
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


def classify_requirements(normalized_requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executes Stage 3 Independent Requirement Classification.
    Returns classified requirement candidates with confidence scores and reasoning.
    """
    print("\n========== STAGE 3: INDEPENDENT REQUIREMENT CLASSIFICATION ==========")
    if not normalized_requirements:
        print("[Stage 3] No normalized requirements received. Returning 0 classified items.")
        return []

    reqs_input = [
        {
            "requirement_candidate_id": r.get("requirement_candidate_id"),
            "description": r.get("description"),
            "requires_clarification": r.get("requires_clarification"),
            "clarification_reason": r.get("clarification_reason"),
        }
        for r in normalized_requirements
    ]

    prompt = f"{STAGE3_CLASSIFICATION_PROMPT}\n{json.dumps(reqs_input, indent=2, ensure_ascii=False)}"
    print(f"[Stage 3] Invoking LLM to classify {len(normalized_requirements)} normalized requirement(s)...")

    response = llm.invoke(prompt)
    raw_content = response.content.strip()

    try:
        parsed = parse_json_response(raw_content)
        classified_list = parsed.get("classified_requirements", [])
        if not isinstance(classified_list, list):
            classified_list = []
    except Exception as exc:
        print(f"[Stage 3 WARNING] Failed to parse JSON response: {exc}")
        classified_list = []

    # Map classifications back by requirement_candidate_id
    classification_map = {}
    for c in classified_list:
        if isinstance(c, dict) and c.get("requirement_candidate_id"):
            classification_map[c["requirement_candidate_id"]] = c

    merged_classified = []
    for r in normalized_requirements:
        rc_id = r.get("requirement_candidate_id")
        clf = classification_map.get(rc_id, {})

        classification = clf.get("classification", "functional")
        if classification not in ["functional", "non_functional", "uncertain", "reject"]:
            classification = "uncertain"

        q_attr = clf.get("quality_attribute")
        cand_classes = clf.get("candidate_classifications")
        conf = float(clf.get("confidence") or 0.85)
        reason = clf.get("classification_reason") or "Classified based on requirement semantics."

        merged_item = {
            **r,
            "classification": classification,
            "quality_attribute": q_attr if classification == "non_functional" else None,
            "candidate_classifications": cand_classes if classification == "uncertain" else None,
            "confidence": conf,
            "classification_reason": reason,
        }
        merged_classified.append(merged_item)

    print(f"[Stage 3] Successfully classified {len(merged_classified)} requirement(s).")
    return merged_classified
