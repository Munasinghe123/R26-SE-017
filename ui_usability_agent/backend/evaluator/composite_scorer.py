"""
evaluator/composite_scorer.py
==============================
Aggregates ISO 9241-11, Nielsen heuristics, and WCAG 2.2 scores into a
single composite usability score, and provides reporting and regression
detection utilities.

Weighting rationale
-------------------
ISO 9241-11   30% — covers usability from a task-performance perspective
                    (effectiveness, efficiency, satisfaction)
Nielsen       30% — covers expert heuristic quality of the interaction design
WCAG 2.2      40% — covers accessibility; given the highest weight because:
                    (a) accessibility is a legal requirement in many
                        jurisdictions (EN 301 549, ADA, EAA),
                    (b) accessibility improvements benefit all users, not just
                        those with disabilities (curb-cut effect),
                    (c) automated WCAG checking is the most objectively
                        verifiable of the three standards

References
----------
ISO 9241-11:2018 Ergonomics of human-system interaction — Part 11.
Nielsen, J. (1994). 10 usability heuristics.
W3C (2023). WCAG 2.2. https://www.w3.org/TR/WCAG22/

EN 301 549 v3.2.1 (2021). Accessibility requirements for ICT products
and services. ETSI.
"""

import json
import os
from datetime import datetime

from evaluator.iso_metrics import compute_iso_score
from evaluator.nielsen_metrics import compute_nielsen_score
from evaluator.wcag_metrics import compute_wcag_score


# ---------------------------------------------------------------------------
# Core evaluator
# ---------------------------------------------------------------------------

def evaluate(html_string: str, iteration_number: int = 1) -> dict:
    """
    Compute a weighted composite usability score from ISO, Nielsen, and WCAG
    sub-evaluations.

    Parameters
    ----------
    html_string      : str  Raw HTML of the generated UI prototype.
    iteration_number : int  Current refinement iteration (1-5). Used to
                            select the pass threshold (thresholds increase
                            with each iteration to enforce progressive quality).

    Thresholds by iteration
    -----------------------
    Iteration 1 → 65   (baseline; newly generated UI)
    Iteration 2 → 75   (first refinement cycle)
    Iteration 3 → 85   (second refinement cycle)
    Iteration 4 → 85   (third refinement cycle — same threshold)
    Iteration 5 → 85   (final iteration)

    The threshold for iterations 1 and 2 is intentionally lower to allow
    the LLM refinement loop to converge without false failures on the first
    pass.

    Returns
    -------
    dict with keys:
        total_score     int   0-100 weighted composite
        iso_score       int   0-100
        nielsen_score   int   0-100
        wcag_score      int   0-100
        iso_details     dict  full result from compute_iso_score
        nielsen_details dict  full result from compute_nielsen_score
        wcag_details    dict  full result from compute_wcag_score
        weakest_standard str  'ISO', 'Nielsen', or 'WCAG'
        weakest_metric   str  name of the lowest sub-metric in weakest standard
        threshold        int  pass threshold for this iteration
        passed           bool total_score >= threshold
        iteration        int  iteration_number
        timestamp        str  ISO 8601 datetime
    """
    safe_html = html_string or ''

    iso_result     = compute_iso_score(safe_html)
    nielsen_result = compute_nielsen_score(safe_html)
    wcag_result    = compute_wcag_score(safe_html)

    iso_score     = iso_result.get('iso_score', 0)
    nielsen_score = nielsen_result.get('nielsen_score', 0)
    wcag_score    = wcag_result.get('wcag_score', 0)

    # Weighted composite
    total_score = (
        iso_score     * 0.30
        + nielsen_score * 0.30
        + wcag_score    * 0.40
    )

    # Identify weakest standard and its lowest sub-metric
    standards = {'ISO': iso_score, 'Nielsen': nielsen_score, 'WCAG': wcag_score}
    weakest_standard = min(standards, key=standards.get)

    if weakest_standard == 'ISO':
        weakest_metric = iso_result.get('weakest_metric', 'unknown')
    elif weakest_standard == 'Nielsen':
        weakest_metric = nielsen_result.get('weakest_metric', 'unknown')
    else:
        weakest_metric = wcag_result.get('weakest_pour', 'unknown')

    thresholds = {1: 65, 2: 75, 3: 85, 4: 85, 5: 85}
    threshold = thresholds.get(iteration_number, 85)
    passed = total_score >= threshold

    return {
        'total_score':      round(total_score),
        'iso_score':        iso_score,
        'nielsen_score':    nielsen_score,
        'wcag_score':       wcag_score,
        'iso_details':      iso_result,
        'nielsen_details':  nielsen_result,
        'wcag_details':     wcag_result,
        'weakest_standard': weakest_standard,
        'weakest_metric':   weakest_metric,
        'threshold':        threshold,
        'passed':           passed,
        'iteration':        iteration_number,
        'timestamp':        datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_score_report(report: dict) -> None:
    """
    Print a formatted usability score table to stdout using Rich.

    Displays
    --------
    • Per-standard score, weight, and weighted contribution
    • Total composite score vs threshold
    • Pass/Fail status
    • Weakest standard and weakest sub-metric (for targeted improvement)
    • Per-standard sub-score breakdown (collapsed by default)

    The Rich library is used for terminal formatting.  If Rich is not
    installed, falls back to plain-text output.
    """
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        _rich_available = True
    except ImportError:
        _rich_available = False

    if not _rich_available:
        _print_plain_report(report)
        return

    console = Console()

    # Main scoring table
    table = Table(
        title='Usability Evaluation Report',
        box=box.ROUNDED,
        show_footer=True,
    )
    table.add_column('Standard',  style='cyan',  footer='TOTAL')
    table.add_column('Score',     justify='right')
    table.add_column('Weight',    justify='right')
    table.add_column('Weighted',  justify='right',
                     footer=str(report.get('total_score', 0)))

    iso_score     = report.get('iso_score', 0)
    nielsen_score = report.get('nielsen_score', 0)
    wcag_score    = report.get('wcag_score', 0)

    table.add_row(
        'ISO 9241-11',
        str(iso_score), '30%',
        f"{iso_score * 0.30:.1f}",
    )
    table.add_row(
        'Nielsen Heuristics',
        str(nielsen_score), '30%',
        f"{nielsen_score * 0.30:.1f}",
    )
    table.add_row(
        'WCAG 2.2',
        str(wcag_score), '40%',
        f"{wcag_score * 0.40:.1f}",
    )

    console.print(table)

    wcag_details = report.get('wcag_details', {})
    if wcag_details.get('reliability') == 'partial':
        console.print(
            Panel(
                "WARNING: axe-core not available - WCAG score is partial "
                "(axe 50% weight redistributed across BS4 checks; WCAG still counts 40% in composite).",
                style='yellow',
                expand=False,
            )
        )

    # Status panel
    total = report.get('total_score', 0)
    threshold = report.get('threshold', 85)
    passed = report.get('passed', False)
    status_colour = 'green' if passed else 'red'
    status_text = '✓ PASSED' if passed else '✗ NEEDS REFINEMENT'

    console.print(
        Panel(
            f"[{status_colour}]{status_text}[/{status_colour}]  "
            f"Score: {total} / Threshold: {threshold}  "
            f"(Iteration {report.get('iteration', 1)})",
            expand=False,
        )
    )

    console.print(
        f"\n[bold]Weakest standard:[/bold] {report.get('weakest_standard', 'N/A')}"
        f"\n[bold]Weakest metric:[/bold]   {report.get('weakest_metric', 'N/A')}"
    )

    # Sub-score breakdown per standard
    for label, key, detail_key in [
        ('ISO sub-scores',     'iso_score',     'iso_details'),
        ('Nielsen sub-scores', 'nielsen_score', 'nielsen_details'),
        ('WCAG sub-scores',    'wcag_score',    'wcag_details'),
    ]:
        detail = report.get(detail_key, {})
        if detail_key == 'wcag_details':
            # Show the BS4 sub-scores (always available) separately from POUR
            wcag_sub = {
                'alt_text':    detail.get('alt_score'),
                'landmarks':   detail.get('landmark_score'),
                'contrast':    detail.get('contrast_score'),
                'lang':        detail.get('lang_score'),
            }
            console.print(f"\n[dim]{label}:[/dim]")
            for metric, score in wcag_sub.items():
                if score is not None:
                    pct = int(score)
                    bar = '█' * (pct // 25) + '░' * (4 - pct // 25)
                    console.print(f"  {metric:<30} {bar}  {pct}%")
            pour = detail.get('pour_scores') or {}
            valid_pour = {k: v for k, v in pour.items() if v is not None}
            if valid_pour:
                console.print("  [dim]POUR breakdown:[/dim]")
                for principle, score in valid_pour.items():
                    console.print(f"    {principle:<28} {score}/25")
            else:
                console.print("  [dim]POUR: unavailable (axe-core not installed)[/dim]")
        else:
            sub = detail.get('sub_scores') or {}
            if sub:
                console.print(f"\n[dim]{label}:[/dim]")
                for metric, score in sorted((k, v) for k, v in sub.items() if v is not None):
                    bar = '█' * score + '░' * (4 - score) if score <= 4 else '█' * 4
                    console.print(f"  {metric:<30} {bar}  {score}")


def _print_plain_report(report: dict) -> None:
    """Fallback plain-text report when Rich is not installed."""
    print('\n=== Usability Evaluation Report ===')
    print(f"ISO 9241-11 :  {report.get('iso_score', 0):>3}  (weight 30%)")
    print(f"Nielsen     :  {report.get('nielsen_score', 0):>3}  (weight 30%)")
    print(f"WCAG 2.2    :  {report.get('wcag_score', 0):>3}  (weight 40%)")
    print(f"{'─' * 35}")
    print(f"Total Score :  {report.get('total_score', 0):>3}  /  {report.get('threshold', 85)} threshold")
    print(f"Status      :  {'PASSED' if report.get('passed') else 'NEEDS REFINEMENT'}")
    print(f"Weakest     :  {report.get('weakest_standard', 'N/A')} → {report.get('weakest_metric', 'N/A')}")

    wcag_details = report.get('wcag_details', {})
    if wcag_details.get('reliability') == 'partial':
        print(
            "WARNING: axe-core not available - WCAG score is partial "
            "(axe 50% weight redistributed across BS4 checks; WCAG still counts 40% in composite)."
        )

    # Sub-score breakdown per standard
    for label, key, detail_key in [
        ('ISO sub-scores',     'iso_score',     'iso_details'),
        ('Nielsen sub-scores', 'nielsen_score', 'nielsen_details'),
        ('WCAG sub-scores',    'wcag_score',    'wcag_details'),
    ]:
        detail = report.get(detail_key, {})
        if detail_key == 'wcag_details':
            # Show the BS4 sub-scores (always available) separately from POUR
            wcag_sub = {
                'alt_text':    detail.get('alt_score'),
                'landmarks':   detail.get('landmark_score'),
                'contrast':    detail.get('contrast_score'),
                'lang':        detail.get('lang_score'),
            }
            print(f"\n{label}:")
            for metric, score in wcag_sub.items():
                if score is not None:
                    pct = int(score)
                    bar = '█' * (pct // 25) + '░' * (4 - pct // 25)
                    print(f"  {metric:<30} {bar}  {pct}%")
            pour = detail.get('pour_scores') or {}
            valid_pour = {k: v for k, v in pour.items() if v is not None}
            if valid_pour:
                print("  POUR breakdown:")
                for principle, score in valid_pour.items():
                    print(f"    {principle:<28} {score}/25")
            else:
                print("  POUR: unavailable (axe-core not installed)")
        else:
            sub = detail.get('sub_scores') or {}
            if sub:
                print(f"\n{label}:")
                for metric, score in sorted((k, v) for k, v in sub.items() if v is not None):
                    bar = '█' * min(score, 4) + '░' * max(0, 4 - score) if score <= 4 else '█' * 4
                    print(f"  {metric:<30} {bar}  {score}")


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_score_report(report: dict, output_path: str = 'outputs/score_report.json') -> None:
    """
    Persist *report* as formatted JSON at *output_path*.

    Creates the output directory if it does not exist.  Uses UTF-8 encoding
    to safely handle any Unicode in HTML content captured in the report.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Regression detection
# ---------------------------------------------------------------------------

def detect_regression(current_report: dict, previous_report: dict | None) -> list:
    """
    Compare the current evaluation report against the previous iteration's
    report and return a list of score regressions.

    A regression occurs when a standard's score in the current report is
    lower than in the previous report.  This is used by the refinement loop
    to detect when a UI change that improved one area degraded another.

    Parameters
    ----------
    current_report  : dict  Result of the current evaluate() call.
    previous_report : dict or None  Result of the previous evaluate() call,
                          or None if this is the first iteration.

    Returns
    -------
    list of dict, each with:
        standard  str   'iso_score', 'nielsen_score', or 'wcag_score'
        drop      float Points lost relative to the previous report
        previous  int   Previous score
        current   int   Current score

    Returns an empty list if no regressions or if previous_report is None.
    """
    if not previous_report:
        return []

    regressions = []
    for key in ('iso_score', 'nielsen_score', 'wcag_score'):
        current  = current_report.get(key, 0)
        previous = previous_report.get(key, 0)
        if current < previous:
            regressions.append({
                'standard': key,
                'drop':     round(previous - current, 1),
                'previous': previous,
                'current':  current,
            })

    return regressions
