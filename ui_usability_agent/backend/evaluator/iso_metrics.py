"""
evaluator/iso_metrics.py
========================
Static-HTML proxy metrics for ISO 9241-11:2018 (Effectiveness, Efficiency,
Satisfaction). See EVALUATION_RATIONALE.md for per-function justification
and academic references.

Sub-metric functions return int in [0, 4]. Only compute_iso_score() parses
raw HTML — sub-metrics accept a pre-parsed BeautifulSoup object so they
can be unit-tested independently.
"""

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Effectiveness
# ---------------------------------------------------------------------------

def nav_depth_score(soup: BeautifulSoup) -> int:
    """
    ISO Effectiveness proxy — navigation cost.

    Counts the maximum nesting depth of <a> tags inside any <nav> element.
    Deeper navigation increases click cost and working memory load.

    Returns
    -------
    4  max_depth ≤ 2  (optimal flat nav)
    2  max_depth = 3  (one sub-menu level)
    0  max_depth ≥ 4  (exceeds recommendation)
    2  no <nav> found (neutral default)

    Ref: ISO 9241-11:2018; Zaphiris & Mtei (1997); WCAG 2.2 SC 2.4.5
    """
    navs = soup.find_all('nav')
    if not navs:
        return 2

    max_depth = 0
    for nav in navs:
        for link in nav.find_all('a'):
            depth = 0
            parent = link.parent
            while parent and parent != nav:
                depth += 1
                parent = parent.parent
            if depth > max_depth:
                max_depth = depth

    if max_depth <= 2:
        return 4
    elif max_depth == 3:
        return 2
    else:
        return 0


def label_pairing_score(soup: BeautifulSoup) -> int:
    """
    ISO Effectiveness proxy — input identification accuracy.

    Checks four programmatic label association patterns (in priority order):
      1. <label for="id"> matched to input id
      2. aria-label attribute on the element
      3. aria-labelledby referencing an existing element id
      4. Input nested inside a <label> (implicit label)

    Covers <input>, <textarea>, and <select>. Excludes non-labelable types
    (hidden, submit, button, checkbox, radio, image, reset, file).

    Returns round(labelled / total × 4)

    Ref: ISO 9241-171:2008 §9.3.14; WCAG 2.2 SC 1.3.1, SC 3.3.2; ARIA 1.2
    """
    EXCLUDED_TYPES = {
        'hidden', 'submit', 'button', 'checkbox', 'radio',
        'image', 'reset', 'file',
    }
    inputs = [
        inp for inp in soup.find_all('input')
        if (inp.get('type', 'text') or 'text').lower() not in EXCLUDED_TYPES
    ]
    inputs += soup.find_all('textarea')
    inputs += soup.find_all('select')

    if not inputs:
        return 4

    matched = 0
    for inp in inputs:
        inp_id = (inp.get('id') or '').strip()
        if inp_id and soup.find('label', attrs={'for': inp_id}):
            matched += 1
            continue
        if (inp.get('aria-label') or '').strip():
            matched += 1
            continue
        lb_id = (inp.get('aria-labelledby') or '').strip()
        if lb_id and soup.find(id=lb_id):
            matched += 1
            continue
        if inp.find_parent('label'):
            matched += 1

    return round((matched / len(inputs)) * 4)


# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------

def form_completion_score(soup: BeautifulSoup) -> int:
    """
    ISO Efficiency proxy — input guidance density.

    Counts text-entry inputs (<input> and <textarea>, excluding non-entry
    types) that carry at least one format hint:
      placeholder  — inline example value (HTML5)
      title        — hover tooltip (HTML 4.01+)
      aria-describedby — linked description element (ARIA 1.2)

    Returns round(hinted / total × 4)

    Ref: ISO 9241-143:2012 §7.2; Nielsen (1994) H6
    """
    EXCLUDED_TYPES = {'hidden', 'submit', 'button', 'image', 'reset', 'file'}
    inputs = [
        inp for inp in soup.find_all('input')
        if (inp.get('type', 'text') or 'text').lower() not in EXCLUDED_TYPES
    ]
    inputs += soup.find_all('textarea')

    if not inputs:
        return 4

    hinted = sum(
        1 for inp in inputs
        if inp.get('placeholder') or inp.get('title') or inp.get('aria-describedby')
    )
    return round((hinted / len(inputs)) * 4)


def heading_hierarchy_score(soup: BeautifulSoup) -> int:
    """
    ISO Efficiency proxy — content scannability.

    Counts forward-level jumps in the h1-h6 sequence where the next heading
    level exceeds the current by more than 1 (e.g. h1→h3 = jump of 2).
    Backward steps are valid and not penalised.

    Returns
    -------
    4  0 jumps    3  1 jump    2  2 jumps    0  3+ jumps
    2  no headings (neutral default)

    Ref: WCAG 2.2 SC 1.3.1, SC 2.4.6; WebAIM semantic structure guidelines
    """
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if not headings:
        return 2

    levels = [int(h.name[1]) for h in headings]
    jumps = sum(
        1 for i in range(1, len(levels))
        if levels[i] - levels[i - 1] > 1
    )

    if jumps == 0:
        return 4
    elif jumps == 1:
        return 3
    elif jumps == 2:
        return 2
    else:
        return 0


# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------

def tab_order_score(soup: BeautifulSoup) -> int:
    """
    ISO Efficiency proxy — keyboard navigation efficiency.

    Checks that interactive elements don't have positive tabindex values 
    (tabindex="1", "2" etc.) which break natural keyboard navigation order.
    
    Positive tabindex values disrupt the expected keyboard navigation order, 
    forcing users to expend extra mental effort and time to navigate the page — 
    a direct efficiency failure per ISO 9241-11.

    Ref: WCAG 2.2 SC 2.4.3 Focus Order (Level A). WAI-ARIA 1.2 tabindex guidance.
    """
    positive_tabindex = soup.find_all(
        attrs={'tabindex': lambda v: v and v.strip().lstrip('-').isdigit() 
               and int(v.strip()) > 0}
    )
    count = len(positive_tabindex)
    if count == 0:   return 4
    elif count == 1: return 3
    elif count == 2: return 2
    elif count == 3: return 1
    else:            return 0


# ---------------------------------------------------------------------------
# Satisfaction
# ---------------------------------------------------------------------------

def button_clarity_score(soup: BeautifulSoup) -> int:
    """
    ISO Satisfaction proxy — action label clarity.

    Collects all <button>, <input type="submit">, and <input type="button">
    elements. A button is "clear" if its effective text (visible text →
    value attribute → aria-label, in that priority) has length > 2 and is
    not in the vague-term list.

    Returns round(clear / total × 4)

    Ref: ISO 9241-143:2012 §8.4; Krug (2014) Ch. 3
    """
    VAGUE = {
        'ok', 'go', 'x', 'click', 'here', 'submit', 'button',
        'yes', 'no', 'done', 'more', '...',
    }

    buttons = soup.find_all('button')
    submit_inputs = soup.find_all(
        'input',
        attrs={'type': lambda t: t and t.lower() in ('submit', 'button')}
    )
    all_buttons = buttons + submit_inputs

    if not all_buttons:
        return 4

    clear = 0
    for btn in all_buttons:
        text  = btn.get_text(strip=True).lower()
        aria  = (btn.get('aria-label') or '').strip().lower()
        value = (btn.get('value') or '').strip().lower()

        if not text and aria and len(aria) > 2 and aria not in VAGUE:
            clear += 1
            continue
        effective = text or value
        if len(effective) > 2 and effective not in VAGUE:
            clear += 1

    return round((clear / len(all_buttons)) * 4)


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------

def compute_iso_score(html_string: str) -> dict:
    """
    Parse *html_string* and return a normalised ISO 9241-11 score.

    Sub-metrics
    -----------
    nav_depth            Effectiveness
    label_pairing        Effectiveness
    form_completion      Efficiency
    heading_hierarchy    Efficiency
    tab_order            Efficiency
    button_clarity       Satisfaction

    Formula: iso_score = (mean(sub_scores) / 4.0) × 100

    Returns
    -------
    dict
        iso_score      int   0-100
        sub_scores     dict  {metric: int 0-4}
        weakest_metric str
    """
    if not html_string or not html_string.strip():
        return {'iso_score': 0, 'sub_scores': {}, 'weakest_metric': 'none'}

    soup = BeautifulSoup(html_string, 'lxml')

    scores = {
        'nav_depth':            nav_depth_score(soup),
        'label_pairing':        label_pairing_score(soup),
        'form_completion':      form_completion_score(soup),
        'heading_hierarchy':    heading_hierarchy_score(soup),
        'tab_order':            tab_order_score(soup),
        'button_clarity':       button_clarity_score(soup),
    }

    raw_average = sum(scores.values()) / len(scores)
    return {
        'iso_score':      round((raw_average / 4.0) * 100),
        'sub_scores':     scores,
        'weakest_metric': min(scores, key=scores.get),
    }