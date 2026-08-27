from typing import List, Dict


REQUIRED_PREFIX = "The system shall"


def find_requirements_to_rewrite(
    classified_requirements: list[Dict]
) ->list[Dict]:

    requirements_to_rewrite = []

    for requirement in classified_requirements:

        text = requirement["text"].strip()

        if not text.startswith(
            REQUIRED_PREFIX
        ):
            requirements_to_rewrite.append(
                requirement
            )

    return requirements_to_rewrite