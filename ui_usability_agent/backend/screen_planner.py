import json
import os
import re
from typing import List, Dict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
# from langchain_ollama import ChatOllama  # Commented out for Groq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables and validate API key
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file. Please add it.")

SCREEN_PLANNER_PROMPT = """You are a senior software architect. 
Given a system description and its requirements, your job is to identify ALL the screens/pages that need to be built for this system.

For each screen, output:
- screen_id: short unique identifier (e.g., "login", "product_list")
- screen_name: human readable name (e.g., "User Login")
- screen_type: "auth" | "form" | "dashboard" | "list" | "detail" | "full-page"
- user_role: who uses this screen (e.g., "Customer", "Admin", "Unauthenticated User")
- purpose: one sentence describing what this screen does
- key_actions: list of things the user can DO on this screen
- relevant_frs: which FR IDs from the requirements are needed for this screen
- depends_on: which screen_id this screen links from (if any)
- priority: "High" | "Medium" | "Low" — build High priority screens first

IMPORTANT: Keep each screen object compact. Use short strings. Do not add extra fields.
Output ONLY a valid JSON array. No explanations. No markdown. Start directly with [

System description and requirements:
{system_input}
"""
def _clean_llm_output(raw_output: str) -> str:
    """Remove markdown code blocks and other common LLM artifacts."""
    raw_output = raw_output.strip()
    if raw_output.startswith("```json"):
        raw_output = raw_output[7:]
    if raw_output.startswith("```"):
        raw_output = raw_output[3:]
    if raw_output.endswith("```"):
        raw_output = raw_output[:-3]
    cleaned = raw_output.strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        return cleaned[start: end + 1]
    return cleaned


def _fix_json_string(raw: str) -> str:
    """Attempt common LLM JSON breakage repairs before parsing."""
    # Remove trailing commas before ] or }
    raw = re.sub(r',\s*([\]}])', r'\1', raw)
    # Replace smart/curly quotes with straight quotes
    raw = raw.replace('\u2018', "'").replace('\u2019', "'")
    raw = raw.replace('\u201c', '"').replace('\u201d', '"')
    return raw


def _recover_truncated_json(raw: str) -> str:
    """
    If the JSON array was truncated mid-stream (cut off before the closing ]),
    attempt to salvage all complete objects from the array.

    Strategy: extract every complete {...} object using a bracket-depth scan,
    then reassemble them into a valid array.
    """
    objects = []
    depth = 0
    start = None

    for i, ch in enumerate(raw):
        if ch == '{':
            if depth == 0:
                start = i          # beginning of a new top-level object
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                obj_str = raw[start: i + 1]
                try:
                    obj = json.loads(obj_str)
                    objects.append(obj)
                except json.JSONDecodeError:
                    pass           # skip malformed individual objects
                start = None

    if objects:
        return json.dumps(objects)  # reassemble as a valid JSON array string
    return raw                      # nothing salvageable — return original

# For planning (bumped to 3000 tokens — a full screen plan needs ~1500-2000)
fast_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    max_tokens=3000,
)

def plan_screens(system_input: Dict) -> List[Dict]:
    """
    Takes the full system input and returns an ordered list of screens to build.
    """
    llm = fast_llm
    prompt = ChatPromptTemplate.from_template(SCREEN_PLANNER_PROMPT)
    chain = prompt | llm | StrOutputParser()

    system_input_str = json.dumps(system_input, indent=2)

    for attempt in range(3):
        try:
            raw_output = chain.invoke({"system_input": system_input_str})
            cleaned_output = _clean_llm_output(raw_output)
            fixed_output = _fix_json_string(cleaned_output)

            # First try: parse as-is
            try:
                screens = json.loads(fixed_output)
            except json.JSONDecodeError as first_err:
                # Second try: attempt truncation recovery
                print(f"[screen_planner] Attempt {attempt + 1}: standard parse failed "
                      f"({first_err}). Trying truncation recovery...")

                # Show a snippet near the error to help diagnose
                pos = first_err.pos if hasattr(first_err, 'pos') else 0
                snippet = fixed_output[max(0, pos - 60): pos + 60]
                print(f"[screen_planner] Near error position: ...{snippet}...")

                recovered = _recover_truncated_json(fixed_output)
                screens = json.loads(recovered)   # raises if still broken
                print(f"[screen_planner] Truncation recovery succeeded — "
                      f"salvaged {len(screens)} screen(s).")

            # Sort by priority: High first, then Medium, then Low
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            screens.sort(key=lambda s: priority_order.get(s.get("priority", "Low"), 2))
            return screens

        except json.JSONDecodeError as e:
            print(f"[screen_planner] Warning: Attempt {attempt + 1} fully failed. Error: {e}")
            if attempt == 2:
                print("[screen_planner] Error: Failed to get valid JSON from LLM after 3 attempts.")
                return []

    return []

def screens_to_requirements(screens: List[Dict], base_requirements: Dict) -> List[Dict]:
    """
    Converts the screen plan into a list of per-screen requirement dicts.
    This function creates a lean, focused payload for the UI generator.
    """
    per_screen_reqs = []

    # These are high-level NFRs that are almost always relevant to the UI
    globally_relevant_nfr_types = ["Accessibility", "Responsiveness", "Dark Mode", "Usability"]
    all_nfrs = base_requirements.get("non_functional_requirements", [])
    relevant_nfrs = [
        nfr for nfr in all_nfrs
        if nfr.get("type") in globally_relevant_nfr_types
    ]

    for screen in screens:
        relevant_fr_ids = screen.get("relevant_frs", [])
        all_frs = base_requirements.get("functional_requirements", [])

        screen_specific_frs = [
            fr for fr in all_frs if fr.get("id") in relevant_fr_ids
        ] if relevant_fr_ids else []

        screen_req = {
            "project_name": base_requirements.get("project_name", "System"),
            "screen_id": screen.get("screen_id"),
            "screen_name": screen.get("screen_name"),
            "screen_type": screen.get("screen_type"),
            "user_role": screen.get("user_role"),
            "purpose": screen.get("purpose"),
            "key_actions": screen.get("key_actions", []),
            "functional_requirements": screen_specific_frs,
            "non_functional_requirements": relevant_nfrs,
        }
        per_screen_reqs.append(screen_req)

    return per_screen_reqs

def save_screen_plan(screens: List[Dict], output_path: str = os.path.join(os.path.dirname(__file__), "outputs", "screen_plan.json")):
    """Save the screen plan for inspection."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(screens, f, indent=2)
    print(f"\n[main] Screen plan saved to {output_path}")
    print(f"[main] {len(screens)} screens identified:")
    for i, s in enumerate(screens, 1):
        print(f"  {i}. [{s.get('priority', '?')}] {s.get('screen_name')} — {s.get('purpose', '')}")


