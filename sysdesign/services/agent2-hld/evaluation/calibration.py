"""
Evaluation — Threshold Calibration

Calibrates the semantic similarity thresholds for RTS (θ_rts) and QAC (θ_qa)
by sweeping candidate thresholds against a manually-labelled ground truth
and selecting the threshold that maximises F1-score.

Usage:
    from evaluation.calibration import calibrate_rts_threshold, calibrate_qac_threshold

    # Ground truth: {fr_id: [component_names_that_should_match]}
    gt = {"FR-1": ["OrderService", "PaymentService"], "FR-2": ["MenuService"]}
    result = calibrate_rts_threshold(gt, architecture, requirements)
    # result = {"best_threshold": 0.55, "best_f1": 0.87, "sweep": [...]}
"""

import logging
from typing import Optional

from evaluation.semantic_engine import get_engine

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLDS = [
    0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80,
]


def _precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Compute precision, recall, and F1-score."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def calibrate_rts_threshold(
    ground_truth: dict[str, list[str]],
    architecture: dict,
    requirements: dict,
    thresholds: list[float] = None,
) -> dict:
    """Calibrate RTS threshold using ground truth FR→component mappings.

    Args:
        ground_truth: {fr_id: [component_names_that_should_trace]}
        architecture: Parsed architecture dict
        requirements: Requirements dict with functional_requirements
        thresholds: List of thresholds to test (default: 0.30 to 0.80)

    Returns:
        {
            "best_threshold": float,
            "best_f1": float,
            "sweep": [{"threshold": float, "precision": float, "recall": float, "f1": float}]
        }
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    engine = get_engine()
    frs = requirements.get("functional_requirements", [])
    components = architecture.get("components", [])

    # Build component text embeddings
    comp_data = []
    for comp in components:
        name = comp.get("name", "").strip()
        parts = [name]
        if isinstance(comp.get("responsibilities"), list):
            parts.extend(r for r in comp["responsibilities"] if r)
        if comp.get("responsibility"):
            parts.append(comp["responsibility"])
        comp_data.append((name, " ".join(parts)))

    sweep = []
    best_f1 = -1.0
    best_threshold = thresholds[0]

    for threshold in thresholds:
        tp = fp = fn = 0

        for fr in frs:
            fr_id = fr.get("id", "?")
            fr_desc = fr.get("description", "")
            gt_components = {c.lower() for c in ground_truth.get(fr_id, [])}

            if not fr_desc:
                continue

            # Find all components matching above threshold
            matched = set()
            for comp_name, comp_text in comp_data:
                sim = engine.cosine_sim(fr_desc, comp_text)
                if sim >= threshold:
                    matched.add(comp_name.lower())

            # Compare with ground truth
            if gt_components:
                for gc in gt_components:
                    if gc in matched:
                        tp += 1
                    else:
                        fn += 1
                for mc in matched:
                    if mc not in gt_components:
                        fp += 1
            else:
                # FR has no ground truth → any match is FP
                fp += len(matched)

        precision, recall, f1 = _precision_recall_f1(tp, fp, fn)
        sweep.append({
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp, "fp": fp, "fn": fn,
        })

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    logger.info(f"RTS calibration: best θ={best_threshold}, F1={best_f1:.4f}")

    return {
        "best_threshold": best_threshold,
        "best_f1": best_f1,
        "sweep": sweep,
    }


def calibrate_qac_threshold(
    ground_truth: dict[str, list[str]],
    architecture: dict,
    requirements: dict,
    thresholds: list[float] = None,
) -> dict:
    """Calibrate QAC threshold using ground truth NFR→component mappings.

    Args:
        ground_truth: {nfr_id: [component_names_providing_quality_attribute]}
        architecture: Parsed architecture dict
        requirements: Requirements dict with non_functional_requirements
        thresholds: List of thresholds to test

    Returns:
        Same structure as calibrate_rts_threshold
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    engine = get_engine()
    nfrs = requirements.get("non_functional_requirements", [])
    components = architecture.get("components", [])

    comp_data = []
    for comp in components:
        name = comp.get("name", "").strip()
        parts = [name]
        if isinstance(comp.get("responsibilities"), list):
            parts.extend(r for r in comp["responsibilities"] if r)
        if comp.get("responsibility"):
            parts.append(comp["responsibility"])
        comp_data.append((name, " ".join(parts)))

    sweep = []
    best_f1 = -1.0
    best_threshold = thresholds[0]

    for threshold in thresholds:
        tp = fp = fn = 0

        for nfr in nfrs:
            nfr_id = nfr.get("id", "?")
            nfr_desc = nfr.get("target", "") or nfr.get("description", "")
            gt_components = {c.lower() for c in ground_truth.get(nfr_id, [])}

            if not nfr_desc:
                continue

            matched = set()
            for comp_name, comp_text in comp_data:
                sim = engine.cosine_sim(nfr_desc, comp_text)
                if sim >= threshold:
                    matched.add(comp_name.lower())

            if gt_components:
                for gc in gt_components:
                    if gc in matched:
                        tp += 1
                    else:
                        fn += 1
                for mc in matched:
                    if mc not in gt_components:
                        fp += 1
            else:
                fp += len(matched)

        precision, recall, f1 = _precision_recall_f1(tp, fp, fn)
        sweep.append({
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp, "fp": fp, "fn": fn,
        })

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    logger.info(f"QAC calibration: best θ={best_threshold}, F1={best_f1:.4f}")

    return {
        "best_threshold": best_threshold,
        "best_f1": best_f1,
        "sweep": sweep,
    }
