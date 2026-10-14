import json
import os
import re
from services.llm import get_llm, llm


def build_prompt(transcript: str) -> str:
    # Find all speaker labels present in transcript (e.g. SPEAKER_00, SPEAKER_01, etc.)
    speakers = sorted(list(set(re.findall(r"SPEAKER_\d+", transcript))))
    if not speakers:
        speakers = ["SPEAKER_00"]

    example_json = "{\n" + ",\n".join([f'  "{spk}": "Business Analyst" or "Client"' for spk in speakers]) + "\n}"

    return f"""
You are analyzing a software requirements elicitation meeting transcript.

Participants are typically:
- The Business Analyst (asks questions, clarifies requirements, summarizes, guides scope)
- The Client (describes business needs, explains problems, requests features)

Map each detected speaker label present in the transcript to their role ("Business Analyst" or "Client").

Return ONLY valid JSON matching this schema:
{example_json}

Do not include markdown fences or explanation.

Transcript:
{transcript}
""".strip()


def identify_speakers(transcript: str) -> dict:
    prompt = build_prompt(transcript)
    response = llm.invoke(prompt)
    content = response.content.strip()

    content = content.replace("```json", "")
    content = content.replace("```", "").strip()

    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Safe fallback if JSON parsing fails
    return {"SPEAKER_00": "Business Analyst", "SPEAKER_01": "Client"}