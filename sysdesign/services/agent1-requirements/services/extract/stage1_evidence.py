"""
Stage 1: Evidence Extraction

Goal:
Identify and capture all stakeholder statements or segments from transcripts/documents
that potentially express a software requirement.

Critical Rules:
1. High recall — capture all potential requirement-related statements.
2. Preserve original stakeholder wording as much as possible.
3. Include speaker and contextual information where available.
4. Extract atomic evidence segments.
5. Do NOT rewrite evidence into formal "The system shall..." statements.
6. Do NOT classify evidence as FR or NFR.
7. Do NOT invent requirements.
8. Do NOT discard statements simply because they are vague or informal.
"""

import json
import re
from typing import Dict, Any, List
from services.llm import llm

STAGE1_EVIDENCE_PROMPT = """
You are a senior requirements analyst conducting the FIRST STAGE of requirements extraction.

Your ONLY job is to identify and extract EVERY stakeholder statement or conversation segment 
that expresses a potential SOFTWARE requirement, capability, constraint, quality expectation, 
business rule, or user expectation about the SYSTEM BEING BUILT.

WHAT COUNTS AS A SOFTWARE REQUIREMENT EVIDENCE:
- A statement describing a specific action, behavior, or capability the system must perform.
- A statement describing a quality attribute the system must satisfy (performance, security, reliability, etc.).
- A statement describing a constraint on how the system must operate.
- A statement describing how a user interacts with the system.

WHAT DOES NOT COUNT (DO NOT EXTRACT THESE):
- High-level project vision or mission statements (e.g., "We are looking for a software solution that can help our team...")
- Business objectives or expected business outcomes (e.g., "We expect the system to reduce the amount of manual work...")
- Summaries or re-statements of goals already captured as specific requirements elsewhere.
- Statements that merely restate or summarize other more specific statements in the same document.

CRITICAL RULES:
- Do NOT rewrite statements into formal "The system shall..." requirements.
- Do NOT classify items as Functional Requirements (FR) or Non-Functional Requirements (NFR).
- Do NOT invent or assume missing capabilities or requirements.
- Do NOT discard vague, informal, or incomplete statements about SPECIFIC system behaviors. Capture them.
- Do NOT output markdown code fences (like ```json). Return ONLY valid raw JSON.
- If a single sentence contains MULTIPLE independent system behaviors, split them into separate evidence candidates.

DO:
- Preserve the exact or near-exact original stakeholder wording.
- Break compound discussions into atomic evidence candidates if multiple distinct needs are discussed.
- Assign each statement a category indicating the type of stakeholder intent:
  "capability" | "quality_expectation" | "constraint" | "business_rule" | "integration" | "user_interaction" | "other"
- Attribute the speaker whenever indicated in the transcript (e.g., "Client", "BA", "User", "Speaker 1").
- Provide a confidence score (0.0 to 1.0) on whether this segment expresses a potential requirement.

OUTPUT SCHEMA:
Return ONLY a valid JSON object matching this exact structure:
{
  "evidence_candidates": [
    {
      "evidence_id": "EV-001",
      "source_text": "Exact or near-exact stakeholder statement",
      "speaker": "Client",
      "context": "Surrounding conversation context or topic being discussed",
      "candidate_category": "capability",
      "confidence": 0.95
    }
  ]
}

TRANSCRIPT / DOCUMENT CONTENT:
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


def extract_evidence(transcript: str) -> List[Dict[str, Any]]:
    """
    Executes Stage 1 Evidence Extraction.
    Returns a list of raw atomic evidence candidate dictionaries.
    """
    print("\n========== STAGE 1: EVIDENCE EXTRACTION ==========")
    if not transcript or not transcript.strip():
        print("[Stage 1] Empty transcript provided. Returning 0 evidence candidates.")
        return []

    prompt = f"{STAGE1_EVIDENCE_PROMPT}\n{transcript.strip()}"
    print(f"[Stage 1] Invoking LLM for high-recall evidence extraction ({len(transcript)} chars)...")

    response = llm.invoke(prompt)
    raw_content = response.content.strip()

    try:
        parsed = parse_json_response(raw_content)
        candidates = parsed.get("evidence_candidates", [])
        if not isinstance(candidates, list):
            candidates = []
    except Exception as exc:
        print(f"[Stage 1 WARNING] Failed to parse JSON response: {exc}")
        candidates = []

    # Clean and normalize IDs
    cleaned_candidates = []
    for idx, c in enumerate(candidates, start=1):
        if not isinstance(c, dict):
            continue
        ev_id = c.get("evidence_id") or f"EV-{idx:03d}"
        source_text = (c.get("source_text") or "").strip()
        if not source_text:
            continue
        cleaned_candidates.append({
            "evidence_id": ev_id,
            "source_text": source_text,
            "speaker": (c.get("speaker") or "Unknown").strip(),
            "context": (c.get("context") or "").strip(),
            "candidate_category": c.get("candidate_category") or "capability",
            "confidence": float(c.get("confidence") or 0.8),
        })

    print(f"[Stage 1] Successfully captured {len(cleaned_candidates)} atomic evidence candidate(s).")
    return cleaned_candidates
