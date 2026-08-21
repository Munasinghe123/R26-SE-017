import json
from services.llm.llm import llm


def build_prompt(
    transcript: str,
    speaker_roles: dict
) -> str:

    return f"""
You are cleaning a software requirements elicitation meeting transcript.

The following speaker labels correspond to these roles:

{speaker_roles}

Your tasks:

1. Replace speaker labels (e.g. SPEAKER_00) with the corresponding role names.
2. Remove ONLY:
   - greetings
   - farewells
   - obvious transcription artifacts
   - filler words (e.g. um, uh, hmm)
   - casual conversation that is completely unrelated to the software system.
3. Preserve ALL discussion related to:
   - functional requirements
   - non-functional requirements
   - business rules
   - constraints
   - assumptions
   - stakeholders
   - timelines
   - priorities
   - decisions
   - clarifying questions and their answers
4. Keep the original order of the conversation.
5. Keep the conversation format.

IMPORTANT RULES:

- Do NOT summarize.
- Do NOT paraphrase.
- Do NOT rewrite sentences.
- Do NOT improve grammar.
- Do NOT merge multiple statements into one.
- Do NOT invent new information.
- Do NOT remove any requirement-related question or answer.
- Preserve the original wording whenever possible.
- If you are unsure whether a sentence is requirement-related, KEEP IT.

Return ONLY the cleaned transcript.

Transcript:

{transcript}
"""


def clean_transcript(transcript:str , speaker_roles:dict) -> str: 
    prompt = build_prompt(
        transcript,
        speaker_roles
    )
    
    print("\n========== CLEANING LLM INPUT ==========")
    print("Transcript length:", len(transcript))
    print("Speaker roles:", speaker_roles)
    print("Prompt length:", len(prompt))
    print("========================================")

    response = llm.invoke(prompt)
    
    print("\n========== CLEANING LLM RESPONSE ==========")
    print("Response type:", type(response))
    print("Response content repr:", repr(response.content))
    print("Content length:", len(response.content))
    print("Full response:", response)
    print("===========================================")

    return response.content.strip()