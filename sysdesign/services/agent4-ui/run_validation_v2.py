"""
run_validation_v2.py  (put next to run_validation.py in backend/)
Usage:  python run_validation_v2.py
        python run_validation_v2.py --resume          # skip scenarios already finished
        python run_validation_v2.py --only S1,S3

Improvements over run_validation.py
- Retries generation until the HTML is complete (not cut off by max_tokens)
- One failing scenario no longer kills the whole run; errors are recorded
- Saves progress after every scenario (--resume)
- Fixed T2: only scenarios that needed refinement are counted, and the
  per-iteration improvement is relative % (first-pass passes no longer count as 0)
- Records final weakest metric + html_complete so failures can be diagnosed
- Saves baseline + final HTML and makes a BLIND, shuffled copy for the expert
  ratings (outputs/validation_html/blind/ + blind_key.csv)
- Writes results_validation.csv, results_targets.csv directly
"""
import argparse, csv, json, os, random, shutil, statistics, time, traceback
from datetime import datetime

from run_validation import SCENARIOS            # reuse the 5 scenarios
from generator.ui_generator import generate_ui
from generator.refinement_controller import run_refinement_loop
from evaluator.composite_scorer import evaluate
import generator.refinement_controller as rc

# ---------------------------------------------------------------------------
# 402 in-flight budget retry wrapper
# OpenRouter reserves credit upfront per request; refinement loops exhaust
# this quickly. Waiting 125 s lets the reserve expire and works for free.
# ---------------------------------------------------------------------------
def _retry(fn):
    def wrapped(*a, **k):
        for i in range(4):
            try:
                return fn(*a, **k)
            except Exception as e:
                if "402" in str(e) and i < 3:
                    print(f"   402 in-flight budget, waiting 125s... (attempt {i+1}/3)")
                    time.sleep(125)
                    continue
                raise
    return wrapped

rc.refine_ui   = _retry(rc.refine_ui)   if hasattr(rc, "refine_ui")   else rc.refine_ui
rc.generate_ui = _retry(rc.generate_ui) if hasattr(rc, "generate_ui") else rc.generate_ui
generate_ui    = _retry(generate_ui)

OUT = os.path.join(os.path.dirname(__file__), "outputs")
HTML_DIR = os.path.join(OUT, "validation_html")
PARTIAL = os.path.join(OUT, "validation_partial.json")
TARGET = 85


def html_ok(h):
    return bool(h) and "</html>" in h.lower() and "</body>" in h.lower() and len(h) > 1500


def generate_complete(req, screen_type, tries=3):
    last = ""
    for i in range(1, tries + 1):
        try:
            last = generate_ui(req, screen_type)
            if html_ok(last):
                return last, i
            print(f"   generation attempt {i}: incomplete HTML ({len(last)} chars), retrying")
        except Exception as e:
            print(f"   generation attempt {i} failed: {e}")
            time.sleep(3)
    if not last:
        raise RuntimeError("generation failed on all attempts")
    return last, tries


def run_scenario(sc):
    req, st = sc["requirements"], sc["screen_type"]
    row = {"scenario_id": sc["scenario_id"], "screen_type": st, "screen_id": req["screen_id"], "error": ""}
    try:
        base_html, attempts = generate_complete(req, st)
        base = evaluate(base_html, iteration_number=1)
        row["attempts"] = attempts
        row["baseline_complete_html"] = html_ok(base_html)
        row["baseline_score"] = base["total_score"]
        row["weakest_standard_baseline"] = base["weakest_standard"]
        row["weakest_metric_baseline"] = base["weakest_metric"]
        os.makedirs(HTML_DIR, exist_ok=True)
        open(os.path.join(HTML_DIR, f"{sc['scenario_id']}_baseline.html"), "w", encoding="utf-8").write(base_html)

        res = run_refinement_loop(req, st, initial_html=base_html)
        scores = [e["report"]["total_score"] for e in res["history"]]
        fin = res["final_report"]
        open(os.path.join(HTML_DIR, f"{sc['scenario_id']}_final.html"), "w", encoding="utf-8").write(res["final_html"])

        rel = [(scores[i] - scores[i - 1]) / scores[i - 1] * 100 for i in range(1, len(scores)) if scores[i - 1] > 0]
        row.update({
            "final_score": fin["total_score"],
            "score_delta": fin["total_score"] - base["total_score"],
            "iterations_to_converge": res["iterations"],
            "converged_ge_85": fin["total_score"] >= TARGET,
            "converged_within_5": fin["total_score"] >= TARGET and res["iterations"] <= 5,
            "regressed": res["regressed"],
            "final_iso": fin["iso_score"], "final_nielsen": fin["nielsen_score"], "final_wcag": fin["wcag_score"],
            "final_weakest_standard": fin["weakest_standard"], "final_weakest_metric": fin["weakest_metric"],
            "final_complete_html": html_ok(res["final_html"]),
            "mean_rel_improvement_pct": round(statistics.mean(rel), 2) if rel else "",
            "refined": res["iterations"] > 1,
        })
        for i in range(5):
            row[f"iter{i+1}_score"] = scores[i] if i < len(scores) else ""
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    return row


COLS = ["scenario_id", "screen_type", "screen_id", "baseline_score", "final_score", "score_delta",
        "iterations_to_converge", "converged_ge_85", "converged_within_5", "regressed",
        "iter1_score", "iter2_score", "iter3_score", "iter4_score", "iter5_score",
        "final_iso", "final_nielsen", "final_wcag", "weakest_standard_baseline", "weakest_metric_baseline",
        "final_weakest_standard", "final_weakest_metric", "baseline_complete_html", "final_complete_html",
        "attempts", "mean_rel_improvement_pct", "refined", "error"]

FORMATTED_COLS = [
    "Scenario",
    "Screen Type",
    "Screen ID",
    "Baseline Score",
    "Final Score",
    "Score Delta",
    "Convergence Status",
    "Score Progression",
    "Rounds to Converge",
    "Final ISO (30%)",
    "Final Nielsen (30%)",
    "Final WCAG (40%)",
    "Relative Gain (%)",
    "Baseline Weakest",
    "Final Weakest",
    "HTML Integrity",
    "Error"
]


def format_row(r):
    delta = r.get("score_delta", "")
    if isinstance(delta, (int, float)):
        delta_str = f"+{delta} pts" if delta > 0 else f"{delta} pts"
    elif delta not in ("", None):
        try:
            d_val = float(delta)
            delta_str = f"+{int(d_val)} pts" if d_val > 0 else f"{int(d_val)} pts"
        except Exception:
            delta_str = str(delta)
    else:
        delta_str = "—"

    # Score progression trajectory across iterations
    prog = [r.get(f"iter{i+1}_score") for i in range(5) if r.get(f"iter{i+1}_score") not in ("", None)]
    prog_str = " -> ".join(map(str, prog)) if prog else (str(r.get("baseline_score", "")) or "—")

    # Human-readable convergence status
    conv = r.get("converged_ge_85")
    is_conv = conv is True or str(conv).strip().lower() == "true"
    iters = r.get("iterations_to_converge", "")
    if is_conv:
        status_str = f"CONVERGED (>=85 in {iters} rds)"
    elif r.get("final_score") not in ("", None):
        status_str = f"STALLED (at {r.get('final_score')}/100)"
    elif r.get("error"):
        status_str = "FAILED (Runtime Error)"
    else:
        status_str = "PENDING"

    # Relative improvement formatting
    rel = r.get("mean_rel_improvement_pct", "")
    if isinstance(rel, (int, float)):
        rel_str = f"+{rel:.2f}%" if rel > 0 else f"{rel:.2f}%"
    elif rel not in ("", None):
        try:
            r_val = float(rel)
            rel_str = f"+{r_val:.2f}%" if r_val > 0 else f"{r_val:.2f}%"
        except Exception:
            rel_str = str(rel)
    else:
        rel_str = "—"

    # HTML integrity
    html_ok = r.get("final_complete_html")
    is_html_ok = html_ok is True or str(html_ok).strip().lower() == "true"
    html_str = "Complete" if is_html_ok else ("Truncated" if r.get("final_score") else "—")

    b_weak = f"{r.get('weakest_standard_baseline','')}: {r.get('weakest_metric_baseline','')}".strip(": ") or "—"
    f_weak = f"{r.get('final_weakest_standard','')}: {r.get('final_weakest_metric','')}".strip(": ") or "—"

    b_score = f"{r.get('baseline_score')}/100" if r.get("baseline_score") not in ("", None) else "—"
    f_score = f"{r.get('final_score')}/100" if r.get("final_score") not in ("", None) else "—"
    iso_score = f"{r.get('final_iso')}/100" if r.get("final_iso") not in ("", None) else "—"
    nielsen_score = f"{r.get('final_nielsen')}/100" if r.get("final_nielsen") not in ("", None) else "—"
    wcag_score = f"{r.get('final_wcag')}/100" if r.get("final_wcag") not in ("", None) else "—"

    return {
        "Scenario": r.get("scenario_id", ""),
        "Screen Type": str(r.get("screen_type", "")).capitalize(),
        "Screen ID": r.get("screen_id", ""),
        "Baseline Score": b_score,
        "Final Score": f_score,
        "Score Delta": delta_str,
        "Convergence Status": status_str,
        "Score Progression": prog_str,
        "Rounds to Converge": f"{iters} rounds" if iters not in ("", None) else "—",
        "Final ISO (30%)": iso_score,
        "Final Nielsen (30%)": nielsen_score,
        "Final WCAG (40%)": wcag_score,
        "Relative Gain (%)": rel_str,
        "Baseline Weakest": b_weak,
        "Final Weakest": f_weak,
        "HTML Integrity": html_str,
        "Error": r.get("error", "") or "None",
    }


def write_csv(rows):
    formatted = [format_row(r) for r in rows]

    # 1. Primary human-readable formatted CSV
    with open("results_validation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FORMATTED_COLS)
        w.writeheader()
        w.writerows(formatted)

    # 2. Raw programmatic backup CSV
    with open("results_validation_raw.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # 3. Clean Markdown summary table for instant reading in preview
    with open("results_validation.md", "w", encoding="utf-8") as f:
        f.write("# Usability Validation & Convergence Report\n\n")
        f.write("| " + " | ".join(FORMATTED_COLS) + " |\n")
        f.write("| " + " | ".join(["---"] * len(FORMATTED_COLS)) + " |\n")
        for row in formatted:
            f.write("| " + " | ".join(str(row[c]) for c in FORMATTED_COLS) + " |\n")


def summarise(rows):
    ok = [r for r in rows if not r.get("error")]
    finals = [float(r["final_score"]) for r in ok if r.get("final_score") not in ("", None)]
    refined = [r for r in ok if r.get("refined") and r.get("mean_rel_improvement_pct") not in ("", None)]
    
    t1 = statistics.mean(finals) if finals else 0.0
    t2_vals = [float(r["mean_rel_improvement_pct"]) for r in refined]
    t2 = statistics.mean(t2_vals) if t2_vals else None
    
    deltas = [float(r["score_delta"]) for r in ok if r.get("refined") and r.get("score_delta") not in ("", None)]
    gain = statistics.mean(deltas) if deltas else None
    
    conv_count = sum(1 for r in ok if r.get("converged_within_5") is True or str(r.get("converged_within_5")).lower() == "true")
    t3 = (conv_count / len(rows) * 100.0) if rows else 0.0

    targets = [
        ["T1", "Mean final composite score (ISO 30% + Nielsen 30% + WCAG 40%)", ">=85",
         f"{t1:.2f} / 100", "PASS" if t1 >= 85 else "FAIL"],
        ["T2", "Mean relative improvement per refinement iteration (refined scenarios only)", ">10%",
         "N/A" if t2 is None else f"+{t2:.2f}%", "N/A" if t2 is None else ("PASS" if t2 > 10 else "FAIL")],
        ["T2b", "Mean score gain baseline -> final (refined scenarios)", "info",
         "N/A" if gain is None else f"+{gain:.2f} points", "Informational"],
        ["T3", "Convergence within 5 iterations (all scenarios; errors count as failures)", ">90%",
         f"{t3:.1f}% ({conv_count} of {len(rows)} converged)", "PASS" if t3 > 90 else f"FAIL ({conv_count} of {len(rows)} converged)"],
    ]

    with open("results_targets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Target", "Evaluation Metric", "Threshold", "Measured Value", "Result"])
        w.writerows(targets)

    return targets


def make_blind_set(rows):
    items = []
    for r in rows:
        for v in ("baseline", "final"):
            p = os.path.join(HTML_DIR, f"{r['scenario_id']}_{v}.html")
            if os.path.exists(p):
                items.append((r["scenario_id"], v, p))
    random.Random(42).shuffle(items)
    bdir = os.path.join(HTML_DIR, "blind")
    shutil.rmtree(bdir, ignore_errors=True)
    os.makedirs(bdir)
    with open(os.path.join(HTML_DIR, "blind_key.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["screen_label", "scenario_id", "version"])
        for i, (sid, v, p) in enumerate(items, 1):
            label = f"screen_{i:02d}"
            shutil.copy(p, os.path.join(bdir, label + ".html"))
            w.writerow([label, sid, v])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    done = {}
    if a.resume and os.path.exists(PARTIAL):
        done = {r["scenario_id"]: r for r in json.load(open(PARTIAL, encoding="utf-8")) if not r["error"]}
    only = set(filter(None, a.only.split(",")))
    rows = []
    for sc in SCENARIOS:
        sid = sc["scenario_id"]
        if only and sid not in only:
            continue
        if sid in done:
            print(f"{sid}: reusing saved result"); rows.append(done[sid]); continue
        print(f"--- {sid} ({sc['screen_type']}) ---")
        r = run_scenario(sc)
        print(f"   baseline={r.get('baseline_score')} final={r.get('final_score')} iters={r.get('iterations_to_converge')} err={r['error']}")
        rows.append(r)
        json.dump(rows, open(PARTIAL, "w", encoding="utf-8"), indent=2, default=str)
        write_csv(rows)
    targets = summarise(rows)
    make_blind_set(rows)
    json.dump({"run_at": datetime.now().isoformat(), "targets": targets, "results": rows},
              open(os.path.join(OUT, "validation_report.json"), "w", encoding="utf-8"), indent=2, default=str)
    print("\n".join(" | ".join(map(str, t)) for t in targets))
    print("Wrote results_validation.csv, results_targets.csv, outputs/validation_html/blind/ (+blind_key.csv)")
