import json

from services.llm.llm import llm

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
        raise json.JSONDecodeError(
            "No JSON object found",
            content,
            0
        )

    json_content = content[start:end + 1]

    return json.loads(json_content)

def extract_requirements(transcript: str):
    print("\n========== EXTRACTION START ==========")

    prompt = build_prompt(transcript)

    print("Calling Groq for extraction...")

    response = llm.invoke(prompt)

    print("Groq extraction response received.")

    print("Response metadata:")
    print(response.response_metadata)

    print("Content length:", len(response.content))

    content = response.content.strip()

    # print("\n========== RAW EXTRACTION RESPONSE ==========")
    # print(content)
    # print("=============================================")

    try:
        data = parse_json_response(content)
        print("JSON parsing: SUCCESS")

    except json.JSONDecodeError as e:
        print("JSON parsing: FAILED")
        print("Error:", e)

        return {
            "error": "invalid_json",
            "raw": content
        }

    print("Running schema validation...")

    if not validate_extraction(data):
        print("Schema validation: FAILED")

        return {
            "error": "invalid_structure",
            "raw": content
        }

    print("Schema validation: SUCCESS")

    print("\n========== EXTRACTED STUFF ==========")
    print(json.dumps(data, indent=4, ensure_ascii=False))
    print("=====================================")

    return data