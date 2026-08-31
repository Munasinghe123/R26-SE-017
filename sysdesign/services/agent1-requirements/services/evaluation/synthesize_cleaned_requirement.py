import re
from typing import Dict, Any, List
from services.llm import llm

SYNTHESIZE_PROMPT = """You are a senior Software Requirements Engineer.

A software requirement was evaluated against ISO/IEC/IEEE 29148 quality characteristics and received specific improvement feedback.

PROJECT SCOPE:
{project_scope}

ORIGINAL REQUIREMENT:
{original_requirement}

IDENTIFIED QUALITY ISSUES AND SUGGESTED IMPROVEMENTS:
{issues_and_improvements}

Your task:
Synthesize a single, clear, standardized, IEEE-compliant software requirement statement that resolves all the identified quality issues while strictly preserving the original intended functionality and business capability.

RULES:
1. Output ONLY the single final improved requirement text.
2. Ensure the requirement begins with "The system shall" (or "The platform shall").
3. Do NOT include explanatory notes, bullet points, or multiple options.
4. Ensure it satisfies all 9 IEEE quality characteristics (unambiguous, complete, verifiable, conforming, singular, etc.).

IMPROVED REQUIREMENT:
"""


def synthesize_cleaned_requirement(
    project_scope: str,
    original_requirement: str,
    evaluations: Dict[str, Dict[str, Any]]
) -> str:
    """
    If any characteristic failed, synthesizes a unified clean requirement.
    If all passed, returns the original requirement.
    """
    failed_items = [
        (char_name, eval_data)
        for char_name, eval_data in evaluations.items()
        if not eval_data.get("satisfies", True)
    ]

    if not failed_items:
        return original_requirement.strip()

    # Build issues list for synthesis
    issues_text = ""
    for char_name, eval_data in failed_items:
        issues_text += f"- Quality Characteristic: {char_name.capitalize()}\n"
        issues_text += f"  Explanation: {eval_data.get('explanation')}\n"
        issues_text += f"  Suggested Fix: {eval_data.get('improvement')}\n\n"

    prompt = SYNTHESIZE_PROMPT.format(
        project_scope=project_scope or "General software application domain.",
        original_requirement=original_requirement,
        issues_and_improvements=issues_text.strip()
    )

    try:
        response = llm.invoke(prompt)
        cleaned = response.content.strip()

        # Strip any accidental preamble/fences
        cleaned = re.sub(r"^IMPROVED REQUIREMENT:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"```.*?", "", cleaned)
        cleaned = cleaned.strip(' "\n`')
        if cleaned:
            return cleaned
    except Exception as e:
        print(f"Warning: Synthesize cleaned requirement error: {e}")

    # Fallback to first available non-empty improvement
    for _, eval_data in failed_items:
        imp = eval_data.get("improvement", "")
        if imp and imp != "No improvement required." and len(imp) > 10:
            return imp.strip()

    return original_requirement.strip()
