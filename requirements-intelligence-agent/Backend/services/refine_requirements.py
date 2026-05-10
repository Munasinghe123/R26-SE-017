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

def extract_json(content: str):
    start = content.find("{")
    end = content.rfind("}") + 1
    return content[start:end]


def normalize_ids(data):
    if "functional" in data:
        for i, item in enumerate(data["functional"], 1):
            item["id"] = f"FR{i}"

    if "non_functional" in data:
        for i, item in enumerate(data["non_functional"], 1):
            item["id"] = f"NFR{i}"

    return data


def refine_requirements(old_requirements, feedback):
    prompt = f"""
You are a senior software requirements analyst.

You are given existing requirements and client feedback.

Your job:
- Modify requirements based on feedback
- Add new requirements if requested
- Remove irrelevant ones
- DO NOT duplicate requirements
- Keep each requirement atomic (one action per requirement)
- Maintain professional format: "The system shall..."

CRITICAL:
- Return ONLY valid JSON
- No explanations
- No extra text

OUTPUT FORMAT:

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

Existing Requirements:
{old_requirements}

Client Feedback:
{feedback}
"""

  
    response = llm.invoke(prompt)
    content = response.content.strip()

  
    content = content.replace("```json", "").replace("```", "").strip()

    
    content = extract_json(content)

    try:
        data = json.loads(content)
    except Exception:
        return {
            "error": "invalid_json",
            "raw": content
        }

    data = normalize_ids(data)

    return data