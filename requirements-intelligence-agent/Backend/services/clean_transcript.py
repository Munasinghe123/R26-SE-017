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

    response = llm.invoke(prompt)

    return response.content.strip()