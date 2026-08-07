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
                You are analyzing a software requirements elicitation meeting.

                One participant is the Business Analyst.
                The other participant is the Client.

                The Business Analyst typically:
                - asks questions
                - clarifies requirements
                - summarizes
                - suggests solutions
                - guides the discussion

                The Client typically:
                - describes business needs
                - explains current problems
                - answers questions
                - requests features

                Return ONLY valid JSON with EXACTLY these keys:

                {{
                    "SPEAKER_00": "...",
                    "SPEAKER_01": "..."
                }}

                Do not add any other speaker labels.

                Transcript:

                {transcript}
            """

def identify_speakers(transcript: str) -> dict:

    prompt = build_prompt(transcript)

    response = llm.invoke(prompt)

    content = response.content.strip()

    content = content.replace("```json", "")
    content = content.replace("```", "").strip()

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        print("Invalid JSON returned by LLM:")
        print(content)
        raise