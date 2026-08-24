import json

from services.llm.llm import llm


QUESTION_GENERATION_PROMPT = """
You generate targeted business clarification questions
for a software requirements review.

The client has already reviewed the requirements and made
changes. Another component has already identified the
semantic impact of those changes.

Your job is to identify the BUSINESS INFORMATION that is
still missing and generate concise questions that resolve
those gaps.

RULES:

1. Questions must be understandable by a non-technical
   business client.

2. Do not use technical implementation terminology.

3. Do not ask about programming languages, databases,
   APIs, frameworks, architecture, or implementation.

4. Only ask questions directly related to the identified
   change and its impact.

5. Do not ask for information that is already explicitly
   provided.

6. Do not invent new features or assumptions.

7. For removed capabilities, verify whether the client
   truly intends to remove the capability.

8. For new capabilities, clarify the important business
   rules needed to define the capability.

9. For scope or role changes, clarify responsibilities
   and boundaries.

10. Generate only the questions necessary to resolve
    meaningful ambiguity.

11. Generate between 1 and 4 questions for each affected
    requirement when clarification is required.

12. Return ONLY valid JSON.

OUTPUT:

{
    "questions": [
        {
            "id": "Q-1",
            "requirement_id": "FR-1",
            "question": "Business-oriented question",
            "reason": "Why this information is needed"
        }
    ]
}
"""

def generate_targeted_questions(
  
    change_analysis,
    change_impacts
):

    prompt = f"""
{QUESTION_GENERATION_PROMPT}


CHANGE ANALYSIS:
{json.dumps(change_analysis, indent=2, ensure_ascii=False)}

CHANGE IMPACTS:
{json.dumps(change_impacts, indent=2, ensure_ascii=False)}
"""

    response = llm.invoke(prompt)

    return json.loads(response.content)