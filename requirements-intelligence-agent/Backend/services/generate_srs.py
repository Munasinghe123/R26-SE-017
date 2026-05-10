import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


def generate_srs(requirements):

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
You are a senior Business Analyst and Software Architect.

Generate a professional IEEE-style Software Requirements Specification (SRS) document.

The document must be formal, structured, and suitable for an academic research demonstration or real-world software project documentation.

DOCUMENT STRUCTURE:

1. INTRODUCTION
   1.1 Purpose
   1.2 Scope
   1.3 Intended Audience
   1.4 System Overview

2. OVERALL DESCRIPTION
   2.1 Product Perspective
   2.2 User Classes and Characteristics
   2.3 Operating Environment
   2.4 Assumptions and Dependencies

3. FUNCTIONAL REQUIREMENTS

4. NON-FUNCTIONAL REQUIREMENTS

5. SYSTEM CONSTRAINTS

6. FUTURE ENHANCEMENTS

7. CONCLUSION

FUNCTIONAL REQUIREMENTS:
{functional_text}

NON-FUNCTIONAL REQUIREMENTS:
{non_functional_text}

STRICT RULES:

- Output plain text only.
- Do NOT use markdown.
- Do NOT use bullet symbols like *, -, or •.
- Use professional enterprise documentation language.
- Use numbered requirement formatting.

Functional requirement format example:
FR-1: The system shall allow users to upload meeting transcripts.

Non-functional requirement format example:
NFR-1: The system shall generate the SRS document within 30 seconds.

- Every requirement MUST begin with:
  "The system shall..."

- Expand requirements professionally where appropriate.
- Avoid repetition.
- Keep tone formal and technical.
- Do not invent unrealistic features.
- Make the document look like a real SRS used in industry.
"""

    response = llm.invoke(prompt)

    return response.content