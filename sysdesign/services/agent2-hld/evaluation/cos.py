"""
Evaluation — CoS: Cohesion Score

Formula:
    CoS = mean_j(cohesion(C_j))
    cohesion(C_j) = mean pairwise cosine_sim of C_j's responsibilities

Measures the semantic coherence of each component's responsibilities.
A component with tightly related responsibilities (e.g., all about "order
processing") has high cohesion. A component with scattered responsibilities
(e.g., "handles payments AND sends emails AND manages users") has low cohesion.

Uses the same frozen all-MiniLM-L6-v2 embeddings as RTS for consistency.
"""

import logging
from evaluation.semantic_engine import get_engine

logger = logging.getLogger(__name__)


def _get_responsibilities(component: dict) -> list[str]:
    """Extract responsibility texts from a component.

    Handles both plural 'responsibilities' (list) and singular 'responsibility' (str).
    """
    resps = []

    if isinstance(component.get("responsibilities"), list):
        resps.extend(r.strip() for r in component["responsibilities"] if r.strip())

    if component.get("responsibility") and isinstance(component["responsibility"], str):
        resp = component["responsibility"].strip()
        if resp and resp not in resps:
            resps.append(resp)

    return resps


def compute_cos(architecture: dict) -> dict:
    """Compute Cohesion Score.

    Args:
        architecture: Parsed architecture dict with 'components'

    Returns:
        {
            "score": float (0.0 - 1.0),
            "num_components": int,
            "component_cohesion": [
                {"name": str, "cohesion": float, "num_responsibilities": int}
            ]
        }
    """
    components = architecture.get("components", [])

    if not components:
        return {
            "score": 0.0,
            "num_components": 0,
            "component_cohesion": [],
        }

    engine = get_engine()
    component_cohesion = []
    total_cohesion = 0.0
    valid_count = 0

    for comp in components:
        name = comp.get("name", "Unknown").strip()
        resps = _get_responsibilities(comp)

        if not resps:
            # No responsibilities → cannot measure cohesion
            component_cohesion.append({
                "name": name,
                "cohesion": 0.0,
                "num_responsibilities": 0,
            })
            continue

        # Single responsibility → trivially cohesive
        if len(resps) == 1:
            cohesion = 1.0
        else:
            cohesion = engine.pairwise_cohesion(resps)

        component_cohesion.append({
            "name": name,
            "cohesion": round(cohesion, 4),
            "num_responsibilities": len(resps),
        })

        total_cohesion += cohesion
        valid_count += 1

    score = total_cohesion / valid_count if valid_count > 0 else 0.0

    logger.info(
        f"CoS: {score:.3f} | Components: {valid_count} with responsibilities"
    )

    return {
        "score": round(score, 4),
        "num_components": len(components),
        "component_cohesion": component_cohesion,
    }
