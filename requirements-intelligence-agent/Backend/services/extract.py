import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


def build_prompt(transcript: str) -> str:
    return f"""
You are a senior software requirements analyst.

Your task is to extract and classify software requirements from the given input text and
find who the end users are.


STRICT DEFINITIONS:

Functional Requirements (FR):
- Describe WHAT the system must do
- Features, behaviors, user actions
- Must start with: "The system shall..."

Non-Functional Requirements (NFR):
- Describe HOW the system performs
- Performance, scalability, security, reliability, usability

IMPORTANT NFR RULES:
- Only include valid system quality attributes (performance, scalability, security, reliability, usability)
- If NFRs are weakly implied by the context, infer only highly reasonable and commonly expected system quality attributes.
- Ensure 3–5 meaningful NFRs when possible
- Do NOT invent unrealistic or unrelated constraints
- Avoid vague terms like "good", "decent", "efficient"
- Prefer clear and specific descriptions

- DO NOT include:
  - project timelines
  - development strategies
  - business goals
  

IMPORTANT FORMATTING RULES:
- Each requirement must represent ONLY ONE action
- DO NOT combine multiple actions
- Each must be independently testable
- Do NOT duplicate items
- Use clear and professional language

CRITICAL:
- Return ONLY valid JSON
- Do NOT include any explanation or text
- Your response must start with '{' and end with '}'
- If you include anything else, the response is INVALID

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "functional": [
    {{
      "id": "FR1",
      "description": "The system shall ..."
    }}
  ],
  "non_functional": [
    {{
      "id": "NFR1",
      "description": "The system shall ..."
    }}
  ]
}}

If no valid requirements exist, return empty arrays.

Input Text:
{transcript}
"""


def validate_requirements(data):
    if not isinstance(data, dict):
        return False

    if "functional" not in data or "non_functional" not in data:
        return False

    for item in data["functional"]:
        if "id" not in item or "description" not in item:
            return False

    for item in data["non_functional"]:
        if "id" not in item or "description" not in item:
            return False

    return True



INVALID_NFR_KEYWORDS = [
    "timeline",
    "phase",
    "priority",
    "development",
    "plan"
]


def filter_nfrs(nfrs):
    cleaned = []
    for item in nfrs:
        desc = item["description"].lower()
        if not any(word in desc for word in INVALID_NFR_KEYWORDS):
            cleaned.append(item)
    return cleaned


def extract_requirements(transcript: str):
    prompt = build_prompt(transcript)

    response = llm.invoke(prompt)
    content = response.content.strip()

    content = content.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(content)
    except Exception:
        return {
            "error": "invalid_json",
            "raw": content
        }

    if not validate_requirements(data):
        return {
            "error": "invalid_structure",
            "raw": content
        }

   
    data["non_functional"] = filter_nfrs(data["non_functional"])

    return data