def partition_client_changes(
    change_set,
    change_analysis
):
    """
    Separate client changes into:

    accepted_changes:
        Changes with no issues.

    clarification_changes:
        Changes with one or more issues.

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
        "added": []
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

    return {
        "accepted_changes": accepted_changes,
        "clarification_changes": clarification_changes
    }