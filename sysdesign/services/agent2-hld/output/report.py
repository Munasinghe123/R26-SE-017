"""
HLA Agent — Evaluation Report Generator
Produces a professional Markdown report with ranked tables,
winner analysis, and per-metric explanations.
"""

from datetime import datetime


def generate_report(ranked_candidates: list, requirements: dict,
                    run_id: str = "", diagram_meta: dict | None = None) -> str:
    """
    Generate a full Markdown evaluation report.

    Args:
        ranked_candidates: Sorted list from rank_candidates()
        requirements: Original requirements dict
        run_id: Optional run identifier

    Returns:
        Complete Markdown report string
    """
    project = requirements.get("project", "Unknown Project")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append(f"# HLA Agent — Architecture Evaluation Report")
    lines.append(f"")
    lines.append(f"**Project:** {project}  ")
    lines.append(f"**Generated:** {timestamp}  ")
    if run_id:
        lines.append(f"**Run ID:** {run_id}  ")
    lines.append(f"**Candidates Evaluated:** {len(ranked_candidates)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === Ranking Table ===
    lines.append("## 📊 Candidate Rankings")
    lines.append("")
    lines.append("| Rank | Model | Declared Style | Detected Style | RTS | QAC | CI | CoS | SSM₁ | SSM₂ | **CAS** | Verdict |")
    lines.append("|------|-------|----------------|----------------|-----|-----|----|-----|------|------|---------|---------|")

    for c in ranked_candidates:
        s = c.get("scores", {})
        arch = c.get("architecture", {})
        verdict_icon = {"Accepted": "✅", "Marginal": "⚠️", "Poor": "❌"}.get(
            s.get("verdict", ""), "❓"
        )
        lines.append(
            f"| {c.get('rank', '?')} | {c['model']} | {arch.get('architecture_style', 'N/A')} "
            f"| {s.get('detected_style', 'N/A')} "
            f"| {s.get('RTS', 0):.2f} | {s.get('QAC', 0):.2f} | {s.get('CI', 0):.2f} "
            f"| {s.get('CoS', 0):.2f} | {s.get('SSM1', 0):.2f} | {s.get('SSM2', 0):.2f} "
            f"| **{s.get('CAS', 0):.4f}** | {verdict_icon} {s.get('verdict', '')} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # === Winner Analysis ===
    if ranked_candidates:
        winner = ranked_candidates[0]
        ws = winner.get("scores", {})
        wa = winner.get("architecture", {})

        lines.append("## 🏆 Winner Analysis")
        lines.append("")
        lines.append(f"- **Model:** {winner['model']}")
        lines.append(f"- **Declared Style:** {wa.get('architecture_style', 'N/A')}")
        lines.append(f"- **Detected Style:** {ws.get('detected_style', 'N/A')}")
        lines.append(f"- **CAS Score:** {ws.get('CAS', 0):.4f}")
        lines.append(f"- **Verdict:** {ws.get('verdict', 'N/A')}")
        lines.append(f"- **Components:** {len(wa.get('components', []))}")
        lines.append(f"- **Connectors:** {len(wa.get('connectors', []) or wa.get('interactions', []))}")
        lines.append(f"- **Layers:** {len(wa.get('layers', []))}")
        lines.append("")

        # Component list
        lines.append("### Components")
        lines.append("")
        lines.append("| Component | Layer | Responsibilities |")
        lines.append("|-----------|-------|------------------|")
        for comp in wa.get("components", []):
            resps = comp.get("responsibilities", [])
            if not resps and comp.get("responsibility"):
                resps = [comp["responsibility"]]
            resp_str = "; ".join(resps) if isinstance(resps, list) else str(resps)
            lines.append(
                f"| {comp.get('name', '')} | {comp.get('layer', comp.get('boundary', ''))} "
                f"| {resp_str} |"
            )
        lines.append("")

    # === Diagram Evidence (optional) ===
    if diagram_meta and diagram_meta.get("diagram_workflow"):
        wf = diagram_meta.get("diagram_workflow") or {}
        pu = (wf.get("plantuml") or {})
        mm = (wf.get("mermaid") or {})
        cur = (pu.get("current") or {})

        lines.append("---")
        lines.append("")
        lines.append("## 🧩 Diagram Workflow (Manual PlantUML → Approve → Mermaid)")
        lines.append("")
        lines.append(f"- **PlantUML Approved:** {str(bool(pu.get('approved')))}")
        lines.append(f"- **LLM Iterations Used:** {pu.get('llm_iterations_used', 'N/A')} / {pu.get('max_llm_iterations', 'N/A')}")
        if cur:
            lines.append(f"- **Current PlantUML Diagram_CAS:** {cur.get('diagram_cas', 0):.4f}")
            b = (cur.get("breakdown") or {})
            lines.append(
                f"- **PlantUML Breakdown:** syntax_ok={b.get('syntax_ok', False)} | "
                f"component_cov={b.get('component_coverage', 0):.4f} | "
                f"interaction_cov={b.get('interaction_coverage', 0):.4f} | "
                f"style_align={b.get('style_alignment', 0):.4f}"
            )
        lines.append("")

        if not bool(mm.get("generated")):
            lines.append("- **Mermaid:** Pending (generated only after PlantUML approval)")
        else:
            mcur = (mm.get("current") or {})
            lines.append(f"- **Mermaid Generated:** True (Diagram_CAS={mcur.get('diagram_cas', 0):.4f})")
        lines.append("")

    elif diagram_meta:
        lines.append("---")
        lines.append("")
        lines.append("## 🧩 Diagram Generation (LLM, max 2 iterations)")
        lines.append("")
        lines.append(
            "This section reports *diagram* iteration quality signals. "
            "`Diagram_CAS` is a deterministic proxy score (coverage + style-alignment + syntax), "
            "and is separate from the architecture CAS."
        )
        lines.append("")

        for kind in ["mermaid", "plantuml"]:
            if kind not in diagram_meta:
                continue

            info = diagram_meta.get(kind, {}) or {}
            final = info.get("final", {}) or {}
            attempts = info.get("attempts", []) or []

            lines.append(f"### {kind.title()}")
            lines.append("")
            lines.append(f"- **Model:** {info.get('model', 'N/A')}")
            lines.append(f"- **Provider:** {info.get('provider', 'N/A')}")
            lines.append(f"- **Final Diagram_CAS:** {final.get('diagram_cas', 0):.4f}")
            lines.append("")

            if attempts:
                lines.append("| Iteration | Diagram_CAS | Syntax OK | Component Cov | Interaction Cov | Style Align |")
                lines.append("|-----------|------------|-----------|---------------|----------------|-------------|")
                for a in attempts:
                    b = (a.get("breakdown", {}) or {})
                    lines.append(
                        f"| {a.get('iteration', '?')} | {a.get('diagram_cas', 0):.4f} "
                        f"| {str(b.get('syntax_ok', False))} "
                        f"| {b.get('component_coverage', 0):.4f} "
                        f"| {b.get('interaction_coverage', 0):.4f} "
                        f"| {b.get('style_alignment', 0):.4f} |"
                    )
                lines.append("")

            diff_text = (info.get("diff", "") or "").strip("\n")
            if diff_text:
                lines.append(f"#### {kind.title()} — Iteration Diff (v1 → v2)")
                lines.append("")
                lines.append("```diff")
                lines.append(diff_text)
                lines.append("```")
                lines.append("")

    # === Metric Details ===
    lines.append("---")
    lines.append("")
    lines.append("## 📈 Metric Definitions (Style-Aware 6-Metric Framework)")
    lines.append("")
    lines.append("| Metric | Full Name | Weight (AHP) | Description / Threshold |")
    lines.append("|--------|-----------|--------------|-------------------------|")
    lines.append("| RTS | Requirement Traceability Score | 29.17% | Semantic trace of FRs to components (θ_rts=0.55) |")
    lines.append("| QAC | Quality Attribute Coverage | 21.94% | ISO 25010 NFR provision coverage (θ_qac=0.50) |")
    lines.append("| CI | Coupling Index | 13.61% | Graph decoupling density (higher = better) |")
    lines.append("| CoS | Cohesion Score | 13.61% | Semantic coherence of responsibilities |")
    lines.append("| SSM₁ | Primary Style Metric | 13.61% | LIS, SBA, EFC, MCR, or PC based on detected style |")
    lines.append("| SSM₂ | Secondary Style Metric | 8.06% | DDS, ISS, PSC, or FIS based on detected style |")
    lines.append("")
    lines.append("**CAS Formula:**  ")
    lines.append("$$\\text{CAS} = 0.2917 \\times \\text{RTS} + 0.2194 \\times \\text{QAC} + 0.1361 \\times \\text{CI} + 0.1361 \\times \\text{CoS} + 0.1361 \\times \\text{SSM}_1 + 0.0806 \\times \\text{SSM}_2$$")
    lines.append("")
    lines.append("Architectural styles evaluated: Layered, Microservices, Event-Driven, Modular Monolith (Newman 2019), Pipe-and-Filter.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by HLA Agent v2.0 (Style-Aware Quantitative Evaluation Framework)*")

    return "\n".join(lines)
