def partition_client_changes(
    change_set,
    change_analysis,
    requirement_analysis=None,
    requirements=None
):
    """
    Separate client changes into:

    accepted_changes:
        Changes with no issues.

    clarification_changes:
        Changes with one or more issues, or unresolved contradictions.

    The original change data is preserved.
    """

    accepted_changes = {
        "kept": change_set.get("kept", []),
        "edited": [],
        "deleted": [],
        "added": []
    }

    clarification_changes = {
        "edited": [],
        "deleted": [],
        "added": [],
        "contradictions": []
    }

    # ---------------------------------------------------------
    # Build analysis lookup
    # ---------------------------------------------------------

    analysis_lookup = {}

    for analysis in change_analysis.get(
        "changes",
        []
    ):

        change_type = analysis["change_type"]

        if change_type == "added":

            key = (
                "id",
                analysis["id"],
                change_type
            )

        else:

            key = (
                "id",
                analysis["id"],
                change_type
            )

        analysis_lookup[key] = analysis

    # ---------------------------------------------------------
    # Process EDITED
    # ---------------------------------------------------------

    for change in change_set.get(
        "edited",
        []
    ):

        key = (
            "id",
            change["id"],
            "edited"
        )

        analysis = analysis_lookup.get(key)

        if analysis is None:
            raise ValueError(
                f"No analysis found for edited "
                f"requirement {change['id']}."
            )

        issues = analysis.get(
            "issues",
            []
        )

        if issues:

            clarification_changes["edited"].append({
                **change,
                "issues": issues
            })

        else:

            accepted_changes["edited"].append(
                change
            )

    # ---------------------------------------------------------
    # Process DELETED
    # ---------------------------------------------------------

    for change in change_set.get(
        "deleted",
        []
    ):

        key = (
            "id",
            change["id"],
            "deleted"
        )

        analysis = analysis_lookup.get(key)

        if analysis is None:
            raise ValueError(
                f"No analysis found for deleted "
                f"requirement {change['id']}."
            )

        issues = analysis.get(
            "issues",
            []
        )

        if issues:

            clarification_changes["deleted"].append({
                **change,
                "issues": issues
            })

        else:

            accepted_changes["deleted"].append(
                change
            )

    # ---------------------------------------------------------
    # Process ADDED
    # ---------------------------------------------------------

    for change in change_set.get(
        "added",
        []
    ):

        key = (
            "id",
            change["id"],
            "added"
        )

        analysis = analysis_lookup.get(key)

        if analysis is None:
            raise ValueError(
                f"No analysis found for new "
                f"requirement {change['id']}."
            )

        issues = analysis.get(
            "issues",
            []
        )

        if issues:

            clarification_changes["added"].append({
                **change,
                "issues": issues
            })

        else:

            accepted_changes["added"].append(
                change
            )

    # ---------------------------------------------------------
    # Check for UNRESOLVED CONTRADICTIONS among KEPT requirements
    # ---------------------------------------------------------
    if requirement_analysis:
        flagged = requirement_analysis.get("flagged_requirements", [])
        kept_ids = {str(item["id"]) for item in change_set.get("kept", [])}
        deleted_ids = {str(item["id"]) for item in change_set.get("deleted", [])}

        req_text_map = {}
        if requirements:
            spec = requirements.get("specified_requirements", {})
            for r in spec.get("functional", []) + spec.get("non_functional", []):
                req_text_map[str(r["id"])] = r.get("description") or r.get("text", "")

        processed_pairs = set()
        for item in flagged:
            if item.get("issue_type") == "contradictory":
                r1_id = str(item.get("id"))
                for r2_id_raw in item.get("conflicts_with", []):
                    r2_id = str(r2_id_raw)
                    pair_key = tuple(sorted([r1_id, r2_id]))
                    if pair_key in processed_pairs:
                        continue
                    # If BOTH are kept and neither was deleted, it is an unresolved contradiction
                    if r1_id in kept_ids and r2_id in kept_ids and r1_id not in deleted_ids and r2_id not in deleted_ids:
                        processed_pairs.add(pair_key)
                        clarification_changes["contradictions"].append({
                            "id": r1_id,
                            "conflicts_with": r2_id,
                            "r1_text": req_text_map.get(r1_id, f"Requirement {r1_id}"),
                            "r2_text": req_text_map.get(r2_id, f"Requirement {r2_id}"),
                            "reason": item.get("reason", "Direct conflict between business rules")
                        })
                        print(f"[partition_client_changes] Flagged unresolved contradiction between '{r1_id}' and '{r2_id}'")

    return {
        "accepted_changes": accepted_changes,
        "clarification_changes": clarification_changes
    }