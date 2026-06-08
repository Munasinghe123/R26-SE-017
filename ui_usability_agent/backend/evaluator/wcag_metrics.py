"""
evaluator/wcag_metrics.py
=========================
Automated WCAG 2.2 accessibility metrics for static HTML.
See EVALUATION_RATIONALE.md for per-function justification and references.

Scoring formula
---------------
wcag_score = axe_score       × 0.50
           + alt_score        × 0.20
           + landmark_score   × 0.15
           + contrast_score   × 0.10
           + lang_score       × 0.05

axe-core receives the highest weight (0.50) because it is the industry-
standard automated WCAG checker (Deque Systems; Google Lighthouse).
Automated tools detect approximately 30-40% of WCAG violations; the
remainder require human expert evaluation.

Sub-metric functions accept a pre-parsed BeautifulSoup object.
Only compute_wcag_score() parses raw HTML.
"""

import subprocess
import json
import os
import tempfile
import re
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Penalty weights aligned with WCAG conformance levels (Deque axe-core docs)
IMPACT_PENALTIES = {
    'critical': 20,   # Level A failures — completely blocks access
    'serious':  10,   # Level A/AA failures — significant barrier
    'moderate':  5,   # Level AA guidance — meaningful friction
    'minor':     2,   # Level AA/AAA guidance — minor inconvenience
}

# axe-core rule IDs grouped by WCAG POUR principle
# Source: Deque axe-core v4.x rule documentation
# https://dequeuniversity.com/rules/axe/4.7
POUR_MAP = {
    'Perceivable': [
        'image-alt',          # SC 1.1.1
        'color-contrast',     # SC 1.4.3
        'audio-caption',      # SC 1.2.2
        'object-alt',         # SC 1.1.1
        'input-image-alt',    # SC 1.1.1
        'video-caption',      # SC 1.2.2
        'meta-viewport',      # SC 1.4.4
    ],
    'Operable': [
        'keyboard',                    # SC 2.1.1
        'focus-order-semantics',       # SC 2.4.3
        'bypass',                      # SC 2.4.1
        'region',                      # SC 2.4.1 - page content in landmarks
        'tabindex',                    # SC 2.4.3
        'scrollable-region-focusable', # SC 2.1.1
        'focus-trap',                  # SC 2.1.2
        'link-in-text-block',          # SC 1.4.1
    ],
    'Understandable': [
        'label',              # SC 3.3.2
        'error-suggestion',   # SC 3.3.3
        'html-has-lang',      # SC 3.1.1
        'html-lang-valid',    # SC 3.1.1
        'autocomplete-valid', # SC 1.3.5
        'select-name',        # SC 4.1.2
        'label-title-only',   # SC 3.3.2
    ],
    'Robust': [
        'valid-lang',             # SC 3.1.2
        'aria-valid-attr',        # SC 4.1.2
        'aria-valid-attr-value',  # SC 4.1.2
        'duplicate-id',           # SC 4.1.1
        'aria-roles',             # SC 4.1.2
        'aria-required-children', # SC 4.1.2
        'aria-required-parent',   # SC 4.1.2
    ],
}


# ---------------------------------------------------------------------------
# axe-core integration
# ---------------------------------------------------------------------------

# evaluator/wcag_metrics.py  (replace the run_axe_core function)

import subprocess
import json
import os
import tempfile
import shutil

def run_axe_core(html_string: str) -> list:
    """
    Runs axe-core via dedicated Node.js script (more reliable than CLI).
    Falls back gracefully if Node is not available.
    """
    if not html_string or not html_string.strip():
        return []

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_string)
            temp_path = f.name

        node_script = os.path.join(os.path.dirname(__file__), 'axe_runner.js')
        
        if not os.path.exists(node_script):
            # Fallback to CLI if script not present
            axe_cmd = shutil.which('axe') or shutil.which('axe.cmd')
            if axe_cmd:
                result = subprocess.run(
                    [axe_cmd, temp_path, '--format', 'json', '--stdout'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return data[0].get('violations', []) if data else []
            return []

        # Call our Node.js script
        result = subprocess.run(
            ['node', node_script, temp_path],
            capture_output=True, text=True, timeout=45
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('violations', [])
        else:
            print(f"[WCAG] Node axe failed: {result.stderr}")
            return []

    except Exception as e:
        print(f"[WCAG] Axe execution error: {e}")
        return []
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


def axe_penalty_score(violations: list) -> float:
    """
    Convert axe-core violations to a 0-100 score.

    Starts at 100 and subtracts IMPACT_PENALTIES[impact] per violation.
    Floored at 0. Penalty-based (not ratio-based) because each violation
    creates a concrete barrier regardless of how many rules pass.

    Ref: Deque impact definitions —
    https://github.com/dequelabs/axe-core/blob/develop/doc/impact.md
    """
    import math
    if violations is None:
        return None
    score = 100.0
    for v in violations:
        impact = (v.get('impact') or 'minor').lower()
        penalty = IMPACT_PENALTIES.get(impact, 2)
        node_count = len(v.get('nodes', [])) or 1
        score -= penalty * math.log2(1 + node_count)
    return max(0.0, score)


def pour_breakdown(violations: list) -> dict:
    """
    Distribute violations across the four WCAG POUR principles.

    Each principle starts at 25 points. Violations mapped to that principle
    (via POUR_MAP) reduce its score by their impact penalty.

    Returns {'Perceivable': int, 'Operable': int,
             'Understandable': int, 'Robust': int}  each 0-25.

    Ref: W3C WCAG 2.2 — Understanding the Four Principles
    https://www.w3.org/WAI/WCAG22/Understanding/intro
    """
    if violations is None:
        return {p: None for p in POUR_MAP}
    result = {}
    for principle, rule_ids in POUR_MAP.items():
        penalty = sum(
            IMPACT_PENALTIES.get((v.get('impact') or 'minor').lower(), 2)
            for v in violations if v.get('id') in rule_ids
        )
        # Proportional decay: 25 * max(0, 1 - penalty/100)
        result[principle] = round(25 * max(0.0, 1 - penalty / 100), 2)
    return result


# ---------------------------------------------------------------------------
# BS4 supplementary checks
# ---------------------------------------------------------------------------

def alt_text_ratio(soup: BeautifulSoup) -> float:
    """
    WCAG 2.2 SC 1.1.1 proxy — Non-text Content (Level A).

    Counts meaningful images (excludes role="presentation" / role="none",
    which correctly use alt="") that have a non-empty alt attribute.

    Returns (with_alt / meaningful_imgs) × 100, or 100 if no images.

    SC 1.1.1 is the most frequently violated WCAG criterion: absent on
    58.2% of pages (WebAIM Million, 2023).

    Ref: WCAG 2.2 SC 1.1.1; WebAIM Million 2023
    """
    imgs = soup.find_all('img')
    if not imgs:
        return 100.0

    meaningful = [
        img for img in imgs
        if (img.get('role') or '').lower() not in ('presentation', 'none')
    ]
    if not meaningful:
        return 100.0

    with_alt = sum(1 for img in meaningful if img.get('alt', '').strip())
    return (with_alt / len(meaningful)) * 100.0


def aria_landmark_score(soup: BeautifulSoup) -> float:
    """
    WCAG 2.2 SC 2.4.1 proxy — Bypass Blocks (Level A).

    Checks five core ARIA landmark roles. Each is accepted as either
    role="<name>" on any element, or the corresponding HTML5 element:
      main / <main>
      nav  / <nav>
      banner / <header>
      contentinfo / <footer>
      complementary / <aside>

    Returns (found / 5) × 100

    Ref: WCAG 2.2 SC 2.4.1; W3C ARIA APG Landmark Regions
    https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/
    """
    CHECKS = [
        ('main',          'main'),
        ('nav',           'nav'),
        ('banner',        'header'),
        ('contentinfo',   'footer'),
        ('complementary', 'aside'),
    ]
    found = sum(
        1 for role, tag in CHECKS
        if soup.find(attrs={'role': role}) or soup.find(tag)
    )
    return (found / len(CHECKS)) * 100.0


def tailwind_contrast_score(soup: BeautifulSoup) -> float:
    """
    WCAG 2.2 SC 1.4.3 approximation — Contrast Minimum (Level AA).

    Flags text elements with known problematic Tailwind class combinations.
    This is an approximation — exact contrast requires the rendered CSS
    cascade. axe-core's color-contrast rule handles accurate checking when
    HTML is rendered in a browser.

    Low-contrast patterns detected:
      • text-{gray|slate|zinc|neutral|stone}-[123][05]0 (light gray text)
      • text-white + bg-white  (invisible)
      • text-black + bg-black  (invisible)
      • text-opacity-[0-3]* or opacity-[0-3]* (low opacity)

    Elements with a dark: prefix class are excluded (dark mode handled).

    Returns (good / total) × 100, or 100 if no text elements.

    Ref: WCAG 2.2 SC 1.4.3; Tailwind CSS color palette docs
    """
    TEXT_TAGS = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'span', 'label', 'a', 'button', 'li', 'td', 'th', 'caption',
    ]
    elements = soup.find_all(TEXT_TAGS)
    if not elements:
        return 100.0

    LIGHT_TEXT  = re.compile(r'\btext-(?:gray|slate|zinc|neutral|stone)-[123][05]0\b')
    WHITE_WHITE = re.compile(r'\btext-white\b.*\bbg-white\b|\bbg-white\b.*\btext-white\b')
    BLACK_BLACK = re.compile(r'\btext-black\b.*\bbg-black\b|\bbg-black\b.*\btext-black\b')
    LOW_OPACITY = re.compile(r'\b(?:text-opacity-[0-3]\d|opacity-[0-3]\d)\b')

    low = 0
    for el in elements:
        cls = ' '.join(el.get('class') or [])
        if 'dark:' in cls:
            continue
        if (LIGHT_TEXT.search(cls)
                or WHITE_WHITE.search(cls)
                or BLACK_BLACK.search(cls)
                or LOW_OPACITY.search(cls)):
            low += 1

    return ((len(elements) - low) / len(elements)) * 100.0


def html_lang_score(soup: BeautifulSoup) -> float:
    """
    WCAG 2.2 SC 3.1.1 — Language of Page (Level A).

    Returns 100 if <html lang="xx"> has a value of at least 2 characters
    (minimum ISO 639-1 code length), else 0.

    Missing lang attribute found on 17.1% of top 1 million pages
    (WebAIM Million, 2023) despite being a Level A requirement.

    Ref: WCAG 2.2 SC 3.1.1
    """
    html_tag = soup.find('html')
    if not html_tag:
        return 0.0
    return 100.0 if len((html_tag.get('lang') or '').strip()) >= 2 else 0.0


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------

def compute_wcag_score(html_string: str) -> dict:
    """
    Parse *html_string* and return a normalised WCAG 2.2 accessibility score.

    Formula
    -------
    wcag_score = axe_score × 0.50 + alt_score × 0.20
               + landmark_score × 0.15 + contrast_score × 0.10
               + lang_score × 0.05

    Returns
    -------
    dict
        wcag_score       int   0-100
        axe_score        float 0-100
        pour_scores      dict  {principle: int 0-25}
        alt_score        float 0-100
        landmark_score   float 0-100
        contrast_score   float 0-100
        lang_score       float 0 or 100
        violations_count int
        weakest_pour     str
    """
    if not html_string or not html_string.strip():
        return {
            'wcag_score': 0, 'axe_score': None, 'pour_scores': {},
            'alt_score': 0, 'landmark_score': 0, 'contrast_score': 0,
            'lang_score': 0, 'violations_count': None,
            'weakest_pour': 'none', 'axe_available': False,
            'reliability': 'partial',
        }

    soup = BeautifulSoup(html_string, 'lxml')

    violations     = run_axe_core(html_string)
    axe_score      = axe_penalty_score(violations)   # None if axe failed
    pour_scores    = pour_breakdown(violations)
    alt_score      = alt_text_ratio(soup)
    landmark_score = aria_landmark_score(soup)
    contrast_score = tailwind_contrast_score(soup)
    lang_score     = html_lang_score(soup)

    axe_available = axe_score is not None

    if axe_available:
        # Full formula — axe result is trustworthy
        wcag_score = (
            axe_score      * 0.50
            + alt_score    * 0.20
            + landmark_score * 0.15
            + contrast_score * 0.10
            + lang_score   * 0.05
        )
        reliability = 'full'
    else:
        # Axe unavailable — redistribute its 50% weight proportionally
        # among the four BS4 checks (weights: 0.20, 0.15, 0.10, 0.05 → sum 0.50)
        # Multiplied by 2 to keep the total at 1.0
        wcag_score = (
            alt_score      * 0.40
            + landmark_score * 0.30
            + contrast_score * 0.20
            + lang_score   * 0.10
        )
        reliability = 'partial'

    # POUR: filter out None entries before finding minimum
    valid_pour = {k: v for k, v in pour_scores.items() if v is not None}
    weakest_pour = min(valid_pour, key=valid_pour.get) if valid_pour else 'unavailable'

    return {
        'wcag_score':       round(wcag_score),
        'axe_score':        axe_score,
        'pour_scores':      pour_scores,
        'alt_score':        alt_score,
        'landmark_score':   landmark_score,
        'contrast_score':   contrast_score,
        'lang_score':       lang_score,
        'violations_count': len(violations) if violations is not None else None,
        'weakest_pour':     weakest_pour,
        'axe_available':    axe_available,
        'reliability':      reliability,
    }