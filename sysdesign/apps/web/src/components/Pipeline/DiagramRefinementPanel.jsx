/**
 * DiagramRefinementPanel.jsx — Interactive Refinement Engine for the SELECTED candidate.
 *
 * Two ways to change a diagram, both producing git-style versions with a live diff:
 *  1. Edit the PlantUML source directly -> "Apply Edit & Rescore"
 *  2. Describe the change in plain language -> "Run AI Refinement"
 */
import React, { useMemo, useRef } from "react";
import { GitBranch, GitCommit, Sparkles, RefreshCw, Save, Undo2, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { lcsDiff, diffStats, normalizeCode } from "../../utils/diagramTools";
import { DiffView } from "./DiagramDiffPanel";

const SOURCE_BADGE = {
  seed: { label: "CAM", cls: "bg-white/10 text-white/60" },
  llm: { label: "AI", cls: "bg-violet-500/20 text-violet-300" },
  manual: { label: "MANUAL", cls: "bg-amber-500/20 text-amber-300" },
};

export default function DiagramRefinementPanel({
  candidateName,
  iterations,
  activeVersion,
  onSelectVersion,
  draftCode,
  setDraftCode,
  onApplyEdit,
  applyingEdit,
  refinePrompt,
  setRefinePrompt,
  onRefine,
  refining,
  notice,
  threshold = 0.75,
}) {
  const gutterRef = useRef(null);
  const versions = iterations || [];
  const activeIdx = Math.max(0, versions.findIndex((v) => v.version === activeVersion));
  const active = versions[activeIdx] || versions[versions.length - 1];
  const activeCode = normalizeCode(active?.code);
  const isDirty = draftCode.trim() !== activeCode.trim();
  const cas = typeof active?.cas === "number" ? active.cas : 0;
  const passed = cas >= threshold;
  const lines = draftCode.split("\n");

  const liveDiff = useMemo(() => {
    if (isDirty) return { label: `Uncommitted changes (${active?.version} → working copy)`, diff: lcsDiff(activeCode, draftCode) };
    if (activeIdx > 0) {
      const prev = versions[activeIdx - 1];
      return { label: `${prev.version} → ${active.version}`, diff: lcsDiff(prev.code, active.code) };
    }
    return { label: "", diff: null };
  }, [isDirty, activeCode, draftCode, activeIdx, versions, active]);
  const stats = liveDiff.diff ? diffStats(liveDiff.diff) : { added: 0, removed: 0 };

  const noticeCls = {
    ok: "border-green-400/30 bg-green-950/30 text-green-300",
    warn: "border-amber-400/30 bg-amber-950/30 text-amber-300",
    error: "border-red-400/30 bg-red-950/30 text-red-300",
  };
  const NoticeIcon = { ok: CheckCircle2, warn: AlertTriangle, error: XCircle };

  return (
    <div className="space-y-6">
      {/* Version timeline */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-2xl bg-white/5 border border-white/10">
        <div className="flex items-center gap-3">
          <GitBranch className="text-cyan-400" size={18} />
          <div>
            <span className="block text-xs font-bold uppercase tracking-wider text-cyan-300" style={{ fontFamily: "Orbitron, sans-serif" }}>
              Diagram Versions (PlantUML)
            </span>
            {candidateName && <span className="text-[10px] text-white/40 font-mono">Candidate: {candidateName}</span>}
          </div>
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {versions.map((it) => (
            <button
              key={it.version}
              onClick={() => onSelectVersion(it.version)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                activeVersion === it.version
                  ? "bg-cyan-400 text-black shadow-[0_0_10px_rgba(45,220,255,0.4)]"
                  : "bg-white/10 text-white/60 hover:bg-white/20"
              }`}
            >
              <GitCommit size={12} />
              {it.version}
              <span className={`px-1 rounded text-[9px] ${activeVersion === it.version ? "bg-black/20" : SOURCE_BADGE[it.source]?.cls || SOURCE_BADGE.seed.cls}`}>
                {SOURCE_BADGE[it.source]?.label || "CAM"}
              </span>
              <span className="opacity-70">CAS {typeof it.cas === "number" ? it.cas.toFixed(3) : it.cas}</span>
            </button>
          ))}
        </div>
      </div>

      {notice && (() => {
        const Icon = NoticeIcon[notice.type] || AlertTriangle;
        return (
          <div className={`flex items-start gap-2 px-4 py-3 rounded-xl border text-xs font-semibold ${noticeCls[notice.type] || noticeCls.warn}`}>
            <Icon size={14} className="mt-0.5 shrink-0" />
            <span>{notice.text}</span>
          </div>
        );
      })()}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Editable PlantUML source */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl border border-cyan-400/30 bg-[#0a0c1a] overflow-hidden flex flex-col font-mono shadow-2xl">
            <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-[#050610] border-b border-white/10 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block" />
                <span className="w-3 h-3 rounded-full bg-yellow-500/80 inline-block" />
                <span className="w-3 h-3 rounded-full bg-green-500/80 inline-block" />
                <span className="ml-2 font-bold text-cyan-400 text-[11px] uppercase tracking-wider">
                  architecture_diagram_{active?.version}.puml
                </span>
                {isDirty && <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-bold">UNSAVED</span>}
              </div>
              <div className="flex items-center gap-2 text-white/50 text-[11px]">
                <span className={`px-2 py-0.5 rounded font-semibold ${passed ? "bg-green-500/15 text-green-300" : "bg-amber-500/15 text-amber-300"}`}>
                  CAS {cas.toFixed(3)}
                </span>
                <span>{lines.length} lines</span>
                <button
                  onClick={() => navigator.clipboard.writeText(draftCode)}
                  className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-[10px] font-bold cursor-pointer transition-all"
                >
                  Copy
                </button>
              </div>
            </div>

            <div className="flex bg-[#060814] h-[420px]">
              <div
                ref={gutterRef}
                className="select-none overflow-hidden py-4 pl-3 pr-3 text-right text-white/30 border-r border-white/10 text-[11px] leading-[1.6]"
                aria-hidden="true"
              >
                {lines.map((_, i) => (
                  <div key={i}>{i + 1}</div>
                ))}
              </div>
              <textarea
                id="diagram-source-editor"
                value={draftCode}
                spellCheck={false}
                wrap="off"
                onChange={(e) => setDraftCode(e.target.value)}
                onScroll={(e) => {
                  if (gutterRef.current) gutterRef.current.scrollTop = e.target.scrollTop;
                }}
                className="flex-1 resize-none bg-transparent text-cyan-200 text-[11px] leading-[1.6] py-4 px-3 outline-none whitespace-pre overflow-auto"
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-[#050610] border-t border-white/10">
              <span className="text-[10px] text-white/40">
                Edit the PlantUML directly. Rescoring is deterministic and runs against this candidate's architecture.
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setDraftCode(activeCode)}
                  disabled={!isDirty}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-bold text-white/70 bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-all"
                >
                  <Undo2 size={12} /> Discard
                </button>
                <button
                  id="apply-manual-edit"
                  onClick={onApplyEdit}
                  disabled={!isDirty || applyingEdit}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[11px] font-bold text-black bg-cyan-400 hover:bg-cyan-300 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-all"
                >
                  {applyingEdit ? <RefreshCw size={12} className="animate-spin" /> : <Save size={12} />}
                  {applyingEdit ? "Rescoring..." : "Apply Edit & Rescore"}
                </button>
              </div>
            </div>
          </div>

          {/* Live git-style diff */}
          {liveDiff.diff && (
            <div className="rounded-2xl border border-white/10 bg-[#080818] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-300 font-mono">
                  Git Diff &middot; {liveDiff.label}
                </span>
                <span className="flex gap-2 text-[11px] font-mono">
                  <span className="px-2 py-0.5 rounded bg-green-500/15 text-green-300">+{stats.added}</span>
                  <span className="px-2 py-0.5 rounded bg-red-500/15 text-red-300">-{stats.removed}</span>
                </span>
              </div>
              <DiffView diff={liveDiff.diff} maxHeight="max-h-[260px]" />
            </div>
          )}
        </div>

        {/* AI refinement */}
        <div
          className={`p-6 rounded-2xl border space-y-4 flex flex-col justify-between ${
            passed
              ? "border-green-400/20 bg-gradient-to-br from-green-950/30 via-emerald-950/10 to-black"
              : "border-amber-400/20 bg-gradient-to-br from-amber-950/30 via-orange-950/10 to-black"
          }`}
        >
          <div className="space-y-3">
            <div className={`flex items-center gap-2 ${passed ? "text-green-300" : "text-amber-300"}`}>
              {passed ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
              <h4 className="text-xs font-bold uppercase tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
                {passed ? "Threshold Met · Refinement Optional" : "Quality Threshold Not Met"}
              </h4>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-white/10 space-y-1">
              <p className="text-[11px] text-white/60 font-mono">
                CAS <span className={passed ? "text-green-300 font-bold" : "text-amber-300 font-bold"}>{cas.toFixed(3)}</span> / threshold{" "}
                <span className="text-white/80">{threshold.toFixed(3)}</span>
              </p>
              {active?.issues?.length > 0 && (
                <ul className="text-[10px] text-amber-200/70 space-y-0.5 mt-1">
                  {active.issues.slice(0, 4).map((iss, i) => (
                    <li key={i} className="flex gap-1">
                      <span className="text-amber-400">›</span>
                      {iss}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <p className="text-[11px] text-white/50">
              Describe the change you want. The AI edits the <strong className="text-white/70">current version</strong> of
              this candidate's diagram and the result is scored deterministically.
            </p>
            <textarea
              id="diagram-refine-prompt"
              rows={5}
              value={refinePrompt}
              onChange={(e) => setRefinePrompt(e.target.value)}
              placeholder="e.g. Add a Redis cache between TaskService and TaskRepository, and group the auth components together."
              className="w-full p-3 rounded-xl bg-black/60 border border-white/10 text-xs text-white placeholder:text-white/30 focus:border-cyan-400 outline-none"
            />
          </div>
          <button
            id="run-ai-refinement"
            onClick={onRefine}
            disabled={refining}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-cyan-400 text-black cursor-pointer hover:bg-cyan-300 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Sparkles size={14} className={refining ? "animate-spin" : ""} />
            {refining ? "AI Refinement Running..." : refinePrompt.trim() ? "Run AI Refinement" : "Run Automatic Improvement"}
          </button>
        </div>
      </div>
    </div>
  );
}
