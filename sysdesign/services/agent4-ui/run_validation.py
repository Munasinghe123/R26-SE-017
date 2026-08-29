"""
run_validation.py
==================
Validates the UI/UX & Usability Agent's refinement loop against the
Section 3.5 proposal targets. Fully deterministic — no LLM-as-judge,
no human review step. Uses the same evaluate() / run_refinement_loop()
functions that power the live pipeline, so validation results always
reflect the actual production scoring logic.

Targets (from proposal Section 3.5):
    T1: final composite score >= 85 on convergence
    T2: mean per-iteration improvement > 10%
    T3: convergence within 5 iterations for >90% of scenarios

Usage:
    python run_validation.py
"""

import json
import os
import statistics
from datetime import datetime

from generator.refinement_controller import run_refinement_loop
from evaluator.composite_scorer import evaluate

# ---------------------------------------------------------------------------
# Fixed validation scenarios (5, per proposal). Each maps to one of the
# 4 existing screen_type values (auth/form/list/detail) — documented
# design decision, see project memory.
# ---------------------------------------------------------------------------
SCENARIOS = [
    {
        "scenario_id": "S1",
        "screen_type": "auth",
        "requirements": {
            "project_name": "StayEasy Hotel Booking Platform",
            "screen_id": "login",
            "screen_name": "User Login",
            "screen_type": "auth",
            "user_role": "Guest",
            "purpose": "Allow registered users to log in.",
            "key_actions": ["Log in"],
            "functional_requirements": [
                {"id": "FR02", "title": "User Login/Logout", "description": "Registered users can log in with credentials."}
            ],
            "non_functional_requirements": [
                {"id": "NFR02", "type": "Accessibility", "description": "WCAG 2.2 AA compliance."}
            ],
        },
    },
    {
        "scenario_id": "S2",
        "screen_type": "form",
        "requirements": {
            "project_name": "StayEasy Hotel Booking Platform",
            "screen_id": "create_booking",
            "screen_name": "Create Booking",
            "screen_type": "form",
            "user_role": "Guest",
            "purpose": "Let guests create a reservation.",
            "key_actions": ["Confirm booking"],
            "functional_requirements": [
                {"id": "FR05", "title": "Create Booking", "description": "Guests select room and dates, provide payment info."}
            ],
            "non_functional_requirements": [
                {"id": "NFR02", "type": "Accessibility", "description": "WCAG 2.2 AA compliance."}
            ],
        },
    },
    {
        "scenario_id": "S3",
        "screen_type": "list",
        "requirements": {
            "project_name": "StayEasy Hotel Booking Platform",
            "screen_id": "manage_bookings",
            "screen_name": "Manage Bookings",
            "screen_type": "list",
            "user_role": "Hotel Staff",
            "purpose": "Staff view and update all bookings.",
            "key_actions": ["Update status"],
            "functional_requirements": [
                {"id": "FR09", "title": "Staff - Manage Bookings", "description": "View all bookings and update status."}
            ],
            "non_functional_requirements": [
                {"id": "NFR02", "type": "Accessibility", "description": "WCAG 2.2 AA compliance."}
            ],
        },
    },
    {
        "scenario_id": "S4",
        "screen_type": "detail",
        "requirements": {
            "project_name": "StayEasy Hotel Booking Platform",
            "screen_id": "room_details",
            "screen_name": "Room Details",
            "screen_type": "detail",
            "user_role": "Guest",
            "purpose": "View detailed info about a specific room.",
            "key_actions": ["Book now"],
            "functional_requirements": [
                {"id": "FR04", "title": "View Room Details", "description": "View photos, description, price, amenities."}
            ],
            "non_functional_requirements": [
                {"id": "NFR02", "type": "Accessibility", "description": "WCAG 2.2 AA compliance."}
            ],
        },
    },
    {
        "scenario_id": "S5",
        "screen_type": "list",
        "requirements": {
            "project_name": "StayEasy Hotel Booking Platform",
            "screen_id": "room_inventory",
            "screen_name": "Room Inventory",
            "screen_type": "list",
            "user_role": "Hotel Staff",
            "purpose": "Staff manage room availability and pricing.",
            "key_actions": ["Update room"],
            "functional_requirements": [
                {"id": "FR10", "title": "Staff - Manage Room Inventory", "description": "Update availability, pricing, room details."}
            ],
            "non_functional_requirements": [
                {"id": "NFR02", "type": "Accessibility", "description": "WCAG 2.2 AA compliance."}
            ],
        },
    },
]

TARGET_FINAL_SCORE = 85
TARGET_MEAN_IMPROVEMENT_PCT = 10
TARGET_CONVERGENCE_ITER = 5
TARGET_CONVERGENCE_RATE_PCT = 90


def run_scenario(scenario: dict) -> dict:
    """Run one scenario with refinement enabled AND baseline-only (no refinement),
    so we can report the delta the refinement loop actually contributes."""
    req = scenario["requirements"]
    screen_type = scenario["screen_type"]

    # Baseline: single-pass generation, no refinement iterations
    from generator.ui_generator import generate_ui
    baseline_html = generate_ui(req, screen_type)
    baseline_report = evaluate(baseline_html, iteration_number=1)

    # Full refinement loop
    result = run_refinement_loop(req, screen_type, initial_html=baseline_html)

    per_iter_scores = [e["report"]["total_score"] for e in result["history"]]
    improvements = [
        per_iter_scores[i] - per_iter_scores[i - 1]
        for i in range(1, len(per_iter_scores))
    ]
    mean_improvement_pct = (
        statistics.mean(improvements) if improvements else 0.0
    )

    return {
        "scenario_id": scenario["scenario_id"],
        "screen_type": screen_type,
        "baseline_score": baseline_report["total_score"],
        "final_score": result["final_report"]["total_score"],
        "iterations_to_converge": result["iterations"],
        "converged": result["final_report"]["total_score"] >= TARGET_FINAL_SCORE,
        "converged_within_5": result["iterations"] <= TARGET_CONVERGENCE_ITER
                              and result["final_report"]["total_score"] >= TARGET_FINAL_SCORE,
        "regressed": result["regressed"],
        "per_iteration_scores": per_iter_scores,
        "mean_improvement_per_iteration": round(mean_improvement_pct, 2),
        "score_delta_vs_baseline": result["final_report"]["total_score"] - baseline_report["total_score"],
    }


def run_all() -> dict:
    print(f"Running {len(SCENARIOS)} validation scenarios...\n")
    results = []
    for scenario in SCENARIOS:
        print(f"--- {scenario['scenario_id']} ({scenario['screen_type']}) ---")
        r = run_scenario(scenario)
        print(f"  Baseline: {r['baseline_score']}  ->  Final: {r['final_score']} "
              f"({r['iterations_to_converge']} iter, converged={r['converged']})")
        results.append(r)

    final_scores = [r["final_score"] for r in results]
    mean_final_score = statistics.mean(final_scores)
    mean_improvement = statistics.mean(r["mean_improvement_per_iteration"] for r in results)
    convergence_rate_pct = (
        sum(1 for r in results if r["converged_within_5"]) / len(results) * 100
    )
    regression_count = sum(1 for r in results if r["regressed"])

    summary = {
        "run_at": datetime.now().isoformat(),
        "num_scenarios": len(results),
        "mean_final_score": round(mean_final_score, 2),
        "mean_improvement_per_iteration_pct": round(mean_improvement, 2),
        "convergence_rate_pct": round(convergence_rate_pct, 2),
        "scenarios_with_regression": regression_count,
        "targets": {
            "T1_final_score_ge_85": mean_final_score >= TARGET_FINAL_SCORE,
            "T2_mean_improvement_gt_10pct": mean_improvement > TARGET_MEAN_IMPROVEMENT_PCT,
            "T3_convergence_rate_gt_90pct": convergence_rate_pct > TARGET_CONVERGENCE_RATE_PCT,
        },
        "results": results,
    }
    return summary


def print_summary(summary: dict):
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Scenarios run:              {summary['num_scenarios']}")
    print(f"Mean final score:           {summary['mean_final_score']} (target >= {TARGET_FINAL_SCORE})")
    print(f"Mean improvement/iteration: {summary['mean_improvement_per_iteration_pct']}% (target > {TARGET_MEAN_IMPROVEMENT_PCT}%)")
    print(f"Convergence rate (<=5 iter): {summary['convergence_rate_pct']}% (target > {TARGET_CONVERGENCE_RATE_PCT}%)")
    print(f"Scenarios with rollback:    {summary['scenarios_with_regression']}")
    print("-" * 60)
    for target, passed in summary["targets"].items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {target}")
    print("=" * 60)


if __name__ == "__main__":
    summary = run_all()
    print_summary(summary)

    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "validation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nFull report saved to {out_path}")