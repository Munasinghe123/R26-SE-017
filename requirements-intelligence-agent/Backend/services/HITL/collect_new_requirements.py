from typing import List, Dict


def collect_new_requirements(
    accepted_changes: Dict,
    answer_requirements: Dict
) -> list[Dict]:

    new_requirements = []

    # =========================================================
    # 1. Direct additions from client review
    # =========================================================

    accepted_items = accepted_changes.get(
        "items",
        []
    )

    for item in accepted_items:

        if (
            item.get("action") == "add"
            and item.get("id", "").startswith("new-")
        ):
            new_requirements.append({
                "id": item["id"],
                "text": item["text"]
            })

    # =========================================================
    # 2. Requirements generated from clarification answers
    # =========================================================

    answer_items = answer_requirements.get(
        "requirements",
        []
    )

    for item in answer_items:

        if item.get("id", "").startswith("new-"):

            new_requirements.append({
                "id": item["id"],
                "text": item["text"]
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

        unique_requirements.append(
            requirement
        )

    return unique_requirements