# Sends prompt to Ollama, gets HTML back
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
# from langchain_ollama import ChatOllama  # Commented out for Groq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

#load secret key from .env file
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file. Please add it.")

# For HTML generation (quality matters)
gen_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.4,
    max_tokens=4000,
)

def get_llm():
    """Create and return a ChatGroq instance"""
    return gen_llm

def _load_prompt_with_addendum(prompt_filename: str, addendum_filename: str, insert_before: str) -> str:
    """
    Loads a base prompt file and injects a smaller addendum file just before
    a given marker string. Keeps large base prompts (generation/refinement)
    untouched in source, so new mandatory rules can be added/removed without
    editing or re-measuring the main prompt's token footprint.
    """
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

    with open(os.path.join(prompts_dir, prompt_filename), "r", encoding="utf-8") as f:
        base = f.read()

    addendum_path = os.path.join(prompts_dir, addendum_filename)
    if not os.path.exists(addendum_path):
        return base

    with open(addendum_path, "r", encoding="utf-8") as f:
        addendum = f.read().strip()

    if insert_before in base:
        return base.replace(insert_before, addendum + "\n\n" + insert_before, 1)

    # Marker not found — append at the end rather than silently dropping the rule
    return base + "\n\n" + addendum

def generate_ui(requirements: dict, screen_type: str) -> str:
    """
    Generate HTML UI from software requirements using an LLM.

    Args:
       requirements: A dictionary containing software requirements.
       screen_type: The specific type of screen to generate (e.g., 'auth', 'list').

    Returns:
       The generated HTML as a string.
    """
    prompt_template_string = _load_prompt_with_addendum(
        "generation_prompt.txt",
        "traceability_addendum.txt",
        insert_before="================================================================================\nHTML BOILERPLATE",
    )

    # Create the prompt template
    prompt_template = ChatPromptTemplate.from_template(
        template=prompt_template_string,
        template_format="jinja2"
    )
    
    # Convert requirements to JSON string for the prompt
    requirements_json_string = json.dumps(requirements, indent=2)

    llm = get_llm()

    chain = prompt_template | llm | StrOutputParser()

    generated_html = chain.invoke({
        "requirements_json": requirements_json_string,
        "screen_name": requirements.get("screen_name", "Untitled Screen"),
        "screen_type_explicit": screen_type
    })

    return generated_html
def refine_ui(existing_html: str, requirements: dict, screen_type: str, instructions: str) -> str:
    """
    Revise an already-generated HTML screen to fix one targeted usability/
    accessibility weakness, instead of regenerating the whole page from
    scratch. Used by generator/refinement_controller.py.

    Args:
        existing_html: The HTML produced by a previous generate_ui()/refine_ui() call.
        requirements:  The same per-screen requirements dict used originally.
        screen_type:   The screen type (e.g. 'list', 'form', 'auth', 'detail').
        instructions:  Targeted fix instructions from
                        prompts.refinement_templates.get_refinement_instructions().

    Returns:
        The revised HTML as a string.
    """
    prompt_template_string = _load_prompt_with_addendum(
        "refinement_prompt.txt",
        "traceability_refinement_addendum.txt",
        insert_before="================================================================================\nCONTEXT",
    )
    
    prompt_template = ChatPromptTemplate.from_template(
        template=prompt_template_string,
        template_format="jinja2"
    )

    requirements_json_string = json.dumps(requirements, indent=2)

    llm = get_llm()
    chain = prompt_template | llm | StrOutputParser()

    revised_html = chain.invoke({
        "existing_html": existing_html,
        "instructions": instructions,
        "requirements_json": requirements_json_string,
        "screen_type_explicit": screen_type,
    })

    return revised_html
    