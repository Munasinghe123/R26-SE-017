import re
import json


def clean_json_response(content):
    # Strip <think> tags
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    
   
    cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"```", "", cleaned)
    
    cleaned = cleaned.strip()

    # Remove common log prefixes if they leaked into content
    cleaned = re.sub(r"^\s*(INFO|ERROR|WARN|DEBUG):.*$", "", cleaned, flags=re.MULTILINE)

    decoder = json.JSONDecoder()

    # Try to decode the first complete JSON value even if the model appended extra text.
    for match in re.finditer(r"[\[{]", cleaned):
        start_index = match.start()
        try:
            parsed, _ = decoder.raw_decode(cleaned[start_index:])
            if isinstance(parsed, (dict, list)):
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[0]
                return parsed
        except json.JSONDecodeError:
            continue

    try:
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