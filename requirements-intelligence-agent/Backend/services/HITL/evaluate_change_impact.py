import json

from services.llm.llm import llm


IMPACT_ANALYSIS_PROMPT = """
You are analyzing changes made by a business client during a
software requirements review.

Your job is to determine the SEMANTIC AND BUSINESS IMPACT of
each affected requirement and decide whether the client needs
to provide additional business information.

IMPORTANT:

A requirement being edited, deleted, or added does NOT
automatically mean that clarification is required.

A change should require clarification ONLY when an important
business decision remains missing, ambiguous, or conflicting.

Your analysis must focus on what the CLIENT means from a
business perspective, not how the system would be implemented.

For each affected requirement:

1. Identify what changed.

2. Classify the semantic impact using EXACTLY ONE of:

   - wording_change
   - scope_change
   - new_capability
   - removed_capability
   - conflicting_change
   - unclear_change
   - no_significant_change

3. Explain the business meaning of the change.

4. Determine whether important business information is still
   missing, ambiguous, or conflicting.

5. Set "requires_clarification" to true ONLY when additional
   information from the client is necessary to clearly define
   the intended business requirement.

==================================================
CHANGE TYPES
==================================================

EDITED REQUIREMENTS:

For an edited requirement:

- Compare the original requirement with the client's new
  version.
- Determine whether the business meaning actually changed.
- If only wording or precision changed, classify it as
  "wording_change".
- If the new version introduces a new business rule, scope,
  responsibility, or capability, classify the appropriate
  impact type.
- Do NOT require clarification if the new requirement is already
  sufficiently defined.

Example:

Original:
"Customers receive a reminder email one day before their
appointment."

New:
"Customers receive a reminder email 24 hours before their
appointment."

The wording has become more precise, but the business meaning
has not changed.

Therefore:

"impact_type": "wording_change"
"requires_clarification": false


DELETED REQUIREMENTS:

For a deleted requirement:

- Determine what business capability was removed.
- Do NOT assume that the client wants a replacement.
- Do NOT invent an alternative process.
- A deletion is not automatically ambiguous.
- If the client clearly removed the capability and no important
  business decision remains unresolved, set
  "requires_clarification": false.
- Set "requires_clarification": true only when the deletion
  creates an important unresolved business question.

Example:

Original:
"Staff can generate monthly sales reports."

Client deletes the requirement.

If the client clearly intends to remove reporting, this does
not automatically require clarification.

Therefore:

"impact_type": "removed_capability"
"requires_clarification": false


ADDED REQUIREMENTS:

For an added requirement:

- Treat the client's text as a newly introduced business
  capability.
- Determine whether the new capability is sufficiently defined.
- Identify only important business rules that are genuinely
  necessary to understand the intended capability.
- A new requirement does NOT automatically require
  clarification.
- Do NOT invent missing rules simply because additional details
  could theoretically exist.
- Only require clarification when the missing information is
  necessary to clearly understand or define the intended
  business behavior.

Example:

Added requirement:
"Customers can save products to a wishlist for later."

This introduces a new capability.

If important business behavior is not defined and that missing
information is necessary to understand how the wishlist should
work, clarification may be required.

However, do NOT automatically ask about every possible detail,
such as implementation, database behavior, or optional features.

Determine whether clarification is genuinely necessary based
ONLY on the information provided.


==================================================
CLARIFICATION RULES
==================================================

Set:

"requires_clarification": false

when:

- The change only improves wording.
- The client makes an existing requirement more precise.
- The new requirement is already sufficiently defined.
- The business meaning is clear.
- The change does not introduce an unresolved business
  decision.
- A deleted requirement is clearly and intentionally removed.
- An added requirement clearly defines the intended business
  behavior.
- The requirement can be understood without additional
  information from the client.

Set:

"requires_clarification": true

ONLY when:

- A new capability is introduced but important business rules
  necessary to define that capability are missing.
- The new requirement is ambiguous.
- The change creates a conflict with another requirement.
- A business rule has changed but the new rule is incomplete.
- A change in roles or responsibilities leaves an important
  business decision unresolved.
- A deletion creates uncertainty about an important business
  expectation.
- The client must make a business decision before the
  requirement can be considered sufficiently defined.


==================================================
IMPORTANT DISTINCTION
==================================================

DO NOT ask questions merely because something changed.

The following are NOT sufficient reasons for clarification:

- The requirement was edited.
- The requirement was deleted.
- The requirement was added.
- More details could theoretically be provided.
- A developer might need additional implementation details.
- The system could have additional technical rules.

The question is:

"Can we understand the intended BUSINESS REQUIREMENT from the
information provided?"

If YES:

"requires_clarification": false

If NO because an important business decision is missing:

"requires_clarification": true.


==================================================
BUSINESS SCOPE
==================================================

Focus ONLY on business meaning and business requirements.

Do NOT discuss:

- programming languages
- databases
- APIs
- frameworks
- architecture
- implementation
- technical mechanisms
- system design
- database design
- concurrency mechanisms
- security mechanisms
- authentication mechanisms
- infrastructure
- deployment
- code
- algorithms


==================================================
DO NOT INVENT INFORMATION
==================================================

Use ONLY the information provided in:

- ORIGINAL REQUIREMENTS
- CLIENT CHANGE SET
- CHANGE ANALYSIS

Do NOT invent:

- features
- workflows
- permissions
- approval processes
- policies
- roles
- business rules
- customer behavior
- staff behavior
- replacement processes
- alternative channels

unless they are explicitly supported by the provided information.

If information is missing, that may be a reason for
"requires_clarification": true, but do not invent the missing
information yourself.


==================================================
DO NOT GENERATE QUESTIONS
==================================================

Your job is ONLY to analyze the impact and determine whether
clarification is required.

Do NOT generate clarification questions.

The question-generation component will handle that separately.


==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{
    "impacts": [
        {
            "requirement_id": "FR-1",
            "impact_type": "new_capability",
            "description": "The client introduced a new capability that is not yet sufficiently defined.",
            "requires_clarification": true
        }
    ]
}

Rules for the output:

- Include one impact object for each affected requirement.
- Do not include unaffected requirements.
- Use the requirement ID provided in CHANGE ANALYSIS.
- For newly added requirements, use their provided temporary ID
  such as "new-1", "new-2", etc.
- Do not create new requirement IDs.
- "impact_type" must be exactly one of the allowed impact types.
- "requires_clarification" must be either true or false.
- Return no text outside the JSON object.
"""

def evaluate_change_impact(
    requirements,
    change_set,
    change_analysis
):
    
    specified_requirements = requirements.get(
        "specified_requirements",
        {}
    )

    prompt = f"""
{IMPACT_ANALYSIS_PROMPT}

ORIGINAL REQUIREMENTS:
{json.dumps(specified_requirements, indent=2, ensure_ascii=False)}

CLIENT CHANGE SET:
{json.dumps(change_set, indent=2, ensure_ascii=False)}

CHANGE ANALYSIS:
{json.dumps(change_analysis, indent=2, ensure_ascii=False)}
"""

    response = llm.invoke(prompt)

    return json.loads(response.content)