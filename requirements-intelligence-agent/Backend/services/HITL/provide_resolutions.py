import json

from services.llm.llm import llm


def provide_resolutions(
    clarification_questions,
    client_answers,
    change_impacts
):

    prompt = f"""
You are a senior requirements analyst.

Determine how the client's clarification answers
resolve the identified requirement changes.

CLARIFICATION QUESTIONS:
{json.dumps(clarification_questions, ensure_ascii=False)}

CLIENT ANSWERS:
{json.dumps(client_answers, ensure_ascii=False)}

CHANGE IMPACTS:
{json.dumps(change_impacts, ensure_ascii=False)}

For each answered question:

1. Identify the affected requirement.
2. Determine whether the answer resolves the ambiguity.
3. Determine the appropriate resolution:
   - update
   - delete
   - keep
   - unresolved
4. If an update is required, produce the revised
   requirement wording.
5. Do not invent information not provided by the client.
6. Do not modify unrelated requirements.
7. If the answer is insufficient, mark it unresolved.
8. Return ONLY valid JSON.

OUTPUT:

{{
  "resolutions": [
    {{
      "question_id": "Q-1",
      "requirement_id": "FR-1",
      "resolution_type": "update",
      "status": "confirmed",
      "resolved_requirement": "...",
      "reason": "..."
    }}
  ]
}}
"""

    response = llm.invoke(prompt)

    return json.loads(response.content)