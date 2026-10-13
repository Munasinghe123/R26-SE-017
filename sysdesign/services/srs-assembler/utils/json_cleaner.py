import json
import re
from typing import Any

def clean_json_response(content: str) -> Any:
    """
    Cleans an LLM response string and parses it as JSON.
    Strips reasoning blocks (<think>...</think>), markdown code fences (```json ... ```),
    and leading/trailing whitespace.
    """
    if not content:
        raise json.JSONDecodeError("Empty content", "", 0)

    text = content.strip()

    # Remove reasoning/thinking tags (e.g. DeepSeek-R1 or Qwen)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code fences if present
    if "```" in text:
        # Match ```json ... ``` or just ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()
        else:
            # Fallback: remove all ``` markers
            text = text.replace("```json", "").replace("```", "").strip()

    # Find the outermost JSON structure if there is leading/trailing text
    # Look for first { or [
    start_bracket = -1
    for i, ch in enumerate(text):
        if ch in ("{", "["):
            start_bracket = i
            break

    if start_bracket != -1:
        end_char = "}" if text[start_bracket] == "{" else "]"
        end_bracket = text.rfind(end_char)
        if end_bracket != -1 and end_bracket > start_bracket:
            text = text[start_bracket : end_bracket + 1]

    return json.loads(text)
