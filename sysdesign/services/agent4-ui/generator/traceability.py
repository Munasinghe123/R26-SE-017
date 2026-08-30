"""
generator/traceability.py
==========================
Builds a requirements-to-UI traceability matrix for a generated screen.

The UI generator is instructed (prompts/generation_prompt.txt, RULE 9) to
tag every element that fulfils a specific functional requirement with a
data-fr="FR1,FR2" attribute. This module parses the generated HTML and
produces a matrix showing, for every FR passed to the generator, which UI
elements (if any) implement it — plus a coverage score.

Scoped to functional requirements (FRs) only. NFRs are cross-cutting
concerns already measured screen-wide by the ISO/Nielsen/WCAG evaluator,
so per-element NFR tagging would be redundant with the existing rubric.
"""

from typing import Dict, List
from bs4 import BeautifulSoup


def _describe_element(el) -> str:
    """Human-readable label for a tagged element, for display in the matrix."""
    text = el.get_text(strip=True)
    if text:
        return text[:60]
    for attr in ("aria-label", "placeholder", "value", "title"):
        val = el.get(attr)
        if val:
            return val[:60]
    return f"<{el.name}>"


def build_traceability_matrix(html_string: str, requirements: List[Dict]) -> Dict:
    """
    Parameters
    ----------
    html_string  : generated HTML for one screen
    requirements : list of FR dicts for that screen, each with at least
                   {"id": "FR1", "title": "...", "description": "..."}

    Returns
    -------
    dict:
        matrix             list of {fr_id, title, description, elements, covered}
        coverage_pct       float  % of FRs with >=1 matched element
        total_frs          int
        covered_frs        int
        untagged_elements  int    interactive elements with no data-fr
        total_interactive_elements int
    """
    soup = BeautifulSoup(html_string or "", "lxml")

    tagged = soup.find_all(attrs={"data-fr": True})

    fr_to_elements: Dict[str, List[Dict]] = {}
    for el in tagged:
        fr_ids = [f.strip() for f in (el.get("data-fr") or "").split(",") if f.strip()]
        for fr_id in fr_ids:
            fr_to_elements.setdefault(fr_id, []).append({
                "tag": el.name,
                "label": _describe_element(el),
            })

    matrix = []
    covered_count = 0
    for fr in requirements or []:
        fr_id = fr.get("id", "unknown")
        elements = fr_to_elements.get(fr_id, [])
        covered = len(elements) > 0
        if covered:
            covered_count += 1
        matrix.append({
            "fr_id": fr_id,
            "title": fr.get("title", ""),
            "description": fr.get("description", ""),
            "elements": elements,
            "covered": covered,
        })

    total = len(matrix)
    coverage_pct = round((covered_count / total) * 100, 1) if total else 0.0

    interactive = soup.find_all(["button", "input", "select", "textarea", "a"])
    untagged = [el for el in interactive if not el.get("data-fr")]

    return {
        "matrix": matrix,
        "coverage_pct": coverage_pct,
        "total_frs": total,
        "covered_frs": covered_count,
        "untagged_elements": len(untagged),
        "total_interactive_elements": len(interactive),
    }