import json
from typing import Dict, List


def get_requirement_type(requirement_id: str):

    if requirement_id.startswith("FR-"):
        return "functional"

    if requirement_id.startswith("NFR-"):
        return "non_functional"

    return None


def extract_original_requirements(
    requirements: Dict
) -> List[Dict]:

    original_items = []

    specified_requirements = requirements.get(
        "specified_requirements",
        {}
    )

    # =========================================================
    # Functional requirements
    # =========================================================

    for item in specified_requirements.get(
        "functional",
        []
    ):

        original_items.append({
            "id": item["id"],
            "text": item["description"],
            "type": "functional"
        })

    # =========================================================
    # Non-functional requirements
    # =========================================================

    for item in specified_requirements.get(
        "non_functional",
        []
    ):

        original_items.append({
            "id": item["id"],
            "text": item["description"],
            "type": "non_functional"
        })

    return original_items


def reconcile_requirements(
    original_requirements: Dict,
    accepted_changes: Dict,
    answer_requirements: Dict,
    normalized_new_requirements: List[Dict]
) -> Dict:

    print(
        "\n========== RECONCILING REQUIREMENTS =========="
    )

    # =========================================================
    # 1. Load original requirements
    # =========================================================

    original_items = extract_original_requirements(
        original_requirements
    )

    print(
        f"\nORIGINAL REQUIREMENTS COUNT: "
        f"{len(original_items)}"
    )

    print(
        "ORIGINAL REQUIREMENT IDS:"
    )

    print(
        [
            requirement["id"]
            for requirement in original_items
        ]
    )

    requirements_by_id = {
        item["id"]: item
        for item in original_items
    }

    print(
        f"\nINITIAL REQUIREMENTS BY ID COUNT: "
        f"{len(requirements_by_id)}"
    )

    # =========================================================
    # 2. Apply client review changes
    # =========================================================

       # =========================================================
    # 2. Apply client review changes
    # =========================================================

    kept_changes = accepted_changes.get(
        "kept",
        []
    )

    edited_changes = accepted_changes.get(
        "edited",
        []
    )

    deleted_changes = accepted_changes.get(
        "deleted",
        []
    )

    added_changes = accepted_changes.get(
        "added",
        []
    )

    print(
        f"\nCLIENT REVIEW KEPT COUNT: "
        f"{len(kept_changes)}"
    )

    print(
        f"CLIENT REVIEW EDITED COUNT: "
        f"{len(edited_changes)}"
    )

    print(
        f"CLIENT REVIEW DELETED COUNT: "
        f"{len(deleted_changes)}"
    )

    print(
        f"CLIENT REVIEW ADDED COUNT: "
        f"{len(added_changes)}"
    )

    # ---------------------------------------------------------
    # KEEP
    # ---------------------------------------------------------

    # Kept requirements already exist in requirements_by_id.
    # Nothing needs to be changed.

    # ---------------------------------------------------------
    # EDIT
    # ---------------------------------------------------------

    for change in edited_changes:

        requirement_id = change["id"]

        if requirement_id not in requirements_by_id:

            raise ValueError(
                f"Cannot edit unknown requirement: "
                f"{requirement_id}"
            )

        requirements_by_id[
            requirement_id
        ]["text"] = change["new_text"]

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    for change in deleted_changes:

        requirement_id = change["id"]

        requirements_by_id.pop(
            requirement_id,
            None
        )

    # ---------------------------------------------------------
    # ADD
    # ---------------------------------------------------------

    for change in added_changes:

        requirement_id = change["id"]

        requirements_by_id[
            requirement_id
        ] = {
            "id": requirement_id,
            "text": change["text"],
            "type": None
        }


    print(
        f"\nAFTER CLIENT REVIEW COUNT: "
        f"{len(requirements_by_id)}"
    )

    print(
        "REQUIREMENT IDS AFTER CLIENT REVIEW:"
    )

    print(
        list(
            requirements_by_id.keys()
        )
    )

    # =========================================================
    # 3. Apply requirements generated from clarification
    # =========================================================

    # This is important:
    #
    # FR-12 may have been deleted during the first review,
    # but the client can later answer a clarification question
    # saying that FR-12 should remain.
    #
    # Therefore answer_requirements overrides the previous
    # deletion.
    #
    # =========================================================

    answer_items = answer_requirements.get(
        "requirements",
        []
    )

    print(
        f"\nCLARIFICATION GENERATED REQUIREMENTS COUNT: "
        f"{len(answer_items)}"
    )

    for requirement in answer_items:

        requirement_id = requirement["id"]

        existing = requirements_by_id.get(
            requirement_id
        )

        requirement_type = (
            existing.get("type")
            if existing
            else get_requirement_type(
                requirement_id
            )
        )

        requirements_by_id[
            requirement_id
        ] = {
            "id": requirement_id,
            "text": requirement["text"],
            "type": requirement_type
        }

    print(
        f"\nAFTER CLARIFICATION ANSWERS COUNT: "
        f"{len(requirements_by_id)}"
    )

    print(
        "REQUIREMENT IDS AFTER CLARIFICATION:"
    )

    print(
        list(
            requirements_by_id.keys()
        )
    )

    # =========================================================
    # 4. Apply normalized NEW requirements
    # =========================================================

    # These have already gone through:
    #
    # collect
    #     ↓
    # classification
    #     ↓
    # format check
    #     ↓
    # normalization
    #
    # So reconciliation simply accepts them.
    #
    # =========================================================

    print(
        f"\nNORMALIZED NEW REQUIREMENTS COUNT: "
        f"{len(normalized_new_requirements)}"
    )

    for requirement in normalized_new_requirements:

        requirement_id = requirement["id"]

        requirements_by_id[
            requirement_id
        ] = {
            "id": requirement_id,
            "text": requirement["text"],
            "type": requirement["type"]
        }

    print(
        f"\nAFTER NEW REQUIREMENTS COUNT: "
        f"{len(requirements_by_id)}"
    )

    print(
        "REQUIREMENT IDS AFTER NEW REQUIREMENTS:"
    )

    print(
        list(
            requirements_by_id.keys()
        )
    )

    # =========================================================
    # 5. Recover classification for any existing FR/NFR
    # =========================================================

    for requirement_id, requirement in (
        requirements_by_id.items()
    ):

        if requirement.get("type") is None:

            requirement["type"] = (
                get_requirement_type(
                    requirement_id
                )
            )

    print(
        f"\nAFTER CLASSIFICATION RECOVERY COUNT: "
        f"{len(requirements_by_id)}"
    )

    # =========================================================
    # 6. Validate classification
    # =========================================================

    validate_final_requirements(
        list(
            requirements_by_id.values()
        )
    )

    print(
        "\nFINAL REQUIREMENT VALIDATION: SUCCESS"
    )

    # =========================================================
    # 7. Preserve original ordering
    # =========================================================

    final_items = []

    processed_ids = set()

    for original in original_items:

        requirement_id = original["id"]

        if requirement_id in requirements_by_id:

            final_items.append(
                requirements_by_id[
                    requirement_id
                ]
            )

            processed_ids.add(
                requirement_id
            )

    print(
        f"\nAFTER PRESERVING ORIGINAL ORDER COUNT: "
        f"{len(final_items)}"
    )

    # =========================================================
    # 8. Append genuinely new requirements
    # =========================================================

    appended_new_count = 0

    for requirement_id, requirement in (
        requirements_by_id.items()
    ):

        if requirement_id not in processed_ids:

            final_items.append(
                requirement
            )

            appended_new_count += 1

    print(
        f"\nGENUINELY NEW REQUIREMENTS APPENDED: "
        f"{appended_new_count}"
    )

    print(
        f"FINAL RECONCILIATION INPUT COUNT: "
        f"{len(final_items)}"
    )

    print(
        "FINAL REQUIREMENT IDS:"
    )

    print(
        [
            requirement["id"]
            for requirement in final_items
        ]
    )

    # =========================================================
    # 9. Separate FRs and NFRs
    # =========================================================

    functional_requirements = []
    non_functional_requirements = []

    for requirement in final_items:

        if requirement["type"] == "functional":

            functional_requirements.append(
                requirement
            )

        elif requirement["type"] == "non_functional":

            non_functional_requirements.append(
                requirement
            )

    print(
        f"\nFINAL FUNCTIONAL REQUIREMENTS COUNT: "
        f"{len(functional_requirements)}"
    )

    print(
        f"FINAL NON-FUNCTIONAL REQUIREMENTS COUNT: "
        f"{len(non_functional_requirements)}"
    )

    # =========================================================
    # 10. Build final result
    # =========================================================

    final_result = {
        "sections": [
            {
                "title": "Functional Requirements",
                "items": functional_requirements
            },
            {
                "title": "Non-Functional Requirements",
                "items": non_functional_requirements
            }
        ]
    }

    # =========================================================
    # 11. Debug output
    # =========================================================

    print(
        "\n========== FINAL FUNCTIONAL REQUIREMENTS =========="
    )

    print(
        json.dumps(
            functional_requirements,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\n========== FINAL NON-FUNCTIONAL REQUIREMENTS =========="
    )

    print(
        json.dumps(
            non_functional_requirements,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\n========== FINAL REQUIREMENTS =========="
    )

    print(
        json.dumps(
            final_result,
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "=========================================="
    )

    return final_result


def validate_final_requirements(
    requirements: List[Dict]
):

    seen_ids = set()

    for requirement in requirements:

        requirement_id = requirement.get(
            "id"
        )

        text = requirement.get(
            "text"
        )

        requirement_type = requirement.get(
            "type"
        )

        # -----------------------------------------------------
        # ID validation
        # -----------------------------------------------------

        if not isinstance(
            requirement_id,
            str
        ):

            raise ValueError(
                "Every final requirement must have "
                "a string ID."
            )

        if requirement_id in seen_ids:

            raise ValueError(
                f"Duplicate requirement ID: "
                f"{requirement_id}"
            )

        seen_ids.add(
            requirement_id
        )

        # -----------------------------------------------------
        # Text validation
        # -----------------------------------------------------

        if not isinstance(
            text,
            str
        ) or not text.strip():

            raise ValueError(
                f"Requirement {requirement_id} "
                f"has invalid text."
            )

        # -----------------------------------------------------
        # Type validation
        # -----------------------------------------------------

        if requirement_type not in {
            "functional",
            "non_functional"
        }:

            raise ValueError(
                f"Requirement {requirement_id} "
                f"does not have a valid classification."
            )

    return True