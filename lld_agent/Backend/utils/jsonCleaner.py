import re
import json


def clean_json_response(content):
    # Strip <think> tags
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    
   
    cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"```", "", cleaned)
    
    cleaned = cleaned.strip()

    # Extract the first complete JSON object in case of extra logs/noise
    start_index = cleaned.find("{")
    end_index = cleaned.rfind("}")

    if start_index != -1 and end_index != -1 and end_index > start_index:
        cleaned = cleaned[start_index:end_index + 1]

    # Remove common log prefixes if they leaked into content
    cleaned = re.sub(r"^\s*(INFO|ERROR|WARN|DEBUG):.*$", "", cleaned, flags=re.MULTILINE)

    try:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            cleaned = cleaned[start:end + 1]

        parsed = json.loads(cleaned, strict=False)

        if isinstance(parsed, list) and len(parsed) > 0:
            parsed = parsed[0]

        return parsed

    except json.JSONDecodeError:

        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

        parsed = json.loads(cleaned, strict=False)

        if isinstance(parsed, list) and len(parsed) > 0:
            parsed = parsed[0]

        return parsed