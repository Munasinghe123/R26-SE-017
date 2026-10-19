"""
Evaluation — RTS: Requirement Traceability Score

Formula:
    RTS = |{FR_i : max_j(cosine_sim(embed(FR_i), embed(C_j))) >= θ_rts}| / |FR|

Each functional requirement is embedded alongside each component's name and
responsibilities. A requirement is considered "traced" if its embedding has
cosine similarity >= θ_rts with at least one component.

The threshold θ_rts should be calibrated using evaluation/calibration.py.
Default: 0.55 (preliminary, to be justified via F1-score calibration).
"""

import logging
from evaluation.semantic_engine import get_engine

logger = logging.getLogger(__name__)

# Default threshold — calibrate via calibration.py (0.48 calibrated for concise requirements)
DEFAULT_RTS_THRESHOLD = 0.48


def _build_component_texts(architecture: dict) -> list[tuple[str, str, list[str]]]:
    """Build (name, full_text, req_ids) tuples for each component.

    Handles responsibilities, provided interfaces, and explicit requirement IDs.
    """
    result = []
    for comp in architecture.get("components", []):
        name = comp.get("name", "").strip()
        if not name:
            continue

        parts = [name]

        # Handle plural responsibilities (preferred)
        if isinstance(comp.get("responsibilities"), list):
            parts.extend(r.strip() for r in comp["responsibilities"] if r.strip())

        # Handle singular responsibility (fallback)
        if comp.get("responsibility") and isinstance(comp.get("responsibility"), str):
            parts.append(comp["responsibility"].strip())

        # Include provided interfaces if present
        if isinstance(comp.get("provided_interfaces"), list):
            parts.extend(str(i).strip() for i in comp["provided_interfaces"] if str(i).strip())

        req_ids = comp.get("requirement_ids") or []
        full_text = " ".join(parts)
        result.append((name, full_text, req_ids))

    return result


def compute_rts(architecture: dict, requirements: dict,
                threshold: float = DEFAULT_RTS_THRESHOLD) -> dict:
    """Compute Requirement Traceability Score.

    Args:
        architecture: Parsed architecture dict with 'components'
        requirements: Requirements dict with 'functional_requirements'
        threshold: Cosine similarity threshold for traceability match

    Returns:
        {
            "score": float (0.0 - 1.0),
            "traced": int,
            "total": int,
            "threshold": float,
            "traceability_map": {fr_id: {"best_component": str, "best_sim": float, "traced": bool}},
            "untraced": [fr_ids]
        }
    """
    frs = requirements.get("functional_requirements", [])
    components = _build_component_texts(architecture)

    if not frs:
        return {
            "score": 1.0, "traced": 0, "total": 0,
            "threshold": threshold,
            "traceability_map": {}, "untraced": [],
        }

    if not components:
        return {
            "score": 0.0, "traced": 0, "total": len(frs),
            "threshold": threshold,
            "traceability_map": {}, "untraced": [fr.get("id", "?") for fr in frs],
        }

    engine = get_engine()
    component_texts = [text for _, text, _ in components]

    # Pre-embed all component texts
    engine.embed_batch(component_texts)

    traceability_map = {}
    untraced = []
    traced_count = 0

    for fr in frs:
        fr_id = fr.get("id", "?")
        fr_title = fr.get("title", "").strip()
        fr_desc = fr.get("description", "").strip()
        fr_full = f"{fr_title}: {fr_desc}".strip() if fr_title else fr_desc
        human_desc = fr_desc or fr_title or f"Requirement {fr_id}"

        if not fr_full:
            untraced.append(fr_id)
            traceability_map[fr_id] = {
                "best_component": None, "best_sim": 0.0, "traced": False,
                "description": human_desc,
            }
            continue

        # Find best matching component
        best_sim = 0.0
        best_comp = None

        for comp_name, comp_text, comp_req_ids in components:
            if fr_id in comp_req_ids:
                sim = 0.95
            else:
                sim = engine.cosine_sim(fr_full, comp_text)

            if sim > best_sim:
                best_sim = sim
                best_comp = comp_name

        is_traced = best_sim >= threshold
        traceability_map[fr_id] = {
            "best_component": best_comp,
            "best_sim": round(best_sim, 4),
            "traced": is_traced,
            "description": human_desc,
        }

        if is_traced:
            traced_count += 1
        else:
            untraced.append(fr_id)

    total = len(frs)
    score = traced_count / total if total > 0 else 0.0

    logger.info(f"RTS: {traced_count}/{total} = {score:.3f} (θ={threshold}) | Untraced: {untraced}")

    return {
        "score": round(score, 4),
        "traced": traced_count,
        "total": total,
        "threshold": threshold,
        "traceability_map": traceability_map,
        "untraced": untraced,
    }
