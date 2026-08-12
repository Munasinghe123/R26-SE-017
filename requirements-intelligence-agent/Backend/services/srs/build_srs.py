import os
from typing import Dict
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


def build_srs(requirements) -> Dict:

    functional = requirements.get("functional", [])
    non_functional = requirements.get("non_functional", [])

    functional_text = "\n".join([
        f"FR-{i+1}: {req['description']}"
        for i, req in enumerate(functional)
    ])

    non_functional_text = "\n".join([
        f"NFR-{i+1}: {req['description']}"
        for i, req in enumerate(non_functional)
    ])

    prompt = f"""
                You are a senior Business Analyst with expertise in ISO/IEC/IEEE 29148:2018 Software Requirements Specifications.

                Your task is to generate ONLY the missing Software Requirements Specification (SRS) sections.

                The Functional Requirements and Non-Functional Requirements have already been extracted and MUST NOT be regenerated or modified.

                Return ONLY valid JSON.

                The JSON must exactly match this structure:

                {{
                    "purpose": "",
                    "scope": "",
                    "product_perspective": "",
                    "product_functions": [],
                    "user_characteristics": [],
                    "assumptions_and_dependencies": []
                }}

                Use the following extracted requirements ONLY as context.

                Functional Requirements

                {functional_text}

                Non-Functional Requirements

                {non_functional_text}

                Generation Rules

                - Generate ONLY the JSON fields shown above.
                - Do NOT generate the Specified Requirements section.
                - Do NOT rewrite, modify or summarize the extracted requirements.
                - Generate only information that can be reasonably inferred from the provided requirements. If a section cannot be confidently inferred, return an empty string ("") for text fields or an empty array ([]) for list fields.
                - Do not invent functionality that is unsupported by the provided requirements.
                - Keep the writing formal, concise and professional.
                - Ensure every generated section is internally consistent with the provided requirements.
                - Return ONLY valid JSON.
                - Do NOT include markdown.
                - Do NOT include explanations.
                - Do NOT include code fences.
                """

    response = llm.invoke(prompt)

    return response.content