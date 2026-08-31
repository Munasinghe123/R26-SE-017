"""
Quality Characteristic Definitions according to ISO/IEC/IEEE 29148
"""

QUALITY_CHARACTERISTICS = {
    "necessary": (
        "The requirement defines an essential capability, characteristic, constraint and/or quality factor. "
        "If it is not included in the set of requirements, a deficiency in capability or characteristic will exist, "
        "which cannot be fulfilled by implementing other requirements. The requirement is currently applicable "
        "and has not been made obsolete by the passage of time. Requirements with planned expiration dates or "
        "applicability dates are clearly identified."
    ),
    "appropriate": (
        "The specific intent and amount of detail of the requirement is appropriate to the level of the entity "
        "to which it refers (level of abstraction appropriate to the level of entity). This includes avoiding "
        "unnecessary constraints on the architecture or design while allowing implementation independence "
        "to the extent possible."
    ),
    "unambiguous": (
        "The requirement is stated in such a way that it can be interpreted in only one way. "
        "The requirement is stated simply and is easy to understand."
    ),
    "complete": (
        "The requirement sufficiently describes the necessary capability, characteristic, constraint or quality factor "
        "to meet the entity need without needing other information to understand the requirement."
    ),
    "singular": (
        "The requirement states a single capability, characteristic, constraint or quality factor."
    ),
    "feasible": (
        "The requirement can be realized within system constraints (e.g., cost, schedule, technical) with acceptable risk."
    ),
    "verifiable": (
        "The requirement is structured and worded such that its realization can be proven (verified) to the customer's "
        "satisfaction at the level the requirements exists. Verifiability is enhanced when the requirement is measurable."
    ),
    "correct": (
        "The requirement is an accurate representation of the entity need from which it was transformed."
    ),
    "conforming": (
        "The individual items conform to an approved standard template and style for writing requirements, when applicable."
    )
}
