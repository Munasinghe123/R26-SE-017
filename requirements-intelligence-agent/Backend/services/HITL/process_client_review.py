def process_client_review(client_view, client_review):

    changes = {
        "kept": [],
        "edited": [],
        "deleted": [],
        "added": []
    }

    # ---------------------------------------------------------
    # Flatten client view
    # Existing requirements are indexed by their original ID.
    # Example: FR-8 -> client-view item
    # ---------------------------------------------------------

    original_items = {}

    for section in client_view.get("sections", []):
        for item in section.get("items", []):
            original_items[item["id"]] = item

    # ---------------------------------------------------------
    # Process client review
    # ---------------------------------------------------------

    for review in client_review:

        review_id = review["id"]
        action = review["action"]

        original_item = original_items.get(review_id)

        # -----------------------------------------------------
        # Existing requirement
        # -----------------------------------------------------

        if original_item:

            if action == "keep":

                changes["kept"].append({
                    "id": review_id
                })

            elif action == "edit":

                changes["edited"].append({
                    "id": review_id,
                    "original_text": original_item["text"],
                    "new_text": review.get("text")
                })

            elif action == "delete":

                changes["deleted"].append({
                    "id": review_id,
                    "original_text": original_item["text"]
                })

        # -----------------------------------------------------
        # New client requirement
        # -----------------------------------------------------

        else:

            if action == "add" and review.get("text"):

                changes["added"].append({
                    "id": review_id,
                    "text": review["text"]
                })

    return changes