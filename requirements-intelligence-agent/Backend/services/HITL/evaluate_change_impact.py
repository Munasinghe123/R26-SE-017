import json

from services.llm.llm import llm


IMPACT_ANALYSIS_PROMPT = """
You are analyzing changes made by a business client
during software requirements review.

Your task is to determine the semantic impact of each
client change on the affected software requirements.

For each affected requirement:

1. Identify what changed.
2. Determine the type of impact.
3. Explain the business meaning of the change.
4. Determine whether clarification is required.

Possible impact types:

- wording_change
- scope_change
- new_capability
- removed_capability
- conflicting_change
- unclear_change
- no_significant_change

Do NOT rewrite the requirement.
Do NOT generate questions yet.

Return ONLY valid JSON:

{
    "impacts": [
        {
            "requirement_id": "FR-1",
            "impact_type": "new_capability",
            "description": "The client introduced a new capability.",
            "requires_clarification": true
        }
    ]
}
"""


def evaluate_change_impact(
    requirements,
    change_set,
    change_analysis
):

    prompt = f"""
{IMPACT_ANALYSIS_PROMPT}

ORIGINAL REQUIREMENTS:
{json.dumps(requirements, indent=2, ensure_ascii=False)}

CLIENT CHANGE SET:
{json.dumps(change_set, indent=2, ensure_ascii=False)}

CHANGE ANALYSIS:
{json.dumps(change_analysis, indent=2, ensure_ascii=False)}
"""

    response = llm.invoke(prompt)

    return json.loads(response.content)