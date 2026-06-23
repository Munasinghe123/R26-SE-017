"""
generator/refinement_controller.py
===================================
Iterative refinement loop for generated UI prototypes.

Pipeline: evaluate -> if it doesn't pass this iteration's threshold, look
up a targeted fix prompt for the weakest sub-metric and ask the LLM to
revise the existing HTML (not regenerate from scratch) -> re-evaluate ->
repeat, up to 5 iterations total, matching the thresholds already defined
in evaluator/composite_scorer.py (65 / 75 / 85 / 85 / 85).

This is intentionally a plain bounded loop, not a LangGraph agent graph —
each step is a straightforward evaluate -> diagnose -> revise -> re-evaluate
cycle with explicit regression checking, which doesn't need branching or
shared graph state to express.
"""

from typing import Dict, List, Optional

from evaluator.composite_scorer import evaluate, detect_regression
from generator.ui_generator import generate_ui, refine_ui
from prompts.refinement_templates import get_refinement_instructions

MAX_ITERATIONS = 5


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
    requirements   : dict  Per-screen requirements payload, as produced by
                            screen_planner.screens_to_requirements().
    screen_type    : str   e.g. "list", "form", "auth", "detail".
    initial_html   : str or None. If None, a fresh first-pass HTML is
                            generated via generate_ui(). Pass an existing
                            HTML string to refine an already generated
                            screen instead of generating a new one.
    max_iterations : int   Hard cap on refinement iterations (default 5,
                            matching the thresholds defined in
                            composite_scorer.evaluate()).

    Returns
    -------
    dict
        final_html   str   Best-scoring HTML produced across all iterations.
        final_report dict  evaluate() report matching final_html.
        passed       bool  Whether final_report met its iteration threshold.
        iterations   int   Number of iterations actually run.
        history      list  One entry per iteration:
                              {iteration, html, report, regressions,
                               applied_fix}
                            applied_fix is None on the iteration where the
                            loop stopped (passed, or iterations exhausted).
        regressed    bool  True if the last iteration run scored lower than
                            the best iteration seen, meaning final_html was
                            rolled back to an earlier iteration.
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

        if best_entry is None or report["total_score"] >= best_entry["report"]["total_score"]:
            best_entry = entry

        if report["passed"] or iteration == max_iterations:
            break

        instructions = get_refinement_instructions(
            report["weakest_standard"], report["weakest_metric"]
        )
        entry["applied_fix"] = {
            "weakest_standard": report["weakest_standard"],
            "weakest_metric": report["weakest_metric"],
            "instructions": instructions,
        }

        previous_report = report
        html = refine_ui(html, requirements, screen_type, instructions)

    last_entry = history[-1]
    regressed = best_entry is not last_entry

    return {
        "final_html": best_entry["html"],
        "final_report": best_entry["report"],
        "passed": bool(best_entry["report"]["passed"]),
        "iterations": len(history),
        "history": history,
        "regressed": regressed,
    }