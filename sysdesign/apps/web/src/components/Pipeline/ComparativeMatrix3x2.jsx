import React from "react";
import {
  Award,
  Cpu,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  ChevronRight,
  TrendingUp,
  BarChart2
} from "lucide-react";

/**
 * Returns human-friendly provider name and model info
 */
function getModelMeta(modelStr = "") {
  const lower = modelStr.toLowerCase();
  if (lower.includes("gpt") || lower.includes("openai")) {
    return {
      title: "OpenAI GPT-4o-mini",
      badge: "Commercial Baseline",
      accent: "#22d3ee",
      color: "border-cyan-400/40 bg-cyan-500/10 text-cyan-300",
      description: "Proprietary commercial reference architecture. Fast token throughput and high API contract precision."
    };
  }
  if (lower.includes("qwen")) {
    return {
      title: "Qwen 2.5 Coder 32B",
      badge: "Open-Weight Code LLM",
      accent: "#a78bfa",
      color: "border-violet-400/40 bg-violet-500/10 text-violet-300",
      description: "Specialized code synthesis model. Excels at REST/gRPC boundary modeling and component modularity."
    };
  }
  if (lower.includes("deepseek")) {
    return {
      title: "DeepSeek V3",
      badge: "Open-Weight MoE Baseline",
      accent: "#34d399",
      color: "border-emerald-400/40 bg-emerald-500/10 text-emerald-300",
      description: "Mixture-of-Experts architecture. Strong multi-layer structural reasoning and decoupled domain boundaries."
    };
  }
  if (lower.includes("llama")) {
    return {
      title: "Meta Llama 3.3 70B",
      badge: "Open Foundation Model",
      accent: "#3b82f6",
      color: "border-blue-400/40 bg-blue-500/10 text-blue-300",
      description: "High-capacity open-weight foundation model. Broad architectural pattern generalizability."
    };
  }
  return {
    title: modelStr.split("/").pop() || modelStr,
    badge: "LLM Model",
    accent: "#94a3b8",
    color: "border-white/20 bg-white/5 text-white/80",
    description: "Evaluated architecture model."
  };
}

export default function ComparativeMatrix3x2({
  candidates = [],
  selectedCandidate,
  onSelectCandidate,
  onInspectMetric
}) {
  // Target 3 research models
  const TARGET_MODELS = [
    { key: "gpt-4o-mini", match: "gpt" },
    { key: "qwen-2.5", match: "qwen" },
    { key: "deepseek", match: "deepseek" },
  ];

  // Group candidates into { modelKey: { primary: c1, alternative: c2 } }
  const matchedCandidateUids = new Set();
  const matrixData = TARGET_MODELS.map((target) => {
    const modelCandidates = candidates.filter((c) =>
      (c.model || "").toLowerCase().includes(target.match)
    );

    modelCandidates.forEach(c => matchedCandidateUids.add(c.uid || `${c.model}::${c.candidate_num}`));

    // Primary is candidate_num 1 (or first); Alternative is candidate_num 2 (or second)
    const primary =
      modelCandidates.find((c) => c.candidate_num === 1) || modelCandidates[0] || null;
    const alternative =
      modelCandidates.find((c) => c.candidate_num === 2) ||
      (modelCandidates.length > 1 && modelCandidates[1] !== primary ? modelCandidates[1] : null);

    const sampleModelName =
      (primary && primary.model) || (alternative && alternative.model) || target.match;

    return {
      targetKey: target.key,
      meta: getModelMeta(sampleModelName),
      primary,
      alternative,
    };
  });

  // Also include any leftover models present in candidates (e.g., custom model or fallback)
  const leftoverCandidates = candidates.filter(
    (c) => !matchedCandidateUids.has(c.uid || `${c.model}::${c.candidate_num}`)
  );
  if (leftoverCandidates.length > 0) {
    const leftoversByModel = {};
    leftoverCandidates.forEach((c) => {
      const m = c.model || "Custom Model";
      if (!leftoversByModel[m]) leftoversByModel[m] = [];
      leftoversByModel[m].push(c);
    });

    Object.entries(leftoversByModel).forEach(([modelName, list]) => {
      const primary = list.find((c) => c.candidate_num === 1) || list[0] || null;
      const alternative = list.find((c) => c.candidate_num === 2) || (list.length > 1 && list[1] !== primary ? list[1] : null);
      matrixData.push({
        targetKey: modelName,
        meta: getModelMeta(modelName),
        primary,
        alternative,
      });
    });
  }

  // Only display rows that have actual candidate outputs (avoids empty ghost placeholders when specific models weren't run)
  const activeRows = matrixData.filter(row => row.primary || row.alternative);
  const displayRows = activeRows.length > 0 ? activeRows : matrixData;

  const renderCandidateCard = (c, isPrimary, meta) => {
    if (!c) {
      return (
        <div className="h-full rounded-xl border border-dashed border-white/10 bg-white/[0.01] p-4 flex flex-col items-center justify-center text-center space-y-2 text-white/30 text-xs">
          <Layers size={20} className="text-white/20" />
          <span>{isPrimary ? "Primary Candidate" : "Alternative Trade-off Candidate"}</span>
          <span className="text-[10px] text-white/20 font-mono">
            {isPrimary ? "Awaiting model synthesis..." : "Run with 2 variations per model"}
          </span>
        </div>
      );
    }

    const isSelected =
      selectedCandidate &&
      selectedCandidate.model === c.model &&
      (selectedCandidate.candidate_num ?? 1) === (c.candidate_num ?? 1);

    const scores = c.scores || {};
    const cas = typeof scores.CAS === "number" ? scores.CAS : (c.cas ?? 0);
    const style = c.style || scores.detected_style || c.architecture?.architecture_style || "Layered";
    const compCount = c.architecture?.components?.length || 0;
    const isWinner = c.rank === 1;

    return (
      <div
        onClick={() => onSelectCandidate(c)}
        className={`
          relative rounded-xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between border
          ${
            isSelected
              ? "border-cyan-400 bg-cyan-950/40 shadow-[0_0_25px_rgba(34,211,238,0.25)] ring-1 ring-cyan-400"
              : isWinner
              ? "border-amber-400/40 bg-amber-950/15 hover:border-amber-400/70 hover:bg-amber-950/25"
              : "border-white/10 bg-black/40 hover:border-white/25 hover:bg-black/60"
          }
        `}
      >
        <div>
          {/* Header Pill */}
          <div className="flex items-center justify-between gap-2 mb-2">
            <span
              className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-md font-bold ${
                isPrimary
                  ? "bg-cyan-500/15 border border-cyan-400/30 text-cyan-300"
                  : "bg-purple-500/15 border border-purple-400/30 text-purple-300"
              }`}
            >
              {isPrimary ? "★ Primary Candidate" : "⇄ Alternative Trade-off"}
            </span>

            {isWinner && (
              <span className="flex items-center gap-1 text-[10px] font-mono uppercase bg-amber-400 text-black font-extrabold px-2 py-0.5 rounded-full shadow-[0_0_10px_rgba(251,191,36,0.4)]">
                <Award size={11} /> Top Rank #1
              </span>
            )}
          </div>

          {/* Style Title & CAS Score */}
          <div className="flex items-start justify-between gap-3 mt-1">
            <div>
              <h4 className="text-sm font-bold text-white tracking-wide font-sans">
                {style}
              </h4>
              <p className="text-[10px] font-mono text-white/50 mt-0.5">
                {compCount} components · {c.architecture?.connectors?.length || 0} connectors
              </p>
            </div>

            <div className="text-right shrink-0">
              <span className="text-[9px] uppercase font-mono text-white/40 block">CAS Utility</span>
              <span className={`text-base font-mono font-bold ${cas >= 0.70 ? "text-green-400" : cas >= 0.60 ? "text-amber-300" : "text-red-400"}`}>
                {cas.toFixed(3)}
              </span>
            </div>
          </div>

          {/* ATAM 4-Metric Grid */}
          <div className="grid grid-cols-4 gap-1.5 mt-3 pt-2.5 border-t border-white/5 text-[10px] font-mono text-center">
            <div
              onClick={(e) => { e.stopPropagation(); onInspectMetric?.("RTS", c); }}
              className="p-1 rounded bg-white/5 hover:bg-cyan-500/20 hover:text-cyan-300 transition-colors cursor-pointer"
              title="Click to inspect RTS Evidence"
            >
              <span className="text-white/40 block text-[8px]">RTS</span>
              <span className="font-bold text-white/90">{(scores.RTS ?? 0).toFixed(2)}</span>
            </div>
            <div
              onClick={(e) => { e.stopPropagation(); onInspectMetric?.("QAC", c); }}
              className="p-1 rounded bg-white/5 hover:bg-cyan-500/20 hover:text-cyan-300 transition-colors cursor-pointer"
              title="Click to inspect QAC Evidence"
            >
              <span className="text-white/40 block text-[8px]">QAC</span>
              <span className="font-bold text-white/90">{(scores.QAC ?? 0).toFixed(2)}</span>
            </div>
            <div
              onClick={(e) => { e.stopPropagation(); onInspectMetric?.("CI", c); }}
              className="p-1 rounded bg-white/5 hover:bg-cyan-500/20 hover:text-cyan-300 transition-colors cursor-pointer"
              title="Click to inspect CI Graph Density"
            >
              <span className="text-white/40 block text-[8px]">CI</span>
              <span className="font-bold text-white/90">{(scores.CI ?? 0).toFixed(2)}</span>
            </div>
            <div
              onClick={(e) => { e.stopPropagation(); onInspectMetric?.("CoS", c); }}
              className="p-1 rounded bg-white/5 hover:bg-cyan-500/20 hover:text-cyan-300 transition-colors cursor-pointer"
              title="Click to inspect CoS Cohesion"
            >
              <span className="text-white/40 block text-[8px]">CoS</span>
              <span className="font-bold text-white/90">{(scores.CoS ?? 0).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Card Footer */}
        <div className="flex items-center justify-between pt-2.5 mt-2 border-t border-white/5 text-[10px]">
          <span className="flex items-center gap-1 text-emerald-400 font-mono">
            <ShieldCheck size={11} /> S-SDLC Verified
          </span>

          <span className={`text-[10px] font-semibold flex items-center gap-1 ${isSelected ? "text-cyan-300 font-bold" : "text-white/50"}`}>
            {isSelected ? "Active View" : "Select Architecture"} <ChevronRight size={12} />
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Table Header: Column Labels */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3 px-2 text-xs font-mono uppercase tracking-wider text-white/50">
        <div className="md:col-span-3">LLM Model Under Evaluation</div>
        <div className="md:col-span-4 flex items-center gap-1.5 text-cyan-400 font-bold">
          <span>Column 1: Primary Best-Fit Synthesis</span>
        </div>
        <div className="md:col-span-5 flex items-center gap-1.5 text-purple-400 font-bold">
          <span>Column 2: Alternative Trade-off Variation</span>
        </div>
      </div>

      {/* Comparative Model Rows */}
      {displayRows.map((row) => (
        <div
          key={row.targetKey}
          className="rounded-2xl border border-white/10 bg-[#070b13]/85 backdrop-blur-xl p-4 shadow-lg"
        >
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-stretch">
            
            {/* Model Profile (Left Column) */}
            <div className="md:col-span-3 flex flex-col justify-between pr-2 border-b md:border-b-0 md:border-r border-white/10 pb-3 md:pb-0">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <div className={`p-1.5 rounded-lg border text-xs font-bold font-mono ${row.meta.color}`}>
                    <Cpu size={14} />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white font-sans">
                      {row.meta.title}
                    </h3>
                    <span className="text-[10px] font-mono text-white/40 block">
                      {row.meta.badge}
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-white/60 leading-relaxed font-sans mt-2">
                  {row.meta.description}
                </p>
              </div>

              <div className="pt-3 mt-3 border-t border-white/5 text-[10px] font-mono text-white/40">
                AHP Evaluator: 0% LLM Bias
              </div>
            </div>

            {/* Candidate 1: Primary (Middle Column) */}
            <div className="md:col-span-4 flex flex-col">
              {renderCandidateCard(row.primary, true, row.meta)}
            </div>

            {/* Candidate 2: Alternative (Right Column) */}
            <div className="md:col-span-5 flex flex-col">
              {renderCandidateCard(row.alternative, false, row.meta)}
            </div>

          </div>
        </div>
      ))}
    </div>
  );
}
