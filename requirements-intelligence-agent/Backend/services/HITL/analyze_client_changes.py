def analyze_client_changes(requirements, change_set):

    analysis = {
        "affected_requirements": [],
        "unaffected_requirements": []
    }

    affected_ids = set()

    # Edited requirements
    for change in change_set.get("edited", []):

        for source_id in change.get("source_ids", []):

            affected_ids.add(source_id)

            analysis["affected_requirements"].append({
                "requirement_id": source_id,
                "change_type": "edited",
                "original_text": change.get("original_text"),
                "new_text": change.get("new_text"),
                "impact": "review_required"
            })

    # Deleted requirements
    for change in change_set.get("deleted", []):

        for source_id in change.get("source_ids", []):

            affected_ids.add(source_id)

            analysis["affected_requirements"].append({
                "requirement_id": source_id,
                "change_type": "deleted",
                "original_text": change.get("original_text"),
                "impact": "review_required"
            })

    # Determine unaffected requirements
    specified_requirements = requirements.get(
        "specified_requirements",
        {}
    )

    for requirement_type in [
        "functional",
        "non_functional"
    ]:

        for requirement in specified_requirements.get(
            requirement_type,
            []
        ):

            requirement_id = requirement.get("id")

            if requirement_id not in affected_ids:

                analysis["unaffected_requirements"].append(
                    requirement_id
                )

    return analysis