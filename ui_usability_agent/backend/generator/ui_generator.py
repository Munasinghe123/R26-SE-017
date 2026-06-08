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

def generate_ui(requirements: dict, screen_type: str) -> str:
    """
    Generate HTML UI from software requirements using an LLM.

    Args:
       requirements: A dictionary containing software requirements.
       screen_type: The specific type of screen to generate (e.g., 'auth', 'list').

    Returns:
       The generated HTML as a string.
    """
    # Read the enhanced prompt template
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "generation_prompt.txt"), "r", encoding="utf-8") as f:
        prompt_template_string = f.read()

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
    