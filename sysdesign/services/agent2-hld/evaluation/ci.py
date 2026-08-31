"""
Evaluation — CI: Coupling Index

Formula:
    CI = 1 - |E| / (|C| × (|C| - 1))

Where:
    |E| = number of directed edges (connectors) in the architecture graph
    |C| = number of components

Higher CI = lower coupling density = better decoupling = better quality.

Known Limitation:
    CI as formulated rewards sparse graphs and therefore structurally favours
    Layered and Pipe-and-Filter architectures over Microservices and Event-Driven
    architectures, which inherently have denser connector graphs. This style-bias
    is partially mitigated by the style-specific metrics (SSM1, SSM2). A
    style-normalized CI using empirically calibrated expected densities is
    identified as future work.
"""

import logging

logger = logging.getLogger(__name__)


def compute_ci(architecture: dict) -> dict:
    """Compute Coupling Index (graph decoupling score).

    Args:
        architecture: Parsed architecture dict with 'components' and
                      'connectors' (or 'interactions')

    Returns:
        {
            "score": float (0.0 - 1.0),
            "num_components": int,
            "num_edges": int,
            "max_possible_edges": int,
            "graph_density": float,
            "limitation_note": str
        }
    """
    components = architecture.get("components", [])
    connectors = (
        architecture.get("connectors", [])
        or architecture.get("interactions", [])
        or []
    )

    num_components = len(components)
    num_edges = len(connectors)

    if num_components <= 1:
        return {
            "score": 1.0,
            "num_components": num_components,
            "num_edges": num_edges,
            "max_possible_edges": 0,
            "graph_density": 0.0,
            "limitation_note": "Trivial architecture (≤1 component)",
        }

    # Maximum possible directed edges in a complete graph
    max_edges = num_components * (num_components - 1)

    # Graph density
    density = num_edges / max_edges if max_edges > 0 else 0.0

    # CI = 1 - density (higher = less coupled = better)
    ci_score = 1.0 - density
    ci_score = max(0.0, min(1.0, ci_score))

    logger.info(
        f"CI: {ci_score:.3f} | Components: {num_components}, "
        f"Edges: {num_edges}/{max_edges}, Density: {density:.3f}"
    )

    return {
        "score": round(ci_score, 4),
        "num_components": num_components,
        "num_edges": num_edges,
        "max_possible_edges": max_edges,
        "graph_density": round(density, 4),
        "limitation_note": (
            "CI favours sparse graphs. Style-specific metrics (SSM1, SSM2) "
            "provide style-appropriate structural evaluation."
        ),
    }
