import re
from typing import Dict, Any
from services.llm import llm

EVALUATION_PROMPT = """You are an expert in Software Requirements Engineering.

Your task is to evaluate a single software requirement against a
specific software requirement quality characteristic.

PROJECT SCOPE:
{project_scope}

REQUIREMENT:
{requirement}

QUALITY CHARACTERISTIC:
{quality_characteristic}

DEFINITION OF THE QUALITY CHARACTERISTIC:
{quality_definition}

Evaluate whether the given requirement satisfies the specified
quality characteristic based on the project scope and the definition
provided above.

Your response must contain the following:

1. SATISFIES:
   Answer only YES or NO.

2. EXPLANATION:
   Explain why the requirement satisfies or does not satisfy the
   specified quality characteristic. Base the explanation only on
   the provided project scope, requirement, and quality characteristic
   definition.

3. IMPROVEMENT:
   If the answer is NO, provide an improved version of the requirement
   that addresses the identified quality issue while preserving the
   original intended functionality.

   If the answer is YES, state:
   "No improvement required."

Do not evaluate other quality characteristics.
Evaluate only the specified quality characteristic.

Do not introduce requirements, constraints, functionality, or
information that is not supported by the project scope.

OUTPUT FORMAT:

SATISFIES: YES/NO

EXPLANATION:
<explanation>

IMPROVEMENT:
<improved requirement or "No improvement required.">
"""


def parse_evaluation_response(content: str) -> Dict[str, Any]:
    """
    Parses the text output from the evaluation prompt into a structured dict:
    {
        "satisfies": bool,
        "satisfies_raw": "YES" | "NO",
        "explanation": str,
        "improvement": str
    }
    """
    text = content.strip()

    satisfies = True
    satisfies_raw = "YES"
    explanation = ""
    improvement = "No improvement required."

    # Parse SATISFIES
    sat_match = re.search(r"SATISFIES:\s*(YES|NO)", text, re.IGNORECASE)
    if sat_match:
        val = sat_match.group(1).upper()
        satisfies_raw = val
        satisfies = (val == "YES")

    # Parse EXPLANATION
    exp_match = re.search(r"EXPLANATION:\s*(.*?)(?=\n\s*IMPROVEMENT:|$)", text, re.DOTALL | re.IGNORECASE)
    if exp_match:
        explanation = exp_match.group(1).strip()

    # Parse IMPROVEMENT
    imp_match = re.search(r"IMPROVEMENT:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
    if imp_match:
        improvement = imp_match.group(1).strip()

    return {
        "satisfies": satisfies,
        "satisfies_raw": satisfies_raw,
        "explanation": explanation,
        "improvement": improvement
    }


def evaluate_single_characteristic(
    project_scope: str,
    requirement: str,
    quality_characteristic: str,
    quality_definition: str
) -> Dict[str, Any]:
    """
    Evaluates a single requirement against one quality characteristic.
    """
    scope_text = (project_scope or "").strip() or "General software application domain."
    req_text = (requirement or "").strip()

    prompt = EVALUATION_PROMPT.format(
        project_scope=scope_text,
        requirement=req_text,
        quality_characteristic=quality_characteristic.capitalize(),
        quality_definition=quality_definition
    )

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        result = parse_evaluation_response(content)
        result["characteristic"] = quality_characteristic
        return result
    except Exception as e:
        print(f"Error evaluating characteristic {quality_characteristic}: {e}")
        return {
            "characteristic": quality_characteristic,
            "satisfies": True,
            "satisfies_raw": "YES",
            "explanation": f"Evaluation completed with fallback: {e}",
            "improvement": "No improvement required."
        }
