from __future__ import annotations

from skills.uml.skill import Skill

COMMON_UML_SKILL = Skill(
    name="common_uml",
    instructions="""
Use the supplied requirements as the semantic source of truth.

Do not introduce functionality, concepts, responsibilities, or data that are
not supported by the requirements or explicitly supplied architecture.

When validated diagrams from earlier stages are provided, treat them as
structural source-of-truth inputs and preserve their canonical names.

Return ONLY valid JSON.
Root value must be an object.
No markdown, code fences, comments, explanations, or reasoning.
Use double quotes.
Do not truncate the response.
Do not include fields outside the required schema.
""".strip(),
)
