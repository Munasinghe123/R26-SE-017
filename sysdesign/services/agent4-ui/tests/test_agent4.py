import os
from bs4 import BeautifulSoup

from evaluator.composite_scorer import evaluate
from evaluator.nielsen_metrics import user_control_score
from generator.traceability import build_traceability_matrix
from screen_planner import _recover_truncated_json, _canon_fr_id
import generator.refinement_controller as rc

BASE = os.path.dirname(os.path.dirname(__file__))


def _read(name):
    with open(os.path.join(BASE, "samples", name), encoding="utf-8") as f:
        return f.read()


def test_good_ui_scores_higher_than_bad_ui():
    good = evaluate(_read("good_ui.html"))
    bad = evaluate(_read("bad_ui.html"))
    print("GOOD:", good["total_score"], "BAD:", bad["total_score"])
    assert good["total_score"] > bad["total_score"] + 20


def test_user_control_counts_controls_not_ancestors():
    one = BeautifulSoup("<div><form><button>Cancel</button></form></div>", "lxml")
    none = BeautifulSoup("<div><h2>Welcome back</h2></div>", "lxml")
    assert user_control_score(one) == 2
    assert user_control_score(none) == 0


def test_fr_id_canonicalisation():
    assert _canon_fr_id("FR-1") == _canon_fr_id("FR01") == "fr1"
    assert _canon_fr_id("FR10") == "fr10"


def test_traceability_matches_across_id_formats():
    html = '<html><body><button data-fr="FR-1">Log in</button></body></html>'
    res = build_traceability_matrix(html, [{"id": "FR01", "title": "Login"}])
    assert res["coverage_pct"] == 100.0


def test_json_repair_salvages_truncated_array():
    raw = '[{"screen_id":"a","screen_name":"A"},{"screen_id":"b","screen_na'
    out = _recover_truncated_json(raw)
    assert '"screen_id": "a"' in out


def _report(total, uc=0):
    return {
        "total_score": total, "threshold": 85,
        "iso_score": 90, "nielsen_score": 60, "wcag_score": 90,
        "iso_details": {"sub_scores": {}},
        "nielsen_details": {"sub_scores": {"user_control": uc}},
        "wcag_details": {"weakest_pour": "Perceivable"},
        "weakest_standard": "Nielsen", "weakest_metric": "user_control",
    }


def test_rollback_returns_best_iteration(monkeypatch):
    scores = {"h1": 70, "h2": 60, "h3": 60, "h4": 60, "h5": 60}
    monkeypatch.setattr(rc, "evaluate", lambda html, iteration_number=1: _report(scores[html]))
    nxt = iter(["h2", "h3", "h4", "h5"])
    monkeypatch.setattr(rc, "refine_ui", lambda *a, **k: next(nxt))
    res = rc.run_refinement_loop({}, "form", initial_html="h1")
    assert res["final_html"] == "h1" and res["regressed"] is True


def test_stall_escalation_note_added(monkeypatch):
    monkeypatch.setattr(rc, "evaluate", lambda html, iteration_number=1: _report(60, uc=0))
    seen = []
    def fake_refine(html, req, st, instr):
        seen.append(instr)
        return "x"
    monkeypatch.setattr(rc, "refine_ui", fake_refine)
    rc.run_refinement_loop({}, "form", initial_html="x", max_iterations=3)
    assert "did not" in seen[1] and "did not" not in seen[0]