def process_client_review(client_view, client_review):
    """
    Convert raw client review items into a structured change set.

    Parameters
    ----------
    client_view : dict
        The client_view stored in graph state (sections/items structure).
    client_review : list[dict]
        Items submitted by the client.
        Each: { "id": str, "action": "keep"|"edit"|"delete"|"add", "text": str|None }

    Returns
    -------
    dict  { kept: [...], edited: [...], deleted: [...], added: [...] }
    """

    changes = {
        "kept": [],
        "edited": [],
        "deleted": [],
        "added": []
    }

    if not client_review:
        return changes

    # ------------------------------------------------------------------
    # Flatten client_view into id -> item lookup.
    # Supports both sections[].items[] and flat items[] structures.
    # ------------------------------------------------------------------
    original_items = {}

    if client_view:
        for section in client_view.get("sections", []):
            for item in section.get("items", []):
                item_id = item.get("id") or item.get("requirement_id")
                if item_id:
                    original_items[item_id] = item

        for item in client_view.get("items", []):
            item_id = item.get("id") or item.get("requirement_id")
            if item_id:
                original_items[item_id] = item

    # ------------------------------------------------------------------
    # Map each client action to its change bucket
    # ------------------------------------------------------------------
    for review in client_review:
        review_id = review.get("id")
        action = review.get("action")

        if not review_id or not action:
            continue

        original_item = original_items.get(review_id)

        if original_item:
            # Existing requirement
            if action == "keep":
                changes["kept"].append({"id": review_id})

            elif action == "edit":
                changes["edited"].append({
                    "id": review_id,
                    "original_text": original_item.get("text", ""),
                    "new_text": review.get("text")
                })

            elif action == "delete":
                changes["deleted"].append({
                    "id": review_id,
                    "original_text": original_item.get("text", "")
                })

        else:
            # New client requirement (id like "new-1234567890")
            if action == "add" and review.get("text"):
                changes["added"].append({
                    "id": review_id,
                    "text": review["text"]
                })

    return changes
