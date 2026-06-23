"""
prompts/refinement_templates.py
================================
Targeted fix instructions per weakest sub-metric, used by
generator/refinement_controller.py to ask the LLM to revise (not
regenerate) a generated screen.

Each evaluate() report names exactly one weakest_standard + weakest_metric
(see evaluator/composite_scorer.py). The metric names are unique across
ISO, Nielsen, and WCAG (POUR), so REFINEMENT_PROMPTS is keyed directly by
weakest_metric. weakest_standard is kept as an argument for clarity and is
only relevant for the WCAG fallback cases.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# ISO 9241-11 sub-metric fixes
# ---------------------------------------------------------------------------
ISO_PROMPTS = {
    "nav_depth": (
        "The <nav> menu is nested too deep (more than 2 levels of <a> tags "
        "inside <nav>). Flatten it to at most 2 levels — move sub-items into "
        "a single top-level list or a simple dropdown, not nested <ul> chains."
    ),
    "label_pairing": (
        "One or more <input>, <textarea>, or <select> elements are missing a "
        "programmatically associated label. For every such element, add a "
        "matching <label for=\"id\">, or an aria-label, or wrap it inside a "
        "<label>. Every form control must have exactly one of these."
    ),
    "form_completion": (
        "Several text-entry inputs have no format guidance. Add a "
        "placeholder, a title attribute, or an aria-describedby pointing to "
        "a short hint paragraph, on every text-entry <input> and <textarea>."
    ),
    "heading_hierarchy": (
        "The heading levels (h1-h6) skip levels (e.g. h1 followed directly "
        "by h3). Renumber headings so each level only increases by 1 at a "
        "time relative to the previous heading."
    ),
    "tab_order": (
        "One or more interactive elements have a positive tabindex value "
        "(tabindex=\"1\", \"2\", etc.). Remove all positive tabindex "
        "attributes so keyboard focus follows natural DOM order."
    ),
    "button_clarity": (
        "Some buttons use vague labels (\"OK\", \"Submit\", \"Click here\"). "
        "Replace them with specific action verbs describing the outcome "
        "(e.g. \"Save changes\", \"Send message\"), matching this screen's "
        "primary_action and domain."
    ),
}

# ---------------------------------------------------------------------------
# Nielsen heuristic sub-metric fixes
# ---------------------------------------------------------------------------
NIELSEN_PROMPTS = {
    "system_status": (
        "The page is missing visible system-status signals. Add a "
        "<progress> element in the header, an aria-current=\"page\" "
        "attribute on the active nav link, and an active/current/selected "
        "class on the current nav item."
    ),
    "user_control": (
        "There is no clearly marked exit path. Add at least one visible "
        "Cancel, Back, or Reset control near the primary action so users can "
        "back out without completing the flow."
    ),
    "button_consistency": (
        "Buttons use inconsistent visual styling. Make every primary button "
        "share one exact class string, every secondary button share one "
        "exact class string, and every danger button share one exact class "
        "string, per the project's button style rules."
    ),
    "error_prevention": (
        "Several text-entry inputs lack HTML5 constraint-validation "
        "attributes. Add required, pattern, minlength/maxlength, or "
        "min/max, and use semantic input types (email, number, tel, date, "
        "url) wherever appropriate."
    ),
    "form_input_type": (
        "Inputs use generic type=\"text\" where a semantic type would help. "
        "Change inputs to type=\"email\", \"tel\", \"date\", \"number\", or "
        "\"url\" wherever the field's purpose matches one of these."
    ),
    "minimalist_design": (
        "The page relies too heavily on undifferentiated <div> wrappers. "
        "Replace generic divs with semantic landmarks where appropriate: "
        "<header> for the top bar, <main> for page content, <nav> for "
        "navigation/pagination, <section> for each major content block, "
        "<footer> for the page footer, <article> for repeated card items."
    ),
    "error_message": (
        "There is no structural error-messaging infrastructure. Add a "
        "role=\"alert\" aria-live region near the filter/search controls and "
        "another near the form submit button, each hidden by default."
    ),
    "focus_indicator": (
        "Interactive elements are missing visible focus styles. Add "
        "focus:outline-none focus:ring-2 focus:ring-violet-500 "
        "focus:ring-offset-2 to every button, link, input, select, and "
        "textarea that doesn't already have it."
    ),
}

# ---------------------------------------------------------------------------
# WCAG 2.2 POUR-level fixes (weakest_metric here is a POUR principle name,
# since wcag_metrics.py reports weakest_pour as the WCAG "weakest_metric")
# ---------------------------------------------------------------------------
WCAG_PROMPTS = {
    "Perceivable": (
        "Fix Perceivable-principle accessibility issues: add meaningful alt "
        "text to every non-decorative <img>, mark purely decorative images "
        "with role=\"presentation\" and alt=\"\", and fix any text/background "
        "colour combinations that are too low-contrast (avoid light gray "
        "text on white, low-opacity text classes, or white-on-white)."
    ),
    "Operable": (
        "Fix Operable-principle accessibility issues: ensure every "
        "interactive element is reachable and operable by keyboard, remove "
        "positive tabindex values, and add ARIA landmark roles (main, nav, "
        "banner/header, contentinfo/footer) so users can skip directly to "
        "page regions instead of tabbing through everything."
    ),
    "Understandable": (
        "Fix Understandable-principle accessibility issues: make sure every "
        "form control has a properly associated <label>, the <html> tag has "
        "a valid lang attribute (e.g. lang=\"en\"), and every <select> has a "
        "linked label."
    ),
    "Robust": (
        "Fix Robust-principle accessibility issues: ensure all ARIA "
        "attributes and roles used are valid (no typos in role names or "
        "aria-* attribute names), remove any duplicate id attributes, and "
        "make sure ARIA parent/child role relationships are correct (e.g. "
        "role=\"listitem\" only inside role=\"list\")."
    ),
    "unavailable": (
        "WCAG automated checks were inconclusive. Make a general accessibility "
        "pass: confirm every image has correct alt text, every form control "
        "has a label, ARIA landmark roles (main/nav/header/footer) are "
        "present, the <html> tag has lang=\"en\", and text contrast is high "
        "(avoid light gray on white)."
    ),
}

GENERIC_FALLBACK = (
    "Make a general usability and accessibility pass on this screen: add "
    "missing labels and alt text, ensure visible focus styles on every "
    "interactive element, use semantic HTML landmarks instead of bare divs, "
    "and use specific, descriptive button labels."
)

REFINEMENT_PROMPTS = {**ISO_PROMPTS, **NIELSEN_PROMPTS, **WCAG_PROMPTS}


def get_refinement_instructions(weakest_standard: Optional[str], weakest_metric: Optional[str]) -> str:
    """
    Look up the targeted fix instructions for a given evaluate() report's
    weakest_standard / weakest_metric pair.

    Falls back to GENERIC_FALLBACK if the metric name isn't recognised
    (e.g. 'unknown', 'none', or a future metric added to the evaluator
    without a matching entry here).
    """
    if weakest_metric and weakest_metric in REFINEMENT_PROMPTS:
        return REFINEMENT_PROMPTS[weakest_metric]
    return GENERIC_FALLBACK