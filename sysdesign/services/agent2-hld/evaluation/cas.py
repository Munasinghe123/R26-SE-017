"""
Evaluation — CAS: Composite Architecture Score + Ranker

CAS = w₁·RTS + w₂·QAC + w₃·CI + w₄·CoS + w₅·SSM₁ + w₆·SSM₂

Weights are derived via AHP (Saaty, 1980). Default weights are preliminary
researcher-derived values (CR = 0.013 < 0.10). Final weights require
expert survey validation.

Provides:
  - CAS computation from 6 individual metric scores
  - Verdict classification (Accepted / Marginal / Poor)
  - Candidate ranking across all models
"""

import logging
from evaluation.ahp import compute_ahp_weights

logger = logging.getLogger(__name__)

# ── Default AHP-derived weights (preliminary) ────────

_DEFAULT_WEIGHTS, _DEFAULT_CR = compute_ahp_weights()

# Verdict thresholds
CAS_ACCEPTED = 0.75
CAS_MARGINAL = 0.60


def compute_cas(
    scores: dict,
    weights: dict = None,
) -> dict:
    """Compute Composite Architecture Score from 6 individual metrics.

    Args:
        scores: Dict with keys: RTS, QAC, CI, CoS, SSM1, SSM2
        weights: Optional custom weight dict. Defaults to AHP-derived weights.

    Returns:
        {
            "cas": float,
            "verdict": "Accepted" | "Marginal" | "Poor",
            "weighted_breakdown": {metric: weighted_value},
            "weights_used": {metric: weight},
            "weights_source": "ahp_preliminary" | "custom",
        }
    """
    w = weights or _DEFAULT_WEIGHTS
    weights_source = "custom" if weights else "ahp_preliminary"

    weighted = {}
    cas = 0.0

    for metric, weight in w.items():
        value = scores.get(metric, 0.0)
        w_value = value * weight
        weighted[metric] = round(w_value, 4)
        cas += w_value

    cas = round(cas, 4)

    if cas >= CAS_ACCEPTED:
        verdict = "Accepted"
    elif cas >= CAS_MARGINAL:
        verdict = "Marginal"
    else:
        verdict = "Poor"

    logger.info(f"CAS: {cas:.4f} → {verdict}")

    return {
        "cas": cas,
        "verdict": verdict,
        "weighted_breakdown": weighted,
        "weights_used": w,
        "weights_source": weights_source,
    }


def rank_candidates(
    candidates: list[dict],
    cas_key: str = "CAS",
) -> list[dict]:
    """Rank architecture candidates by CAS score (descending).

    Args:
        candidates: List of dicts, each with 'scores' containing CAS
        cas_key: Key to sort by (default: "CAS")

    Returns:
        Same list sorted by CAS descending, with 'rank' field added (1-based)
    """
    sorted_candidates = sorted(
        candidates,
        key=lambda c: c.get("scores", {}).get(cas_key, 0),
        reverse=True,
    )

    for i, candidate in enumerate(sorted_candidates):
        candidate["rank"] = i + 1

    if sorted_candidates:
        winner = sorted_candidates[0]
        logger.info(
            f"Winner: {winner.get('model', '?')} candidate "
            f"{winner.get('candidate_num', '?')} with "
            f"{cas_key}={winner['scores'].get(cas_key, 0):.4f}"
        )

    return sorted_candidates
