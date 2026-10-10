import json
import re
from typing import Dict, Any
from services.llm import llm

VALIDATE_DOC_PROMPT = """
You are an expert software requirements evaluator.

Analyze the following document content and determine whether it is a technical document related to software, IT systems, applications, project requirements, features, or digital product specifications.

ACCEPTABLE TECHNICAL DOCUMENTS:
- Software Requirements Specifications (SRS), PRDs, feature roadmaps, user stories
- System architecture, database designs, API specifications, technical briefs
- Meeting transcripts or notes discussing software development, requirements, or digital systems
- Project proposals and functional/technical specifications

NON-TECHNICAL / REJECTED DOCUMENTS:
- Cooking recipes, poems, fiction, literary essays, novels
- Grocery lists, general invoices, tax receipts, non-software financial records
- Resumes/CVs, personal letters, unrelated legal terms or medical reports
- Meaningless gibberish or general non-technical articles

DOCUMENT CONTENT (first portion):
\"\"\"
{content}
\"\"\"

Return ONLY valid JSON in the following format:
{{
  "is_technical": true,
  "confidence": 0.95,
  "reason": "Brief explanation of why this document is accepted or rejected."
}}
"""


def validate_technical_document(text: str) -> Dict[str, Any]:
    """
    Validates if the provided text is a technical/software requirements document.
    Returns {"is_technical": bool, "reason": str}
    """
    clean_text = (text or "").strip()
    if not clean_text or len(clean_text) < 20:
        return {
            "is_technical": False,
            "reason": "The uploaded document is empty or contains insufficient text to extract requirements."
        }

    # Sample representative portion of document
    sample = clean_text[:4000]

    prompt = VALIDATE_DOC_PROMPT.format(content=sample)

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Parse JSON
        import json_repair
        data = json_repair.loads(content)

        if isinstance(data, dict):
            is_tech = bool(data.get("is_technical", False))
            reason = data.get("reason", "Document does not appear to contain technical software requirements.")
            return {
                "is_technical": is_tech,
                "reason": reason
            }
    except Exception as e:
        print(f"Warning: Document validation error: {e}")

    # Fallback to true if LLM fails so user isn't blocked by transient error
    return {
        "is_technical": True,
        "reason": "Validation fallback."
    }
