"""
HLA Agent — Evaluation Engine (v2: Style-Aware 6-Metric Framework)

Pipeline:
    1. Classify architectural style
    2. Compute 4 universal metrics (RTS, QAC, CI, CoS)
    3. Compute 2 style-specific metrics (SSM₁, SSM₂)
    4. Compute CAS (Composite Architecture Score) with AHP-derived weights

All 6 individual metric scores + CAS are stored separately for analysis.
"""

from evaluation.rts import compute_rts
from evaluation.qac import compute_qac
from evaluation.ci import compute_ci
from evaluation.cos import compute_cos
from evaluation.style_metrics import compute_style_metrics
from evaluation.style_classifier import classify_style, normalize_style_name
from evaluation.cas import compute_cas, rank_candidates
from evaluation.ahp import compute_ahp_weights
from evaluation.semantic_engine import get_engine


def evaluate_architecture(architecture: dict, requirements: dict) -> dict:
    """Run the full 6-metric evaluation on a single architecture candidate.

    Args:
        architecture: Parsed & normalized architecture dict
        requirements: Original requirements dict (FR/NFR)

    Returns:
        Dict with all individual scores, CAS, and details:
        {
            "RTS": float, "QAC": float, "CI": float,
            "CoS": float, "SSM1": float, "SSM2": float,
            "CAS": float, "verdict": str,
            "detected_style": str, "style_confidences": dict,
            "ssm1_name": str, "ssm2_name": str,
            "details": { per-metric details }
        }
    """
    # Step 1: Classify architectural style
    detected_style, style_confidences = classify_style(architecture)

    # Step 2: Universal metrics
    rts_result = compute_rts(architecture, requirements)
    qac_result = compute_qac(architecture, requirements)
    ci_result = compute_ci(architecture)
    cos_result = compute_cos(architecture)

    # Step 3: Style-specific metrics
    ssm_result = compute_style_metrics(architecture, requirements, detected_style)

    # Step 4: Assemble scores for CAS
    scores = {
        "RTS": rts_result["score"],
        "QAC": qac_result["score"],
        "CI": ci_result["score"],
        "CoS": cos_result["score"],
        "SSM1": ssm_result["ssm1"]["score"],
        "SSM2": ssm_result["ssm2"]["score"],
    }

    cas_result = compute_cas(scores)

    return {
        # Individual scores (always stored separately)
        **scores,
        # Composite
        "CAS": cas_result["cas"],
        "verdict": cas_result["verdict"],
        # Style info
        "detected_style": detected_style,
        "style_confidences": style_confidences,
        "ssm1_name": ssm_result["ssm1_name"],
        "ssm1_display": ssm_result["ssm1_display"],
        "ssm2_name": ssm_result["ssm2_name"],
        "ssm2_display": ssm_result["ssm2_display"],
        # Detailed breakdowns (for explainability)
        "details": {
            "rts": rts_result,
            "qac": qac_result,
            "ci": ci_result,
            "cos": cos_result,
            "ssm": ssm_result,
            "cas": cas_result,
        },
    }


__all__ = [
    "evaluate_architecture",
    "compute_rts",
    "compute_qac",
    "compute_ci",
    "compute_cos",
    "compute_style_metrics",
    "classify_style",
    "normalize_style_name",
    "compute_cas",
    "rank_candidates",
    "compute_ahp_weights",
    "get_engine",
]
