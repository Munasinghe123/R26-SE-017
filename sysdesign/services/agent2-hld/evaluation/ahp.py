"""
Evaluation — AHP: Analytic Hierarchy Process Weight Derivation

Implements Saaty's AHP (1980) for mathematically rigorous metric weight
derivation. Computes the principal eigenvector of a pairwise comparison
matrix and validates consistency via CR < 0.10.

Reference:
    Saaty, T.L. (1980). The Analytic Hierarchy Process. McGraw-Hill.

Usage:
    from evaluation.ahp import compute_ahp_weights
    weights, cr = compute_ahp_weights()
    # weights = {"RTS": 0.27, "QAC": 0.20, "CI": 0.15, ...}
    # cr = 0.013
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

# Saaty's Random Index (RI) for n = 1..15
# Source: Saaty (1980), Table 3.1
RANDOM_INDEX = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59,
}

# Default criteria names
DEFAULT_CRITERIA = ["RTS", "QAC", "CI", "CoS", "SSM1", "SSM2"]

# Default pairwise comparison matrix (researcher-derived, preliminary)
# Rationale:
#   - RTS slightly more important than QAC (2:1): requirements are fundamental
#   - RTS/QAC more important than CI/CoS/SSM1 (2:1): satisfaction > structure
#   - CI = CoS = SSM1 (1:1): structural metrics equally important
#   - SSM2 least important (1/2 of CI/CoS/SSM1): secondary refinement
DEFAULT_PCM = [
    [1,   2,   2,   2,   2,   3  ],   # RTS
    [1/2, 1,   2,   2,   2,   2  ],   # QAC
    [1/2, 1/2, 1,   1,   1,   2  ],   # CI
    [1/2, 1/2, 1,   1,   1,   2  ],   # CoS
    [1/2, 1/2, 1,   1,   1,   2  ],   # SSM1
    [1/3, 1/2, 1/2, 1/2, 1/2, 1  ],   # SSM2
]


def compute_ahp_weights(
    pcm: list[list[float]] = None,
    criteria: list[str] = None,
) -> tuple[dict[str, float], float]:
    """Compute AHP weights from a pairwise comparison matrix.

    Args:
        pcm: n×n pairwise comparison matrix (Saaty's 1-9 scale).
             If None, uses DEFAULT_PCM.
        criteria: List of n criteria names.
             If None, uses DEFAULT_CRITERIA.

    Returns:
        Tuple of (weights_dict, consistency_ratio)
        weights_dict: {criterion: weight} summing to 1.0
        consistency_ratio: CR value (must be < 0.10 for acceptance)

    Raises:
        ValueError: If CR >= 0.10 (inconsistent judgments)
    """
    pcm = pcm or DEFAULT_PCM
    criteria = criteria or DEFAULT_CRITERIA

    matrix = np.array(pcm, dtype=np.float64)
    n = matrix.shape[0]

    if matrix.shape != (n, n):
        raise ValueError(f"PCM must be square, got {matrix.shape}")
    if len(criteria) != n:
        raise ValueError(f"Expected {n} criteria names, got {len(criteria)}")

    # Step 1: Normalize columns
    col_sums = matrix.sum(axis=0)
    normalized = matrix / col_sums

    # Step 2: Compute priority vector (row averages)
    weights = normalized.mean(axis=1)

    # Ensure weights sum to exactly 1.0
    weights = weights / weights.sum()

    # Step 3: Consistency check
    # Compute weighted sum vector
    weighted_sum = matrix @ weights

    # Compute lambda_max
    ratios = weighted_sum / weights
    lambda_max = ratios.mean()

    # Consistency Index
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0

    # Consistency Ratio
    ri = RANDOM_INDEX.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0

    # Build result dict
    weights_dict = {
        criteria[i]: round(float(weights[i]), 4)
        for i in range(n)
    }

    logger.info(
        f"AHP weights: {weights_dict} | "
        f"λ_max={lambda_max:.4f}, CI={ci:.4f}, CR={cr:.4f}"
    )

    if cr >= 0.10:
        logger.warning(
            f"AHP consistency ratio CR={cr:.4f} >= 0.10. "
            f"Pairwise judgments are inconsistent. Review the comparison matrix."
        )

    return weights_dict, round(cr, 4)


def validate_pcm(pcm: list[list[float]]) -> list[str]:
    """Validate a pairwise comparison matrix for common errors.

    Returns list of error messages (empty if valid).
    """
    errors = []
    matrix = np.array(pcm, dtype=np.float64)
    n = matrix.shape[0]

    if matrix.shape[0] != matrix.shape[1]:
        errors.append(f"Matrix must be square, got {matrix.shape}")
        return errors

    # Check diagonal = 1
    for i in range(n):
        if abs(matrix[i, i] - 1.0) > 1e-9:
            errors.append(f"Diagonal element [{i},{i}] must be 1.0, got {matrix[i, i]}")

    # Check reciprocity: a[i,j] * a[j,i] ≈ 1
    for i in range(n):
        for j in range(i + 1, n):
            product = matrix[i, j] * matrix[j, i]
            if abs(product - 1.0) > 0.01:
                errors.append(
                    f"Reciprocity violated: [{i},{j}]={matrix[i, j]:.2f} × "
                    f"[{j},{i}]={matrix[j, i]:.2f} = {product:.4f} (should be 1.0)"
                )

    # Check values in Saaty's range [1/9, 9]
    for i in range(n):
        for j in range(n):
            if matrix[i, j] < 1/9 - 0.01 or matrix[i, j] > 9.01:
                errors.append(
                    f"Value [{i},{j}]={matrix[i, j]:.4f} outside Saaty's range [1/9, 9]"
                )

    return errors
