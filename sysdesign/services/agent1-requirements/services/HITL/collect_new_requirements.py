from typing import List, Dict, Any, Optional


def collect_new_requirements(
    accepted_changes: Optional[Dict] = None,
    answer_requirements: Optional[Any] = None
) -> list[Dict]:

    new_requirements = []
    accepted_changes = accepted_changes or {}

    # =========================================================
    # 1. Direct additions from client review
    # =========================================================

    # Check accepted_changes["added"] (from partition_client_changes)
    for item in accepted_changes.get("added", []):
        item_id = item.get("id", "")
        if item_id.startswith("new-") or item_id:
            new_requirements.append({
                "id": item_id,
                "text": item.get("text", "")
            })

    # Also check accepted_changes["items"] if present
    for item in accepted_changes.get("items", []):
        if (
            item.get("action") == "add"
            and item.get("id", "").startswith("new-")
        ):
            new_requirements.append({
                "id": item["id"],
                "text": item.get("text", "")
            })

    # =========================================================
    # 2. Requirements generated from clarification answers
    # =========================================================

    if isinstance(answer_requirements, dict):
        answer_items = answer_requirements.get("requirements", [])
    elif isinstance(answer_requirements, list):
        answer_items = answer_requirements
    else:
        answer_items = []

    for item in answer_items:
        if isinstance(item, dict) and item.get("id", "").startswith("new-"):
            new_requirements.append({
                "id": item["id"],
                "text": item.get("text", "")
            })

    # =========================================================
    # 3. Prevent duplicate new IDs
    # =========================================================

    seen_ids = set()
    unique_requirements = []

    for requirement in new_requirements:
        requirement_id = requirement["id"]
        if requirement_id in seen_ids:
            continue
        seen_ids.add(requirement_id)
        unique_requirements.append(requirement)

    return unique_requirements