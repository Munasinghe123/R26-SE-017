import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
from .extract_guidelines import (
    PURPOSE_GUIDELINES,
    SCOPE_GUIDELINES,
    PRODUCT_PERSPECTIVE_GUIDELINES,
    PRODUCT_FUNCTIONS_GUIDELINES,
    USER_CHARACTERISTICS_GUIDELINES,
    ASSUMPTIONS_AND_DEPENDENCIES_GUIDELINES,
    SPECIFIED_REQUIREMENTS_GUIDELINES,
    EXTERNAL_INTERFACES_GUIDELINES,
    DESIGN_CONSTRAINTS_GUIDELINES,
    STANDARDS_COMPLIANCE_GUIDELINES,
    SUPPORTING_INFORMATION_GUIDELINES,
    GLOBAL_RULES,
    OUTPUT_SCHEMA,
)
import re



load_dotenv()


llm = ChatOpenAI(
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url='https://openrouter.ai/api/v1', 
    model="meta-llama/llama-3.3-70b-instruct",
    temperature=0
)


def build_prompt(transcript: str) -> str:
    return f"""
You are a senior software requirements analyst.

Extract structured software requirements and other SRS-relevant information
from the provided client/BA meeting transcript.

The purpose of this extraction is to provide the information available from
the elicitation meeting for generation of an initial IEEE/ISO/IEC 29148
Software Requirements Specification (SRS) Version 1.

{PURPOSE_GUIDELINES}

{SCOPE_GUIDELINES}

{PRODUCT_PERSPECTIVE_GUIDELINES}

{PRODUCT_FUNCTIONS_GUIDELINES}

{USER_CHARACTERISTICS_GUIDELINES}

{ASSUMPTIONS_AND_DEPENDENCIES_GUIDELINES}

{SPECIFIED_REQUIREMENTS_GUIDELINES}

{EXTERNAL_INTERFACES_GUIDELINES}


{DESIGN_CONSTRAINTS_GUIDELINES}

{STANDARDS_COMPLIANCE_GUIDELINES}

{SUPPORTING_INFORMATION_GUIDELINES}

{GLOBAL_RULES}

{OUTPUT_SCHEMA}

MEETING TRANSCRIPT:
{transcript}
"""


def validate_extraction(data):
    if not isinstance(data, dict):
        return False

    required_fields = [
        "purpose",
        "scope",
        "product_perspective",
        "product_functions",
        "user_characteristics",
        "assumptions_and_dependencies",
        "specified_requirements",
        "external_interfaces",
        "design_constraints",
        "standards_compliance",
        "supporting_information",
    ]

    if not all(field in data for field in required_fields):
        return False

    # Product perspective
    perspective_fields = [
        "system_interfaces",
        "user_interfaces",
        "hardware_interfaces",
        "software_interfaces",
        "communications_interfaces",
        "memory_constraints",
        "operations",
        "site_adaptation_requirements",
        "service_interfaces",
    ]

    perspective = data["product_perspective"]

    if not isinstance(perspective, dict):
        return False

    if not all(field in perspective for field in perspective_fields):
        return False

    # Specified requirements
    specified = data["specified_requirements"]

    if not isinstance(specified, dict):
        return False

    if "functional" not in specified or "non_functional" not in specified:
        return False

    # FR / NFR structure
    for requirement_type in ["functional", "non_functional"]:
        requirements = specified[requirement_type]

        if not isinstance(requirements, list):
            return False

        for item in requirements:
            if not isinstance(item, dict):
                return False

            if "id" not in item or "description" not in item:
                return False

            if not isinstance(item["id"], str):
                return False

            if not isinstance(item["description"], str):
                return False

    return True

def parse_json_response(content: str):
    content = content.strip()

    # Remove markdown code fences if present
    content = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"```\s*", "", content)

    # Find the actual JSON object
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise json.JSONDecodeError("No JSON object found", content, 0)

    json_content = content[start:end + 1]

    try:
        return json.loads(json_content, strict=False)
    except json.JSONDecodeError:
        # Fallback: remove trailing commas before closing braces/brackets
        cleaned = re.sub(r",\s*([\]}])", r"\1", json_content)
        return json.loads(cleaned, strict=False)


def extract_requirements(transcript: str):
    print("\n========== EXTRACTION START ==========")

    prompt = build_prompt(transcript)

    print("Calling LLM for extraction...")

    response = llm.invoke(prompt)

    print("LLM extraction response received.")

    content = response.content.strip()

    print("\n========== RAW EXTRACTION RESPONSE ==========")
    print(content)
    print("=============================================")

    data = None
    try:
        data = parse_json_response(content)
        print("JSON parsing: SUCCESS")
    except Exception as e:
        print("JSON parsing: FAILED -", e)

    if data and isinstance(data, dict):
        print("Running schema validation...")
        if not validate_extraction(data):
            print("Schema validation: WARNING (minor structure mismatch, proceeding with extracted data)")
        else:
            print("Schema validation: SUCCESS")

        print("\n========== EXTRACTED STUFF ==========")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        print("=====================================")
        return data

    print("[WARNING] Could not parse valid JSON. Returning raw content container.")
    return {
        "error": "invalid_json",
        "raw": content
    }