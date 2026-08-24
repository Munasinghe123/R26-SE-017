def process_client_review(client_view, client_review):

    changes = {
        "kept": [],
        "edited": [],
        "deleted": [],
        "added": []
    }

    submitted_ids = set()

    # Flatten client view items
    original_items = {}

    for section in client_view.get("sections", []):
        for item in section.get("items", []):
            original_items[item["id"]] = item

    for review in client_review:

        item_id = review["id"]
        action = review["action"]

        submitted_ids.add(item_id)

        original_item = original_items.get(item_id)

        # Existing client-view item
        if original_item:

            if action == "keep":
                changes["kept"].append({
                    "id": item_id
                })

            elif action == "edit":
                changes["edited"].append({
                    "id": item_id,
                    "original_text": original_item["text"],
                    "new_text": review.get("text"),
                    "source_ids": original_item.get("source_ids", [])
                })

            elif action == "delete":
                changes["deleted"].append({
                    "id": item_id,
                    "original_text": original_item["text"],
                    "source_ids": original_item.get("source_ids", [])
                })

        # Client-added item
        else:

            if action == "edit" and review.get("text"):
                changes["added"].append({
                    "id": item_id,
                    "text": review["text"]
                })

    return changes