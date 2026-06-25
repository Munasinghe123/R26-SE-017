"""
generator/refinement_controller.py
===================================
Iterative refinement loop for generated UI prototypes.

Each iteration collects ALL sub-metrics scoring below 2 across every
standard, bundles their fix instructions into one combined prompt, and
sends a single targeted revision request to the LLM. This is more
effective than fixing one metric per pass, because Nielsen typically has
multiple low-scoring sub-metrics simultaneously.

Deliberately a plain bounded loop — no LangGraph needed.
"""

from typing import Dict, List, Optional

from evaluator.composite_scorer import evaluate, detect_regression
from generator.ui_generator import generate_ui, refine_ui
from prompts.refinement_templates import get_refinement_instructions

MAX_ITERATIONS = 5
WEAK_THRESHOLD = 2   # sub-metric scores at or below this get included in fix


def _collect_weak_instructions(report: dict) -> tuple:
    """
    Scan all sub-metric scores across ISO, Nielsen, and WCAG and collect
    fix instructions for every metric scoring <= WEAK_THRESHOLD.

    Returns (combined_instructions: str, fixes_list: list)
    where fixes_list is for logging/history.
    """
    fixes = []

    # ISO sub-scores
    iso_sub = report.get("iso_details", {}).get("sub_scores", {})
    for metric, score in iso_sub.items():
        if score <= WEAK_THRESHOLD:
            instructions = get_refinement_instructions("ISO", metric)
            fixes.append({"standard": "ISO", "metric": metric, "score": score, "instructions": instructions})

    # Nielsen sub-scores
    nielsen_sub = report.get("nielsen_details", {}).get("sub_scores", {})
    for metric, score in nielsen_sub.items():
        if score <= WEAK_THRESHOLD:
            instructions = get_refinement_instructions("Nielsen", metric)
            fixes.append({"standard": "Nielsen", "metric": metric, "score": score, "instructions": instructions})

    # WCAG — use weakest_pour if WCAG score is low
    if report.get("wcag_score", 100) < 70:
        weakest_pour = report.get("wcag_details", {}).get("weakest_pour", "unavailable")
        instructions = get_refinement_instructions("WCAG", weakest_pour)
        fixes.append({"standard": "WCAG", "metric": weakest_pour, "score": report["wcag_score"], "instructions": instructions})

    if not fixes:
        # nothing obviously weak — fall back to weakest standard
        instructions = get_refinement_instructions(
            report["weakest_standard"], report["weakest_metric"]
        )
        fixes.append({
            "standard": report["weakest_standard"],
            "metric": report["weakest_metric"],
            "score": None,
            "instructions": instructions,
        })

    # Combine into one prompt block
    combined = "\n\n".join(
        f"FIX {i+1} ({f['standard']} / {f['metric']}):\n{f['instructions']}"
        for i, f in enumerate(fixes)
    )
    return combined, fixes


def run_refinement_loop(
    requirements: Dict,
    screen_type: str,
    initial_html: Optional[str] = None,
    max_iterations: int = MAX_ITERATIONS,
) -> Dict:
    """
    Run the iterative refinement loop for one screen.

    Parameters
    ----------
    requirements   : dict
    screen_type    : str
    initial_html   : str or None — if None, generates a fresh first pass
    max_iterations : int — hard cap (default 5)

    Returns
    -------
    dict with keys:
        final_html, final_report, passed, iterations, history, regressed
    """
    html = initial_html or generate_ui(requirements, screen_type)

    history: List[Dict] = []
    best_entry: Optional[Dict] = None
    previous_report: Optional[Dict] = None

    for iteration in range(1, max_iterations + 1):
        report = evaluate(html, iteration_number=iteration)
        regressions = detect_regression(report, previous_report)

        entry = {
            "iteration": iteration,
            "html": html,
            "report": report,
            "regressions": regressions,
            "applied_fix": None,
        }
        history.append(entry)

        # Track best scoring iteration for regression rollback
        if best_entry is None or report["total_score"] >= best_entry["report"]["total_score"]:
            best_entry = entry

        # Stop if target reached or iterations exhausted
        if report["total_score"] >= 85 or iteration == max_iterations:
            break

        # Collect ALL weak sub-metrics and bundle into one fix prompt
        combined_instructions, fixes_list = _collect_weak_instructions(report)

        entry["applied_fix"] = {
            "weakest_standard": report["weakest_standard"],
            "weakest_metric": report["weakest_metric"],
            "all_fixes": fixes_list,
            "instructions": combined_instructions,
        }

        previous_report = report
        html = refine_ui(html, requirements, screen_type, combined_instructions)

    last_entry = history[-1]
    regressed = best_entry is not last_entry

    return {
        "final_html": best_entry["html"],
        "final_report": best_entry["report"],
        "passed": best_entry["report"]["total_score"] >= 85,
        "iterations": len(history),
        "history": history,
        "regressed": regressed,
    }