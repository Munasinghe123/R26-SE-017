import json
import re

from services.llm.llm import llm


CLASSIFICATION_PROMPT = """
You are a senior software requirements analyst.

You will receive a list of requirements that were just extracted from a
meeting transcript. Some may have been classified incorrectly as
functional when they are actually non-functional, or vice versa.

Re-classify EVERY requirement as either:

- functional
- non_functional

DECISION RULE (apply this test to every requirement):

Ask: "Does this requirement describe WHAT the system does (an action or
capability), or HOW WELL / under what constraint it does something (a
quality attribute)?"

- If the main verb describes a system action or capability
  ("the system shall allow/generate/send/store/display/calculate X"),
  it is FUNCTIONAL — even if the sentence also mentions a quality word
  in passing (e.g. "securely store").

- If the requirement's entire content is a quality attribute —
  performance, response time, security, availability, usability,
  scalability, reliability, maintainability, portability — with no
  distinct new action being introduced, it is NON_FUNCTIONAL.

EXAMPLES:

"The system shall allow staff to reset a customer's password."
-> functional (describes an action)

"The system shall reset passwords within 2 seconds of the request."
-> non_functional (the entire content is a performance constraint on
   an action, not the action itself)

"The system shall encrypt customer payment data at rest."
-> non_functional (security/quality attribute, even though it has a verb)

"The system shall allow customers to submit payment information."
-> functional (describes the capability; encryption of that data is a
   separate NFR if stated separately)

"The system shall support 500 concurrent users."
-> non_functional (scalability constraint, no new action)

"The system shall allow staff to manage services, schedules, and
appointments without technical knowledge or developer assistance."
-> non_functional (usability constraint. The capability to "manage
   services/schedules" is ALREADY covered by other functional
   requirements elsewhere. This sentence adds nothing new about WHAT
   the system does — it only constrains HOW USABLE that existing
   capability must be, i.e. no technical training required. Any
   requirement whose real payload is "without needing X skill/
   assistance/expertise" is a usability NFR, even though it is
   phrased with "allow ... to").

RULE OF THUMB FOR "WITHOUT NEEDING X" / "NO TECHNICAL SKILL REQUIRED"
PHRASING:

This pattern can appear in many different surface forms, such as:
- "allow staff to do Y without needing Z"
- "provide an interface that staff can use without Z"
- "enable non-technical users to do Y"
- "staff shall be able to do Y without developer assistance"

Regardless of the exact wording, if the requirement's core payload is
a claim about ease-of-use, required skill level, or independence from
technical/developer assistance — and the underlying action (Y) is
already covered by a separate functional requirement elsewhere — this
is a USABILITY constraint, not new functional scope.

Test: strip away the "without needing X" / "non-technical" /
"can be used by anyone" clause. If what remains is just a restatement
of an action already captured elsewhere, classify as non_functional.
If what remains describes a genuinely new, distinct system action,
classify as functional.

IMPORTANT:

1. Classify based only on the requirement text (the "description" field).
2. Do NOT change the requirement text.
3. Preserve the requirement "id" exactly.
4. Do NOT create new ids.
5. Every requirement supplied must receive exactly one classification.
6. Do not add explanations.
7. Return ONLY valid JSON.

OUTPUT FORMAT:

{
    "requirements": [
        {
            "id": "FR-1",
            "type": "functional"
        }
    ]
}
"""


def parse_json_response(content: str):

    content = content.strip()

    content = re.sub(
        r"```json\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"```\s*",
        "",
        content
    )

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise json.JSONDecodeError(
            "No JSON object found",
            content,
            0
        )

    return json.loads(
        content[start:end + 1]
    )


def validate_classification(data, source_items):

    if not isinstance(data, dict):
        raise ValueError(
            "Classification response must be an object."
        )

    requirements = data.get("requirements")

    if not isinstance(requirements, list):
        raise ValueError(
            "Classification response must contain "
            "a 'requirements' list."
        )

    expected_ids = {item["id"] for item in source_items}

    returned_ids = [
        requirement.get("id")
        for requirement in requirements
    ]

    if len(requirements) != len(source_items):
        raise ValueError(
            "Every requirement sent for classification "
            "must be returned exactly once."
        )

    missing_ids = expected_ids - set(returned_ids)

    if missing_ids:
        raise ValueError(
            f"Missing classified requirements: {sorted(missing_ids)}"
        )

    unexpected_ids = set(returned_ids) - expected_ids

    if unexpected_ids:
        raise ValueError(
            f"Unexpected requirement ids: {sorted(unexpected_ids)}"
        )

    if len(returned_ids) != len(set(returned_ids)):
        raise ValueError("Duplicate requirement ids in classification.")

    valid_types = {"functional", "non_functional"}

    for requirement in requirements:

        requirement_id = requirement.get("id")
        requirement_type = requirement.get("type")

        if requirement_type not in valid_types:
            raise ValueError(
                f"Invalid type for {requirement_id}: {requirement_type}"
            )

    return True


def normalize_text_for_comparison(text: str) -> str:
    """
    Normalizes a requirement description for duplicate detection by:
    - Converting to lowercase
    - Normalizing common modal prefixes (e.g. 'the system shall/must/should/will')
    - Removing punctuation
    - Collapsing multiple whitespace characters
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    text = text.lower().strip()
    # Normalize common modal prefixes
    text = re.sub(r"^the\s+system\s+(shall|must|should|will)\s+", "", text)
    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _merge_evidence_into_list(target_list: list, norm_key: str, duplicate_item: dict) -> bool:
    """
    Finds a matching requirement in target_list by normalized description
    and merges source_evidence from duplicate_item into it without duplicate statements.
    Returns True if a match was found and merged, False otherwise.
    """
    for existing in target_list:
        if not isinstance(existing, dict):
            continue
        if normalize_text_for_comparison(existing.get("description", "")) == norm_key:
            existing_evidence = existing.setdefault("source_evidence", [])
            new_evidence = duplicate_item.get("source_evidence", [])
            if isinstance(new_evidence, list) and isinstance(existing_evidence, list):
                existing_stmts = {
                    (e.get("speaker"), e.get("statement"))
                    for e in existing_evidence if isinstance(e, dict)
                }
                for ev in new_evidence:
                    if isinstance(ev, dict):
                        ev_key = (ev.get("speaker"), ev.get("statement"))
                        if ev_key not in existing_stmts:
                            existing_evidence.append(ev)
                            existing_stmts.add(ev_key)
            return True
    return False


def deduplicate_requirements(
    requirements: list[dict] | dict[str, list[dict]]
) -> list[dict] | dict[str, list[dict]]:
    """
    Deduplicates software requirements based on normalized description content.
    Preserves the first occurrence of each unique requirement and merges
    source_evidence from duplicate entries to retain complete traceability.

    Accepts:
    - A list of requirement dicts -> returns a deduplicated list of requirement dicts.
    - A dict with 'functional' and 'non_functional' lists -> returns a dict with deduplicated lists.
    """
    if isinstance(requirements, dict):
        functional = requirements.get("functional", [])
        non_functional = requirements.get("non_functional", [])

        seen_texts = set()
        deduped_functional = []
        deduped_non_functional = []

        if isinstance(functional, list):
            for item in functional:
                if not isinstance(item, dict):
                    continue
                norm_key = normalize_text_for_comparison(item.get("description", ""))
                if not norm_key:
                    norm_key = item.get("description", "").strip().lower()
                if not norm_key:
                    continue

                if norm_key in seen_texts:
                    _merge_evidence_into_list(deduped_functional, norm_key, item)
                    continue

                seen_texts.add(norm_key)
                deduped_functional.append({**item})

        if isinstance(non_functional, list):
            for item in non_functional:
                if not isinstance(item, dict):
                    continue
                norm_key = normalize_text_for_comparison(item.get("description", ""))
                if not norm_key:
                    norm_key = item.get("description", "").strip().lower()
                if not norm_key:
                    continue

                if norm_key in seen_texts:
                    if not _merge_evidence_into_list(deduped_non_functional, norm_key, item):
                        _merge_evidence_into_list(deduped_functional, norm_key, item)
                    continue

                seen_texts.add(norm_key)
                deduped_non_functional.append({**item})

        return {
            "functional": deduped_functional,
            "non_functional": deduped_non_functional
        }

    elif isinstance(requirements, list):
        seen_texts = set()
        unique_requirements = []

        for item in requirements:
            if not isinstance(item, dict):
                continue
            norm_key = normalize_text_for_comparison(item.get("description", ""))
            if not norm_key:
                norm_key = item.get("description", "").strip().lower()
            if not norm_key:
                continue

            if norm_key in seen_texts:
                _merge_evidence_into_list(unique_requirements, norm_key, item)
                continue

            seen_texts.add(norm_key)
            unique_requirements.append({**item})

        return unique_requirements

    return requirements


def renumber_ids(functional: list, non_functional: list) -> tuple[list, list]:
    """
    Reassign ids so that every item's id prefix matches its
    final bucket (FR-N for functional, NFR-N for non_functional),
    numbered sequentially starting at 1.

    Original relative order within each bucket is preserved,
    because the caller passes items in their original extraction
    order (see reclassify_requirements below).
    """

    renumbered_functional = []

    for index, item in enumerate(functional, start=1):

        renumbered_functional.append({
            **item,
            "id": f"FR-{index}"
        })

    renumbered_non_functional = []

    for index, item in enumerate(non_functional, start=1):

        renumbered_non_functional.append({
            **item,
            "id": f"NFR-{index}"
        })

    return renumbered_functional, renumbered_non_functional


def reclassify_requirements(specified_requirements: dict) -> dict:
    """
    Takes the {"functional": [...], "non_functional": [...]} block
    produced by the initial extraction, deduplicates requirements to
    prevent duplicate requirements from being generated, and re-verifies
    the classification with a dedicated LLM pass.

    Returns the same shape, corrected and deduplicated, with ids renumbered
    to match each item's final bucket.
    """

    functional = specified_requirements.get("functional", [])
    non_functional = specified_requirements.get("non_functional", [])

    all_items = functional + non_functional

    if not all_items:
        return {
            "functional": [],
            "non_functional": []
        }

    # Deduplicate requirements to eliminate duplicate requirements before classification
    initial_count = len(all_items)
    all_items = deduplicate_requirements(all_items)

    if len(all_items) < initial_count:
        print(
            f"\n[DEDUPLICATION] Removed {initial_count - len(all_items)} duplicate requirement(s). "
            f"Unique requirements remaining: {len(all_items)}"
        )

    # Ensure temporary unique IDs for the classification LLM step if any ID collisions existed
    seen_ids = set()
    for idx, item in enumerate(all_items, start=1):
        item_id = item.get("id")
        if not item_id or item_id in seen_ids:
            item["id"] = f"REQ-TEMP-{idx}"
        seen_ids.add(item["id"])

    print(
        "\n========== RECLASSIFYING SPECIFIED REQUIREMENTS =========="
    )

    print(f"Total requirements to verify: {len(all_items)}")

    # Only send id + description — never the full object with
    # source_evidence, to keep the prompt small and the LLM's
    # job narrow.
    items_for_llm = [
        {
            "id": item["id"],
            "description": item["description"]
        }
        for item in all_items
    ]

    prompt = f"""
{CLASSIFICATION_PROMPT}

REQUIREMENTS TO CLASSIFY:

{json.dumps(items_for_llm, indent=2, ensure_ascii=False)}
"""

    response = llm.invoke(prompt)

    content = response.content.strip()

    print("\n========== RAW RECLASSIFICATION RESPONSE ==========")
    print(content)
    print("=====================================================")

    try:
        data = parse_json_response(content)

    except json.JSONDecodeError as e:
        raise ValueError(
            "LLM returned invalid JSON for requirement reclassification."
        ) from e

    validate_classification(data, all_items)

    # Build id -> type lookup from the LLM's verdict.
    # NOTE: dict insertion order here follows the LLM's response
    # order, NOT necessarily the original extraction order — do not
    # iterate over this dict directly when rebuilding the buckets.
    type_by_id = {
        requirement["id"]: requirement["type"]
        for requirement in data["requirements"]
    }

    # Rebuild functional / non_functional by iterating over
    # all_items (the ORIGINAL extraction order), looking up each
    # item's corrected type. This guarantees the final bucket order
    # matches the original extraction order regardless of what
    # order the LLM happened to return its classifications in.
    new_functional = []
    new_non_functional = []

    for item in all_items:

        requirement_type = type_by_id[item["id"]]

        if requirement_type == "functional":
            new_functional.append(item)
        else:
            new_non_functional.append(item)

    # Reassign ids so they match each item's final bucket
    # (e.g. an item that moved from FR-18 to non_functional
    # must not keep the "FR-18" id).
    new_functional, new_non_functional = renumber_ids(
        new_functional,
        new_non_functional
    )

    print(
        f"\nBEFORE -> functional: {len(functional)}, "
        f"non_functional: {len(non_functional)}"
    )

    print(
        f"AFTER  -> functional: {len(new_functional)}, "
        f"non_functional: {len(new_non_functional)}"
    )

    print("=====================================================")

    return {
        "functional": new_functional,
        "non_functional": new_non_functional
    }