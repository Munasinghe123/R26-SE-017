/**
 * DiagramDiffPanel.jsx — git-style revision control for the diagrams of ONE candidate.
 * Uses a real LCS line diff between any two versions (not just v1 vs latest).
 */
import React, { useMemo } from "react";
import { FileDiff, GitCommit } from "lucide-react";
import { lcsDiff, diffStats } from "../../utils/diagramTools";

export function DiffView({ diff, maxHeight = "max-h-[420px]", emptyText = "No differences." }) {
  if (!diff || diff.length === 0) {
    return <div className="text-xs text-white/40 font-mono p-4">{emptyText}</div>;
  }
  const changed = diff.some((d) => d.type !== "same");
  return (
    <div className={`rounded-xl bg-black/90 font-mono text-[11px] overflow-auto ${maxHeight} border border-white/10`}>
      {!changed && <div className="text-xs text-white/40 p-3">Versions are identical.</div>}
      {diff.map((d, idx) => {
        const cls =
          d.type === "add"
            ? "text-green-300 bg-green-950/60"
            : d.type === "del"
            ? "text-red-300 bg-red-950/60"
            : "text-white/55";
        const sign = d.type === "add" ? "+" : d.type === "del" ? "-" : " ";
        return (
          <div key={idx} className={`${cls} flex whitespace-pre leading-relaxed`}>
            <span className="select-none w-9 shrink-0 text-right pr-2 text-white/25 border-r border-white/10">
              {d.oldNo ?? ""}
            </span>
            <span className="select-none w-9 shrink-0 text-right pr-2 text-white/25 border-r border-white/10">
              {d.newNo ?? ""}
            </span>
            <span className="select-none w-5 shrink-0 text-center font-bold">{sign}</span>
            <span className="pr-3">{d.text || " "}</span>
          </div>
        );
      })}
    </div>
  );
}

const SOURCE_BADGE = {
  seed: { label: "CAM", cls: "bg-white/10 text-white/60" },
  llm: { label: "AI", cls: "bg-violet-500/20 text-violet-300" },
  manual: { label: "MANUAL", cls: "bg-amber-500/20 text-amber-300" },
};

export default function DiagramDiffPanel({ candidateName, iterations, diffFrom, diffTo, setDiffFrom, setDiffTo }) {
  const versions = iterations || [];
  const fromV = diffFrom || versions[0]?.version;
  const toV = diffTo || versions[versions.length - 1]?.version;
  const fromIt = versions.find((v) => v.version === fromV);
  const toIt = versions.find((v) => v.version === toV);

  const diff = useMemo(
    () => (fromIt && toIt ? lcsDiff(fromIt.code, toIt.code) : []),
    [fromIt, toIt]
  );
  const stats = diffStats(diff);

  return (
    <div className="rounded-2xl border border-cyan-400/20 bg-[#080818] p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <FileDiff className="text-cyan-400" size={18} />
          <div>
            <h3 className="text-sm font-bold text-cyan-300" style={{ fontFamily: "Orbitron, sans-serif" }}>
              Revision Control &mdash; {fromV || "?"} &rarr; {toV || "?"}
            </h3>
            {candidateName && <p className="text-[10px] text-white/40 font-mono mt-0.5">Candidate: {candidateName}</p>}
          </div>
        </div>
        <div className="flex items-center gap-2 text-[11px] font-mono">
          <span className="px-2 py-0.5 rounded bg-green-500/15 text-green-300">+{stats.added}</span>
          <span className="px-2 py-0.5 rounded bg-red-500/15 text-red-300">-{stats.removed}</span>
        </div>
      </div>

      {versions.length < 2 ? (
        <div className="text-xs text-white/50 p-4 rounded-xl bg-white/5 border border-white/10">
          Only one version exists for this candidate. Edit the PlantUML code or run an AI refinement in the
          <strong className="text-cyan-300"> Interactive Refinement Engine</strong> tab to create a second version.
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
            {[
              ["From", fromV, setDiffFrom],
              ["To", toV, setDiffTo],
            ].map(([label, value, setter]) => (
              <label key={label} className="flex items-center gap-2 text-white/60">
                {label}
                <select
                  value={value || ""}
                  onChange={(e) => setter(e.target.value)}
                  className="bg-black/60 border border-white/15 rounded-lg px-2 py-1 text-cyan-200 outline-none focus:border-cyan-400"
                >
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      {v.version} · {SOURCE_BADGE[v.source]?.label || "CAM"} · CAS{" "}
                      {typeof v.cas === "number" ? v.cas.toFixed(3) : v.cas}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            {versions.map((v) => (
              <div key={v.version} className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded-lg bg-white/5 border border-white/10">
                <GitCommit size={11} className="text-cyan-400" />
                <span className="text-white/80">{v.version}</span>
                <span className={`px-1.5 rounded ${SOURCE_BADGE[v.source]?.cls || SOURCE_BADGE.seed.cls}`}>
                  {SOURCE_BADGE[v.source]?.label || "CAM"}
                </span>
                <span className="text-white/40 max-w-[220px] truncate" title={v.prompt}>
                  {v.prompt}
                </span>
              </div>
            ))}
          </div>

          <DiffView diff={diff} maxHeight="max-h-[520px]" />
        </>
      )}
    </div>
  );
}
