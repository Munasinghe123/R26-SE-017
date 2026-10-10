import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  X,
  FileCheck2,
  Check,
  Info
} from "lucide-react";

export default function QualityEvaluationModal({
  isOpen,
  onClose,
  evaluationData,
  loading
}) {
  const [selectedTab, setSelectedTab] = useState("all");
  const [expandedReq, setExpandedReq] = useState(null);

  if (!isOpen) return null;

  const report = evaluationData?.quality_report || {};
  const summary = report.summary || {
    total_requirements: 0,
    passed_all_characteristics: 0,
    needs_improvement: 0
  };
  const detailed = report.detailed_evaluations || [];

  const filtered = detailed.filter((req) => {
    if (selectedTab === "passed") return (req.issues_found || []).length === 0;
    if (selectedTab === "issues") return (req.issues_found || []).length > 0;
    return true;
  });

  const toggleExpand = (id) => {
    setExpandedReq(expandedReq === id ? null : id);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-4 md:p-8 overflow-y-auto">
      <div className="relative w-full max-w-5xl max-h-[90vh] bg-[#0f172a] border border-cyan-500/30 rounded-3xl shadow-[0_0_50px_rgba(34,211,238,0.15)] flex flex-col overflow-hidden text-white my-auto">
        
        {/* MODAL HEADER */}
        <div className="p-6 md:p-8 border-b border-white/10 flex items-start justify-between gap-4 bg-gradient-to-r from-cyan-950/40 via-[#0f172a] to-purple-950/40">
          <div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-2">
              <ShieldCheck size={14} />
              ISO/IEC/IEEE 29148 Verification Report
            </div>
            <h2 
              style={{ fontFamily: "Orbitron, sans-serif" }} 
              className="text-2xl md:text-3xl font-extrabold text-white"
            >
              Requirements <span className="text-cyan-300">Quality Audit</span>
            </h2>
            <p className="text-xs md:text-sm text-gray-400 mt-1">
              Automated evaluation against 9 IEEE 29148 quality characteristics with explanations and improvements.
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white transition cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        {/* LOADING STATE */}
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center p-16 space-y-4">
            <div className="animate-spin rounded-full h-14 w-14 border-t-2 border-b-2 border-cyan-400"></div>
            <p className="text-cyan-300 font-semibold animate-pulse text-sm">
              Evaluating requirements against 9 IEEE 29148 Quality Characteristics...
            </p>
            <p className="text-xs text-gray-400 max-w-md text-center">
              Auditing necessity, appropriateness, ambiguity, completeness, singularity, feasibility, verifiability, correctness, and IEEE conforming format.
            </p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 custom-scrollbar">
            
            {/* EXECUTIVE METRICS SUMMARY */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Total Evaluated */}
              <div className="p-5 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                  <FileCheck2 size={14} /> Total Requirements
                </span>
                <div className="text-3xl md:text-4xl font-extrabold mt-2 text-white font-mono">
                  {summary.total_requirements}
                </div>
                <span className="text-[11px] text-gray-400 mt-1">Checked Across 9 Standards</span>
              </div>

              {/* Fully Compliant */}
              <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 flex flex-col justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 size={14} /> Passed 9/9 Standards
                </span>
                <div className="text-3xl md:text-4xl font-extrabold mt-2 text-emerald-300 font-mono">
                  {summary.passed_all_characteristics}
                </div>
                <span className="text-[11px] text-emerald-500/80 mt-1">Fully Compliant</span>
              </div>

              {/* Needs Improvement */}
              <div className="p-5 rounded-2xl bg-amber-950/20 border border-amber-500/30 flex flex-col justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                  <AlertTriangle size={14} /> Quality Gaps Found
                </span>
                <div className="text-3xl md:text-4xl font-extrabold mt-2 text-amber-300 font-mono">
                  {summary.needs_improvement}
                </div>
                <span className="text-[11px] text-amber-500/80 mt-1">Improvements Identified</span>
              </div>
            </div>

            {/* 9 CHARACTERISTICS OVERVIEW */}
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10 space-y-3">
              <h3 className="text-sm font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                <Sparkles size={16} />
                Audited Quality Characteristics
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {[
                  "necessary",
                  "appropriate",
                  "unambiguous",
                  "complete",
                  "singular",
                  "feasible",
                  "verifiable",
                  "correct",
                  "conforming"
                ].map((charName) => (
                  <div key={charName} className="p-3 rounded-xl bg-[#090d16] border border-white/5 flex items-center gap-2">
                    <span className="p-1 rounded-md bg-cyan-500/10 text-cyan-300">
                      <Check size={12} />
                    </span>
                    <span className="text-xs font-semibold text-gray-200 capitalize">
                      {charName}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* REQUIREMENTS DETAILED AUDIT LIST */}
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  Requirement Evaluations ({filtered.length})
                </h3>

                <div className="flex items-center gap-2 text-xs">
                  <button
                    onClick={() => setSelectedTab("all")}
                    className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                      selectedTab === "all"
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                        : "text-gray-400 hover:text-white"
                    }`}
                  >
                    All ({detailed.length})
                  </button>
                  <button
                    onClick={() => setSelectedTab("issues")}
                    className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                      selectedTab === "issues"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                        : "text-gray-400 hover:text-white"
                    }`}
                  >
                    With Gaps ({summary.needs_improvement})
                  </button>
                  <button
                    onClick={() => setSelectedTab("passed")}
                    className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                      selectedTab === "passed"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : "text-gray-400 hover:text-white"
                    }`}
                  >
                    Fully Compliant ({summary.passed_all_characteristics})
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {filtered.map((req) => {
                  const isExpanded = expandedReq === req.id;
                  const hasIssues = (req.issues_found || []).length > 0;

                  return (
                    <div
                      key={req.id}
                      className={`p-5 rounded-2xl border transition-all duration-300 space-y-3 ${
                        hasIssues
                          ? "bg-amber-950/10 border-amber-500/20 hover:border-amber-400/40"
                          : "bg-white/5 border-white/10 hover:border-emerald-500/30"
                      }`}
                    >
                      {/* CARD HEADER */}
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-0.5 rounded-md bg-white/10 font-mono font-bold text-cyan-300 text-xs">
                              {req.id}
                            </span>
                            <span className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold">
                              {req.type === "non_functional" ? "Non-Functional" : "Functional"}
                            </span>
                            {hasIssues ? (
                              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full border border-amber-500/40 bg-amber-950/40 text-amber-300">
                                {req.issues_found.length} Issue{req.issues_found.length > 1 ? "s" : ""} Identified
                              </span>
                            ) : (
                              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full border border-emerald-500/40 bg-emerald-950/40 text-emerald-300">
                                Compliant
                              </span>
                            )}
                          </div>

                          <p className="text-sm text-gray-200 leading-relaxed font-medium pt-1">
                            {req.original_text}
                          </p>
                        </div>

                        <button
                          onClick={() => toggleExpand(req.id)}
                          className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 transition cursor-pointer shrink-0"
                        >
                          {isExpanded ? (
                            <>Hide Findings <ChevronUp size={14} /></>
                          ) : (
                            <>View Findings <ChevronDown size={14} /></>
                          )}
                        </button>
                      </div>

                      {/* 9 CHARACTERISTICS STATUS PILLS & COMPOUND ATOMICITY PRE-CHECK */}
                      <div className="space-y-2 pt-1">
                        {/* Atomicity Check Badge */}
                        {req.rule_checks?.compound_check && (
                          <div className="flex items-center text-[11px]">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md font-semibold border ${
                                req.rule_checks.compound_check?.is_compound
                                  ? "bg-amber-950/40 border-amber-500/40 text-amber-300"
                                  : "bg-emerald-950/40 border-emerald-500/30 text-emerald-300"
                              }`}
                            >
                              {req.rule_checks.compound_check?.is_compound ? (
                                <AlertTriangle size={11} />
                              ) : (
                                <Check size={11} />
                              )}
                              Atomicity: {req.rule_checks.compound_check?.is_compound ? `Possible Compound (${req.rule_checks.compound_check.evidence?.join(", ")})` : "Atomic Statement"}
                            </span>
                          </div>
                        )}

                        {/* 9 Quality Characteristics Pills */}
                        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                          {Object.entries(req.evaluations || {}).map(([charName, evalItem]) => {
                            const satisfies = evalItem.satisfies;
                            return (
                              <span
                                key={charName}
                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${
                                  satisfies
                                    ? "bg-emerald-950/30 border-emerald-500/20 text-emerald-400"
                                    : "bg-amber-950/30 border-amber-500/30 text-amber-300"
                                }`}
                              >
                                {satisfies ? <Check size={10} /> : <AlertTriangle size={10} />}
                                {charName}: {satisfies ? "YES" : "NO"}
                              </span>
                            );
                          })}
                        </div>
                      </div>

                      {/* EXPANDED AUDIT DETAILS */}
                      {isExpanded && (
                        <div className="pt-3 border-t border-white/10 space-y-4 text-xs">
                          
                          {/* COMPOUND REQUIREMENT FINDINGS */}
                          {req.rule_checks?.compound_check?.is_compound && (
                            <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-2">
                              <span className="font-bold text-purple-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                                <ShieldCheck size={14} /> Atomicity Linguistic Pre-Check:
                              </span>
                              
                              <div className="text-gray-200 bg-black/40 p-2.5 rounded-lg border border-amber-500/20 space-y-1">
                                <div className="font-semibold text-amber-300 flex items-center gap-1 text-[11px]">
                                  <AlertTriangle size={12} /> Possible Compound Requirement:
                                </div>
                                <p className="text-gray-300 text-xs">{req.rule_checks.compound_check?.message}</p>
                                {req.rule_checks.compound_check?.detected_actions?.length > 0 && (
                                  <p className="text-cyan-300 text-[11px]">
                                    Detected Actions: {req.rule_checks.compound_check.detected_actions.join(" | ")}
                                  </p>
                                )}
                              </div>
                            </div>
                          )}

                          {hasIssues ? (
                            <div className="space-y-3">
                              {/* ACTIONABLE IMPROVEMENTS: ONE LINE AFTER THE NEXT */}
                              <div className="p-4 rounded-2xl bg-amber-950/30 border border-amber-500/40 space-y-2.5">
                                <span className="font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5 text-xs">
                                  <Sparkles size={14} className="text-cyan-400" />
                                  Recommended Improvements:
                                </span>
                                <div className="space-y-2 text-xs">
                                  {req.issues_found.map((issueKey) => {
                                    const issueData = req.evaluations[issueKey] || {};
                                    const fixText = (issueData.improvement && issueData.improvement !== "No improvement required.")
                                      ? issueData.improvement
                                      : issueData.explanation;
                                    return (
                                      <div key={issueKey} className="flex items-start gap-2 text-gray-200 bg-black/30 p-2.5 rounded-xl border border-white/5">
                                        <span className="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 font-bold uppercase text-[10px] tracking-wider shrink-0 mt-0.5">
                                          {issueKey}
                                        </span>
                                        <p className="leading-relaxed text-xs text-gray-100 flex-1">
                                          {fixText}
                                        </p>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>

                              {/* EVALUATION EXPLANATIONS */}
                              <div className="space-y-2">
                                <span className="font-semibold text-gray-400 uppercase tracking-wider text-[11px] block">
                                  Evaluation Findings & Analysis:
                                </span>
                                {req.issues_found.map((issueKey) => {
                                  const issueData = req.evaluations[issueKey] || {};
                                  return (
                                    <div key={issueKey} className="p-3 rounded-xl bg-black/40 border border-white/10 space-y-1">
                                      <div className="font-bold text-amber-400 capitalize flex items-center gap-1.5 text-xs">
                                        <AlertTriangle size={13} /> {issueKey}
                                      </div>
                                      <p className="text-gray-300 leading-relaxed text-xs">
                                        {issueData.explanation}
                                      </p>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          ) : (
                            <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                              <CheckCircle2 size={16} /> This requirement satisfies all 9 IEEE quality characteristics with no issues identified.
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}

        {/* MODAL FOOTER */}
        <div className="p-6 border-t border-white/10 bg-[#090d16] flex items-center justify-between gap-4">
          <div className="text-xs text-gray-400">
            {summary.needs_improvement > 0 ? (
              <span>
                <strong className="text-amber-300">{summary.needs_improvement}</strong> requirement{summary.needs_improvement > 1 ? "s" : ""} have improvement suggestions available.
              </span>
            ) : (
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 size={14} /> All requirements satisfy the 9 quality characteristics.
              </span>
            )}
          </div>

          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-full text-xs font-semibold uppercase tracking-wider text-gray-300 border border-white/10 hover:bg-white/5 transition cursor-pointer"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
