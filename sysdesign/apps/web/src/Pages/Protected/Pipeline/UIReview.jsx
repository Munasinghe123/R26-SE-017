/**
 * UIReview.jsx — UI/UX Usability Suite (Agent 4) Research & Execution Dashboard
 *
 * Features:
 * 1. Screen Plan & Hierarchy (User Roles, Screen Types, Key Actions, Mapped FRs)
 * 2. Interactive Prototype Sandbox with live FR Traceability Highlighting (data-fr)
 * 3. Multi-Standard Convergence Chart (ISO 9241-11, Nielsen 10 Heuristics, WCAG 2.2)
 * 4. Iterative Refinement History with automated fixes & regression checks
 * 5. Traceability Matrix & Usability Score Breakdown
 * 6. Research Methodology, Formulas & Academic Citations
 *
 * Aesthetic: Dark mode #05050f, Orbitron font, cyan #2DDCFF & pink/violet accents.
 */

import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import {
  LayoutGrid,
  Monitor,
  Smartphone,
  Tablet,
  TrendingUp,
  History,
  ShieldCheck,
  BookOpen,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Download,
  Code2,
  Activity,
  ArrowRight,
  RefreshCw,
  Eye,
  FileCode,
  Sliders,
  Check,
} from "lucide-react";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from "recharts";

const SERIES = [
  { key: "total_score", label: "Total", color: "#22d3ee" },
  { key: "iso_score", label: "ISO 9241-11", color: "#4ade80" },
  { key: "nielsen_score", label: "Nielsen", color: "#c084fc" },
  { key: "wcag_score", label: "WCAG 2.2", color: "#60a5fa" },
];

function ConvergenceChart({ history }) {
  if (!history || history.length === 0) {
    return <p className="text-white/40 text-xs font-mono">No convergence iterations recorded yet for this screen.</p>;
  }
  const threshold = history[0]?.report?.threshold ?? 85;
  const data = history.map((e) => ({
    name: `Iter ${e.iteration}`,
    total_score: e.report.total_score,
    iso_score: e.report.iso_score,
    nielsen_score: e.report.nielsen_score,
    wcag_score: e.report.wcag_score,
  }));

  return (
    <div className="bg-black/40 border border-white/10 rounded-xl p-4">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid stroke="#1e293b" />
          <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 100]} stroke="#94a3b8" tick={{ fontSize: 12 }} />
          <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} labelStyle={{ color: "#f1f5f9" }} />
          <Legend wrapperStyle={{ fontSize: 12, color: "#cbd5e1" }} />
          <ReferenceLine y={threshold} stroke="#facc15" strokeDasharray="6 4"
            label={{ value: `Threshold ${threshold}`, position: "insideTopRight", fill: "#facc15", fontSize: 12 }} />
          {SERIES.map((s) => (
            <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color}
              strokeWidth={2.5} dot={{ r: 4, fill: s.color, strokeWidth: 0 }} isAnimationActive={false} connectNulls />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "http://127.0.0.1:8000";
const AGENT4_BASE = "http://127.0.0.1:8004";


export default function UIReview() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // ── Top Level States ────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState("screens");
  const [uiData, setUiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

    // Agent 4 real data
  const [screenIds, setScreenIds] = useState([]);
  const [reportsMap, setReportsMap] = useState({});
  const [htmlCache, setHtmlCache] = useState({});
  const [historyCache, setHistoryCache] = useState({});
  const [traceCache, setTraceCache] = useState({});
  const [loadingScreen, setLoadingScreen] = useState(false);

  // Sandbox controls
  const [selectedScreenId, setSelectedScreenId] = useState("");
  const [viewportMode, setViewportMode] = useState("desktop");
  const [highlightedFr, setHighlightedFr] = useState(searchParams.get("highlight") || "");
  const [showHtmlCode, setShowHtmlCode] = useState(false);
  const [copied, setCopied] = useState(false);

  const iframeRef = useRef(null);

    // Load screen plan + reports list once
  useEffect(() => {
    if (!jobId) return;


    // reset per-job caches so a new session doesn't show stale data
    setScreenIds([]);
    setReportsMap({});
    setHtmlCache({});
    setHistoryCache({});
    setTraceCache({});
    setSelectedScreenId("");
    setHighlightedFr("");

    const loadAll = async () => {
      try {
        const jobRes = await fetch(`${ORCHESTRATOR}/jobs/${jobId}`);
        const jobData = await jobRes.json();

        const uiArtifact = jobData?.artifacts?.ui || {};

        setUiData({
          project_name:
            uiArtifact.project_name ||
            jobData?.job?.project_name ||
            "Project",
          domain: uiArtifact.domain || "",
          screens: uiArtifact.screens || [],
        });

        const outputsRes = await fetch(`${AGENT4_BASE}/api/outputs`);
        const outputsData = await outputsRes.json();

        const ids = outputsData.screens || [];

        setScreenIds(ids);

        if (ids.length > 0) {
          setSelectedScreenId(ids[0]);
        }

        const reportsRes = await fetch(`${AGENT4_BASE}/api/reports`);
        const reportsData = await reportsRes.json();

        const rMap = {};

        (reportsData.reports || []).forEach((r) => {
          rMap[r.screenId] = r.report;
        });

        setReportsMap(rMap);
      } catch (err) {
        console.error("Agent 4 loading error:", err);

        setError(
          "Could not load UI Usability data from Agent 4. Is it running on :8004?"
        );
      } finally {
        setLoading(false);
      }
    };

    loadAll();
  }, [jobId]);

    // Load per-screen HTML / history / traceability on demand
  useEffect(() => {
    if (!selectedScreenId) return;

    const loadScreen = async () => {
      setLoadingScreen(true);

      try {
        if (htmlCache[selectedScreenId] === undefined) {
          const res = await fetch(
            `${AGENT4_BASE}/api/outputs?screenId=${selectedScreenId}`
          );

          const data = await res.json();

          setHtmlCache((prev) => ({
            ...prev,
            [selectedScreenId]: data.html || "",
          }));
        }

        if (historyCache[selectedScreenId] === undefined) {
          const res = await fetch(
            `${AGENT4_BASE}/api/history?screenId=${selectedScreenId}`
          );

          const data = await res.json();

          setHistoryCache((prev) => ({
            ...prev,
            [selectedScreenId]: data.history || [],
          }));
        }

        if (traceCache[selectedScreenId] === undefined) {
          const res = await fetch(
            `${AGENT4_BASE}/api/traceability?screenId=${selectedScreenId}`
          );

          const data = await res.json();

          setTraceCache((prev) => ({
            ...prev,
            [selectedScreenId]: data.traceability || null,
          }));
        }
      } catch (err) {
        console.warn("Failed to load screen detail:", err);
      } finally {
        setLoadingScreen(false);
      }
    };

    loadScreen();
  }, [
    selectedScreenId,
    htmlCache,
    historyCache,
    traceCache,
  ]);

  // Highlight FR inside iframe when changed
  useEffect(() => {
    if (!iframeRef.current || !highlightedFr) return;
    try {
      const doc = iframeRef.current.contentDocument || iframeRef.current.contentWindow?.document;
      if (!doc) return;

      const targets = doc.querySelectorAll("[data-fr]");
      let matchedEl = null;

      targets.forEach((el) => {
        const ids = (el.getAttribute("data-fr") || "").split(",").map((s) => s.trim());
        if (!matchedEl && ids.includes(highlightedFr)) {
          matchedEl = el;
        } else {
          el.style.outline = "";
          el.style.boxShadow = "";
        }
      });

      if (matchedEl) {
        matchedEl.scrollIntoView({ behavior: "smooth", block: "center" });
        matchedEl.style.outline = "3px solid #2DDCFF";
        matchedEl.style.outlineOffset = "3px";
        matchedEl.style.boxShadow = "0 0 20px rgba(45, 220, 255, 0.8)";
      }
    } catch {
      // Cross-origin safe
    }
  }, [highlightedFr, selectedScreenId]);

    const [evaluating, setEvaluating] = useState(false);
  const [refining, setRefining] = useState(false);

  const evaluateScreen = async (screenId) => {
    if (!screenId) return;
    setEvaluating(true);
    try {
      const res = await fetch(`${AGENT4_BASE}/api/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ screenIds: [screenId] }),
      });
      const data = await res.json();
      const rpt = data.reports?.find((r) => r.screenId === screenId)?.report;
      if (rpt) setReportsMap((prev) => ({ ...prev, [screenId]: rpt }));
    } catch (err) {
      console.error("Evaluate failed:", err);
    } finally {
      setEvaluating(false);
    }
  };

    const evaluateAllScreens = async () => {
    setEvaluating(true);
    try {
      const res = await fetch(`${AGENT4_BASE}/api/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `Evaluate failed (HTTP ${res.status})`);
      }
      const data = await res.json();
      // Merge into existing map instead of replacing — a partial batch
      // (some screens succeeded, some failed) should never erase results
      // that already came back successfully.
      setReportsMap((prev) => {
        const next = { ...prev };
        (data.reports || []).forEach((r) => { next[r.screenId] = r.report; });
        return next;
      });
      if (data.errors?.length) {
        console.warn("Some screens failed to evaluate:", data.errors);
      }
    } catch (err) {
      console.error("Evaluate all failed:", err);
      setError(`Evaluation failed: ${err.message}`);
    } finally {
      setEvaluating(false);
    }
  };
  const refineScreen = async (screenId) => {
    if (!screenId) return;
    setRefining(true);
    try {
      const res = await fetch(`${AGENT4_BASE}/api/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ screenId }),
      });
      const data = await res.json();
      setHtmlCache((prev) => ({ ...prev, [screenId]: data.html ?? prev[screenId] }));
      setHistoryCache((prev) => ({ ...prev, [screenId]: data.history || [] }));
      if (data.finalReport) {
        setReportsMap((prev) => ({ ...prev, [screenId]: data.finalReport }));
      }
    } catch (err) {
      console.error("Refine failed:", err);
    } finally {
      setRefining(false);
    }
  };

  const downloadScreenReport = async (screenId) => {
  try {
    let history = historyCache[screenId];
    if (history === undefined) {
      const res = await fetch(`${AGENT4_BASE}/api/history?screenId=${screenId}`);
      const data = await res.json();
      history = data.history || [];
      setHistoryCache((prev) => ({ ...prev, [screenId]: history }));
    }
    // Prefer the actual final/best refinement iteration; fall back to the
    // plain evaluate result only if this screen was never refined.
    const finalEntry = history.find((h) => h.isFinal);
    const report = finalEntry ? finalEntry.report : reportsMap[screenId];
    if (!report) return;

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${screenId}_final_score_report.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to download report:", err);
  }
};

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#05050f]">
        <div className="text-cyan-400 animate-spin"><Activity size={40} /></div>
      </div>
    );
  }

  const currentScreen = uiData?.screens?.find((s) => s.screen_id === selectedScreenId) || uiData?.screens?.[0];
  const currentHtml = htmlCache[selectedScreenId] || "<p class='p-8 text-white'>Loading...</p>";
  const currentHistory = historyCache[selectedScreenId] || [];
  const currentTraceability = traceCache[selectedScreenId] || {
    coverage_pct: 0, total_frs: 0, covered_frs: 0,
    untagged_elements: 0, total_interactive_elements: 0, matrix: [],
  };


  const copyCode = () => {
    navigator.clipboard.writeText(currentHtml);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadHtmlFile = () => {
    const blob = new Blob([currentHtml], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedScreenId || "screen"}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen w-full px-6 pb-20 pt-24 text-white bg-[#05050f]">
      <div className="mx-auto w-full max-w-7xl space-y-6">

        {/* ── Title & Header ─────────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-cyan-500/20 pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
              UI/UX Usability <span className="text-cyan-400">Suite (Agent 4)</span>
            </h1>
            <p className="text-xs text-white/50 mt-1">
              Automated Screen Planning · Qwen3-Coder Generation · ISO 9241-11 · Nielsen 10 · WCAG 2.2 Self-Refinement
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 rounded-full">
              Model: Qwen3-Coder (via OpenRouter)
            </span>
          </div>
        </div>

        {/* ── Navigation Tabs ────────────────────────────────────────── */}
        <div className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
          {[
            { id: "screens",      label: "Screen Plan & Hierarchy",   icon: LayoutGrid },
            { id: "sandbox",      label: "Interactive Prototype",     icon: Monitor },
            { id: "reports",      label: "Score Reports",             icon: FileCode },
            { id: "convergence",  label: "Convergence Chart",         icon: TrendingUp },
            { id: "history",      label: "Refinement Iterations",     icon: History },
            { id: "traceability", label: "Traceability Matrix",       icon: ShieldCheck },
            { id: "rubric",       label: "Evaluation Rubric",         icon: BookOpen },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wider transition-all cursor-pointer
                  ${active
                    ? "bg-cyan-500/10 border border-cyan-400 text-cyan-300 shadow-[0_0_15px_rgba(45,220,255,0.2)]"
                    : "bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10"
                  }
                `}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {["convergence", "history", "traceability"].includes(activeTab) && (
          <div className="flex items-center gap-3 pb-2">
            <span className="text-xs text-white/50 uppercase font-mono">Screen:</span>
            <select
              value={selectedScreenId}
              onChange={(e) => setSelectedScreenId(e.target.value)}
              className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-xl text-xs text-cyan-300 font-mono focus:outline-none focus:border-cyan-400"
            >
              {screenIds.map((id) => (
                <option key={id} value={id} className="bg-slate-900 text-white">{id}</option>
              ))}
            </select>
            {loadingScreen && <span className="text-[10px] text-white/30">loading…</span>}
          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 1: SCREEN PLAN & HIERARCHY                                */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "screens" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-cyan-300 uppercase tracking-widest" style={{ fontFamily: "Orbitron, sans-serif" }}>
                Architectural Screen Plan
              </h3>
              <span className="text-xs text-white/40">{uiData?.screens?.length || 0} Screens Planned</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {uiData?.screens?.map((scr, idx) => (
                <div
                  key={idx}
                  className="p-6 rounded-2xl border border-cyan-400/20 bg-black/60 space-y-4 hover:border-cyan-400/40 transition"
                >
                  <div className="flex justify-between items-start border-b border-white/10 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-bold bg-cyan-400/10 text-cyan-300 px-2 py-0.5 rounded">
                          {scr.screen_id}
                        </span>
                        <h4 className="text-sm font-bold text-white font-mono">{scr.screen_name}</h4>
                      </div>
                      <p className="text-xs text-white/40 mt-1">Role: <strong className="text-white/70">{scr.user_role}</strong></p>
                    </div>
                    <span
                      className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${
                        scr.priority === "High"
                          ? "bg-red-400/10 text-red-300 border-red-400/20"
                          : "bg-amber-400/10 text-amber-300 border-amber-400/20"
                      }`}
                    >
                      {scr.priority} Priority
                    </span>
                  </div>

                  <p className="text-xs text-white/70 leading-relaxed">{scr.purpose}</p>

                  {/* Key Actions */}
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold text-white/40">Key Actions</span>
                    <div className="flex flex-wrap gap-1.5">
                      {scr.key_actions?.map((act, ai) => (
                        <span key={ai} className="text-[11px] font-mono px-2 py-0.5 bg-white/5 border border-white/10 rounded-md text-cyan-200">
                          ✓ {act}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Relevant FRs */}
                  <div className="flex items-center justify-between pt-3 border-t border-white/10 text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="text-white/40 text-[10px] uppercase">FR Coverage:</span>
                      {scr.relevant_frs?.map((fr, fi) => (
                        <button
                          key={fi}
                          onClick={() => {
                            setSelectedScreenId(scr.screen_id);
                            setHighlightedFr(fr);
                            setActiveTab("sandbox");
                          }}
                          className="px-1.5 py-0.5 bg-cyan-400/20 text-cyan-300 font-mono text-[10px] rounded hover:bg-cyan-400/40 cursor-pointer"
                        >
                          {fr}
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={() => {
                        setSelectedScreenId(scr.screen_id);
                        setActiveTab("sandbox");
                      }}
                      className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer flex items-center gap-1"
                    >
                      Inspect Sandbox →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 2: SCORE REPORTS                                         */}
        {/* ───────────────────────────────────────────────────────────── */}

        {activeTab === "reports" && (
          <div className="space-y-6">

            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3
                  className="text-sm font-bold text-cyan-300 uppercase tracking-widest"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  Score Reports
                </h3>

                <p className="text-xs text-white/40 mt-1">
                  Multi-standard usability evaluation for each generated screen
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={evaluateAllScreens}
                  disabled={evaluating}
                  className="px-3 py-1.5 bg-cyan-500/10 border border-cyan-400/30 rounded-xl text-xs text-cyan-300 hover:bg-cyan-500/20 cursor-pointer disabled:opacity-50"
                >
                  {evaluating ? "Evaluating..." : "Evaluate All Screens"}
                </button>
                <span className="text-xs text-white/40 font-mono">
                  {Object.keys(reportsMap).length} report(s)
                </span>
              </div>
            </div>

            {Object.keys(reportsMap).length === 0 ? (

              <div className="p-8 rounded-2xl border border-white/10 bg-black/40 text-center">
                <FileCode
                  size={32}
                  className="mx-auto mb-3 text-white/20"
                />

                <p className="text-sm text-white/50">
                  No score reports available yet.
                </p>

                <p className="text-xs text-white/30 mt-1">
                  Generate and evaluate a screen first.
                  <button
                  onClick={evaluateAllScreens}
                  disabled={evaluating}
                  className="px-3 py-1.5 bg-cyan-500/10 border border-cyan-400/30 rounded-xl text-xs text-cyan-300 hover:bg-cyan-500/20 cursor-pointer disabled:opacity-50"
                >
                  {evaluating ? "Evaluating..." : "Evaluate All Screens"}
                </button>
                </p>
              </div>

            ) : (

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

                {Object.entries(reportsMap).map(([screenId, report]) => {

                  const score = Number(report?.total_score ?? 0);
                  const iso = Number(report?.iso_score ?? 0);
                  const nielsen = Number(report?.nielsen_score ?? 0);
                  const wcag = Number(report?.wcag_score ?? 0);

                  return (
                    <div
                      key={screenId}
                      className="p-5 rounded-2xl border border-white/10 bg-black/50 hover:border-cyan-400/40 transition"
                    >

                      {/* Header */}
                      <div className="flex items-center justify-between mb-5">

                        <div>
                          <p className="text-xs text-white/40 uppercase tracking-wider">
                            Screen
                          </p>

                          <h4 className="text-sm font-bold text-white font-mono mt-1">
                            {screenId}
                          </h4>
                        </div>

                        <div
                          className={`px-3 py-1.5 rounded-xl text-sm font-bold font-mono ${
                            score >= 85
                              ? "bg-green-400/10 text-green-300 border border-green-400/30"
                              : "bg-amber-400/10 text-amber-300 border border-amber-400/30"
                          }`}
                        >
                          {score.toFixed(1)}/100
                        </div>

                      </div>

                      {/* Standards */}
                      <div className="grid grid-cols-3 gap-3 mb-5">

                        <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                          <p className="text-[10px] text-white/40 uppercase">
                            ISO 9241
                          </p>

                          <p className="text-lg font-bold text-green-300 font-mono mt-1">
                            {iso.toFixed(1)}
                          </p>

                          <p className="text-[9px] text-white/30">
                            Weight 30%
                          </p>
                        </div>

                        <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                          <p className="text-[10px] text-white/40 uppercase">
                            Nielsen
                          </p>

                          <p className="text-lg font-bold text-purple-300 font-mono mt-1">
                            {nielsen.toFixed(1)}
                          </p>

                          <p className="text-[9px] text-white/30">
                            Weight 30%
                          </p>
                        </div>

                        <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                          <p className="text-[10px] text-white/40 uppercase">
                            WCAG 2.2
                          </p>

                          <p className="text-lg font-bold text-blue-300 font-mono mt-1">
                            {wcag.toFixed(1)}
                          </p>

                          <p className="text-[9px] text-white/30">
                            Weight 40%
                          </p>
                        </div>

                      </div>

                      {/* Weakest area */}
                      {(report?.weakest_standard || report?.weakest_metric) && (
                        <div className="p-3 rounded-xl bg-red-400/5 border border-red-400/10 mb-4">

                          <p className="text-[10px] text-red-300/70 uppercase tracking-wider">
                            Area requiring improvement
                          </p>

                          <p className="text-xs text-white/70 mt-1">
                            {report?.weakest_standard || "Unknown"}
                            {report?.weakest_metric
                              ? ` · ${report.weakest_metric}`
                              : ""}
                          </p>

                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2">

                        <button
                          onClick={() => {
                            setSelectedScreenId(screenId);
                            setActiveTab("convergence");
                          }}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-cyan-500/10 border border-cyan-400/20 text-cyan-300 text-xs hover:bg-cyan-500/20 transition cursor-pointer"
                        >
                          <TrendingUp size={14} />
                          View Convergence
                        </button>

                        <button
                          onClick={() => {
                            setSelectedScreenId(screenId);
                            setActiveTab("history");
                          }}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white/60 text-xs hover:bg-white/10 transition cursor-pointer"
                        >
                          <History size={14} />
                          View Iterations
                        </button>

                        <button
                          onClick={() => downloadScreenReport(screenId)}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white/60 text-xs hover:bg-white/10 transition cursor-pointer"
                        >
                          <Download size={14} /> Download Report
                        </button>

                      </div>

                    </div>
                  );
                })}

              </div>
            )}

          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 3: INTERACTIVE PROTOTYPE SANDBOX                          */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "sandbox" && (
          <div className="space-y-6">
            
            {/* Top Toolbar: Screen Switcher + Viewport + Traceability Trigger */}
            <div className="p-4 rounded-2xl border border-cyan-400/20 bg-black/60 flex flex-col md:flex-row items-center justify-between gap-4">
              
              {/* Screen Selector */}
              <div className="flex items-center gap-3 w-full md:w-auto">
                <span className="text-xs text-white/50 uppercase font-mono">Screen:</span>
                <select
                  value={selectedScreenId}
                  onChange={(e) => setSelectedScreenId(e.target.value)}
                  className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-xl text-xs text-cyan-300 font-mono focus:outline-none focus:border-cyan-400"
                >
                  {uiData?.screens?.map((s) => (
                    <option key={s.screen_id} value={s.screen_id} className="bg-slate-900 text-white">
                      [{s.screen_id}] {s.screen_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Viewport Switcher */}
              <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
                {[
                  { id: "desktop", label: "Desktop", icon: Monitor },
                  { id: "tablet",  label: "Tablet",  icon: Tablet },
                  { id: "mobile",  label: "Mobile",  icon: Smartphone },
                ].map((vp) => {
                  const Icon = vp.icon;
                  return (
                    <button
                      key={vp.id}
                      onClick={() => setViewportMode(vp.id)}
                      className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition ${
                        viewportMode === vp.id
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/30"
                          : "text-white/60 hover:text-white"
                      }`}
                    >
                      <Icon size={13} />
                      {vp.label}
                    </button>
                  );
                })}
              </div>

              {/* Actions: Trace FR, Download, View Code */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => evaluateScreen(selectedScreenId)}
                  disabled={evaluating}
                  className="px-3 py-1.5 bg-cyan-500/10 border border-cyan-400/30 rounded-xl text-xs text-cyan-300 hover:bg-cyan-500/20 cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                >
                  <TrendingUp size={13} /> {evaluating ? "Evaluating..." : "Evaluate Screen"}
                </button>
                <button
                  onClick={() => refineScreen(selectedScreenId)}
                  disabled={refining}
                  className="px-3 py-1.5 bg-purple-500/10 border border-purple-400/30 rounded-xl text-xs text-purple-300 hover:bg-purple-500/20 cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                >
                  <RefreshCw size={13} className={refining ? "animate-spin" : ""} /> {refining ? "Refining..." : "Refine Screen"}
                </button>
                <button
                  onClick={() => setShowHtmlCode(!showHtmlCode)}
                  className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-xl text-xs text-white hover:bg-white/10 cursor-pointer flex items-center gap-1.5"
                >
                  <Code2 size={13} /> {showHtmlCode ? "Hide Code" : "View Code"}
                </button>
                <button
                  onClick={downloadHtmlFile}
                  className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-xl text-xs text-white hover:bg-white/10 cursor-pointer flex items-center gap-1.5"
                >
                  <Download size={13} /> Export HTML
                </button>
              </div>
            </div>

            {/* FR Traceability Bar */}
            <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/30 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Sparkles size={14} className="text-cyan-400" />
                <span className="text-white/70">Trace Requirement:</span>
                <div className="flex gap-1.5">
                  {currentScreen?.relevant_frs?.map((frId) => (
                    <button
                      key={frId}
                      onClick={() => setHighlightedFr(frId)}
                      className={`px-2 py-0.5 rounded font-mono text-[11px] cursor-pointer transition ${
                        highlightedFr === frId
                          ? "bg-cyan-400 text-slate-950 font-bold shadow-[0_0_10px_rgba(45,220,255,0.6)]"
                          : "bg-white/10 text-cyan-300 hover:bg-white/20"
                      }`}
                    >
                      {frId}
                    </button>
                  ))}
                </div>
              </div>
              {highlightedFr && (
                <button
                  onClick={() => setHighlightedFr("")}
                  className="text-white/40 hover:text-white text-[11px] underline cursor-pointer"
                >
                  Clear Highlight
                </button>
              )}
            </div>

            {/* Sandbox Container */}
            <div className="flex justify-center p-6 bg-slate-950 rounded-2xl border border-white/10 min-h-[600px] overflow-hidden">
              <div
                className={`transition-all duration-300 bg-white rounded-xl shadow-2xl overflow-hidden border border-slate-700 ${
                  viewportMode === "mobile"
                    ? "w-[375px] h-[667px]"
                    : viewportMode === "tablet"
                    ? "w-[768px] h-[750px]"
                    : "w-full h-[700px]"
                }`}
              >
                <iframe
                  ref={iframeRef}
                  srcDoc={currentHtml}
                  title="Screen Sandbox"
                  className="w-full h-full border-none"
                  sandbox="allow-scripts allow-same-origin"
                />
              </div>
            </div>

            {/* Collapsible HTML Source Code */}
            {showHtmlCode && (
              <div className="p-5 rounded-2xl border border-white/10 bg-black/90 space-y-3 font-mono text-xs text-cyan-200">
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-white/50 uppercase">HTML & Tailwind Source Code</span>
                  <button
                    onClick={copyCode}
                    className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 cursor-pointer"
                  >
                    {copied ? <Check size={14} className="text-green-400" /> : <FileCode size={14} />}
                    {copied ? "Copied!" : "Copy Code"}
                  </button>
                </div>
                <pre className="text-white/80 leading-relaxed overflow-x-auto max-h-[350px] whitespace-pre-wrap">
                  {currentHtml}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 4: CONVERGENCE CHART                                      */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "convergence" && (
          <div className="space-y-6">

            <div className="flex items-center justify-between border-b border-white/10 pb-3">

              <div>
                <h3
                  className="text-sm font-bold text-cyan-300 uppercase tracking-widest"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  Multi-Standard Usability Convergence
                </h3>

                <p className="text-xs text-white/40 mt-1">
                  Score progression across refinement iterations
                </p>
              </div>

              <span className="text-xs text-white/40 font-mono">
                Target Threshold: 85%
              </span>

            </div>

            {/* Current screen */}
            <div className="p-4 rounded-2xl border border-white/10 bg-black/40">

              <div className="flex items-center justify-between">

                <div>
                  <p className="text-[10px] text-white/40 uppercase tracking-wider">
                    Selected Screen
                  </p>

                  <p className="text-sm text-cyan-300 font-mono mt-1">
                    {selectedScreenId || "No screen selected"}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-[10px] text-white/40 uppercase">
                    Iterations
                  </p>

                  <p className="text-sm text-white font-mono mt-1">
                    {currentHistory.length}
                  </p>
                </div>

              </div>

            </div>

            {/* Actual Recharts graph */}
            <ConvergenceChart history={currentHistory} />

          </div>
        )}
          
          {activeTab === "history" && (
            <div className="space-y-6">

              <div className="border-b border-white/10 pb-3">

                <h3
                  className="text-sm font-bold text-cyan-300 uppercase tracking-widest"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  Refinement Iterations
                </h3>

                <p className="text-xs text-white/40 mt-1">
                  Evaluation and improvement history for the selected screen
                </p>

              </div>

              {currentHistory.length === 0 ? (

                <div className="p-8 rounded-2xl border border-white/10 bg-black/40 text-center">

                  <History
                    size={32}
                    className="mx-auto mb-3 text-white/20"
                  />

                  <p className="text-sm text-white/50">
                    No refinement iterations recorded for this screen.
                  </p>

                </div>

              ) : (

                <div className="space-y-4">

                  {currentHistory.map((entry, index) => {

                    const report = entry?.report || {};

                    const score = Number(report.total_score ?? 0);
                    const threshold = Number(
                      report.threshold ??
                      entry.threshold ??
                      85
                    );

                    const passed = score >= 85;

                    return (
                      <div
                        key={entry.iteration ?? index}
                        className="p-5 rounded-2xl border border-white/10 bg-black/50"
                      >

                        {/* Iteration header */}
                        <div className="flex items-center justify-between mb-5">

                          <div className="flex items-center gap-3">

                            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-400/20 flex items-center justify-center">
                              <span className="text-cyan-300 font-bold font-mono">
                                {entry.iteration ?? index + 1}
                              </span>
                            </div>

                            <div>
                              <p className="text-[10px] text-white/40 uppercase">
                                Refinement
                              </p>

                              <p className="text-sm font-bold text-white">
                                Iteration {entry.iteration ?? index + 1}
                              </p>
                            </div>

                          </div>

                          <div
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono ${
                              passed
                                ? "bg-green-400/10 text-green-300 border border-green-400/20"
                                : "bg-amber-400/10 text-amber-300 border border-amber-400/20"
                            }`}
                          >
                            {passed ? "PASSED" : "REFINED"}
                          </div>

                        </div>

                        {/* Score */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

                          <div className="p-3 rounded-xl bg-cyan-400/5 border border-cyan-400/10">
                            <p className="text-[10px] text-white/40 uppercase">
                              Total
                            </p>

                            <p className="text-xl font-bold text-cyan-300 font-mono mt-1">
                              {score.toFixed(1)}
                            </p>
                          </div>

                          <div className="p-3 rounded-xl bg-green-400/5 border border-green-400/10">
                            <p className="text-[10px] text-white/40 uppercase">
                              ISO
                            </p>

                            <p className="text-lg font-bold text-green-300 font-mono mt-1">
                              {Number(report.iso_score ?? 0).toFixed(1)}
                            </p>
                          </div>

                          <div className="p-3 rounded-xl bg-purple-400/5 border border-purple-400/10">
                            <p className="text-[10px] text-white/40 uppercase">
                              Nielsen
                            </p>

                            <p className="text-lg font-bold text-purple-300 font-mono mt-1">
                              {Number(report.nielsen_score ?? 0).toFixed(1)}
                            </p>
                          </div>

                          <div className="p-3 rounded-xl bg-blue-400/5 border border-blue-400/10">
                            <p className="text-[10px] text-white/40 uppercase">
                              WCAG
                            </p>

                            <p className="text-lg font-bold text-blue-300 font-mono mt-1">
                              {Number(report.wcag_score ?? 0).toFixed(1)}
                            </p>
                          </div>

                        </div>

                        {/* Threshold */}
                        <div className="mt-4 flex items-center justify-between text-xs">

                          <span className="text-white/40">
                            Required threshold
                          </span>

                          <span className="text-yellow-300 font-mono">
                            {threshold}%
                          </span>

                        </div>

                        {/* Progress */}
                        <div className="mt-2 h-2 rounded-full bg-white/5 overflow-hidden">

                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${Math.min(score, 100)}%`,
                              background:
                                score >= 85
                                  ? "#4ade80"
                                  : "#22d3ee",
                            }}
                          />

                        </div>

                        {/* Weakest metric */}
                        {(
                          report.weakest_standard ||
                          report.weakest_metric
                        ) && (
                          <div className="mt-4 pt-4 border-t border-white/10">

                            <p className="text-[10px] text-white/40 uppercase tracking-wider">
                              Refinement focus
                            </p>

                            <p className="text-xs text-white/60 mt-1">
                              {report.weakest_standard || "Unknown"}
                              {report.weakest_metric
                                ? ` · ${report.weakest_metric}`
                                : ""}
                            </p>

                          </div>
                        )}

                      </div>
                    );
                  })}

                </div>
              )}

            </div>
          )}
        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 6: TRACEABILITY MATRIX                                    */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "traceability" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-cyan-300 uppercase tracking-widest" style={{ fontFamily: "Orbitron, sans-serif" }}>
                Requirement Traceability Matrix
              </h3>
              <span className="text-xs text-green-400 font-mono font-bold">
                Coverage: {currentTraceability.coverage_pct}%
              </span>
            </div>

            <div className="p-6 rounded-2xl border border-cyan-400/20 bg-black/60 space-y-4">
              <div className="grid grid-cols-4 gap-4 text-xs font-mono border-b border-white/10 pb-4">
                <div className="p-3 bg-white/5 rounded-xl">
                  <span className="text-white/40 text-[10px] block">Total FRs</span>
                  <strong className="text-white text-sm">{currentTraceability.total_frs}</strong>
                </div>
                <div className="p-3 bg-white/5 rounded-xl">
                  <span className="text-white/40 text-[10px] block">Covered FRs</span>
                  <strong className="text-green-400 text-sm">{currentTraceability.covered_frs}</strong>
                </div>
                <div className="p-3 bg-white/5 rounded-xl">
                  <span className="text-white/40 text-[10px] block">Interactive Elements</span>
                  <strong className="text-cyan-300 text-sm">{currentTraceability.total_interactive_elements}</strong>
                </div>
                <div className="p-3 bg-white/5 rounded-xl">
                  <span className="text-white/40 text-[10px] block">Untagged Elements</span>
                  <strong className="text-emerald-400 text-sm">{currentTraceability.untagged_elements}</strong>
                </div>
              </div>

              {/* Matrix Table */}
              <div className="space-y-2 font-mono text-xs">
                <div className="grid grid-cols-12 text-[10px] uppercase font-bold text-white/40 px-3 pb-1">
                  <span className="col-span-2">FR ID</span>
                  <span className="col-span-4">Requirement Title</span>
                  <span className="col-span-4">Mapped UI Element</span>
                  <span className="col-span-2 text-right">Status</span>
                </div>

                {currentTraceability.matrix?.map((row, ri) => (
                  <div
                    key={ri}
                    className="grid grid-cols-12 items-center p-3 bg-white/5 border border-white/5 rounded-xl text-xs"
                  >
                    <span className="col-span-2 text-cyan-300 font-bold">{row.fr_id}</span>
                    <span className="col-span-4 text-white/80">{row.description}</span>
                    <span className="col-span-4 text-white/50 text-[11px] truncate">{row.element}</span>
                    <span className="col-span-2 text-right">
                      <span className="px-2 py-0.5 bg-green-400/20 text-green-300 font-bold text-[10px] rounded-full">
                        MATCHED
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 7: EVALUATION RUBRIC & METHODOLOGY                        */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "rubric" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-cyan-300 uppercase tracking-widest" style={{ fontFamily: "Orbitron, sans-serif" }}>
                Empirical Evaluation Architecture
              </h3>
              <span className="text-xs text-white/40">ISO 9241-11 · Nielsen 10 · WCAG 2.2</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 rounded-2xl border border-green-400/30 bg-black/60 space-y-3">
                <span className="text-xs font-bold text-green-400 font-mono uppercase tracking-wider">ISO 9241-11 (30% Weight)</span>
                <p className="text-xs text-white/70 leading-relaxed">
                  Evaluates task performance usability: Effectiveness, Efficiency, and User Satisfaction.
                </p>
                <div className="text-[11px] font-mono text-white/50 space-y-1 pt-2 border-t border-white/10">
                  <p>• Form field grouping & hierarchy</p>
                  <p>• Action button clarity & layout density</p>
                  <p>• Error prevention mechanisms</p>
                </div>
              </div>

              <div className="p-6 rounded-2xl border border-purple-400/30 bg-black/60 space-y-3">
                <span className="text-xs font-bold text-purple-300 font-mono uppercase tracking-wider">Nielsen 10 Heuristics (30% Weight)</span>
                <p className="text-xs text-white/70 leading-relaxed">
                  Expert interaction design quality: Visibility of system status, match with real world, and user control.
                </p>
                <div className="text-[11px] font-mono text-white/50 space-y-1 pt-2 border-t border-white/10">
                  <p>• Status indicators & loading states</p>
                  <p>• Consistency in design tokens</p>
                  <p>• Recognition over recall</p>
                </div>
              </div>

              <div className="p-6 rounded-2xl border border-blue-400/30 bg-black/60 space-y-3">
                <span className="text-xs font-bold text-blue-300 font-mono uppercase tracking-wider">WCAG 2.2 (40% Weight)</span>
                <p className="text-xs text-white/70 leading-relaxed">
                  Accessibility compliance checked via axe-core engine: Legal standard (ADA, EN 301 549, EAA).
                </p>
                <div className="text-[11px] font-mono text-white/50 space-y-1 pt-2 border-t border-white/10">
                  <p>• Color contrast ratio ≥ 4.5:1</p>
                  <p>• Form inputs with explicit labels</p>
                  <p>• Keyboard navigable & ARIA landmarks</p>
                </div>
              </div>

              <div className="p-6 rounded-2xl border border-white/10 bg-black/60 space-y-3">
                <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider">Composite Scoring Formula</h4>
                <p className="text-xs text-white/60 font-mono">Total Score = ISO × 0.30 + Nielsen × 0.30 + WCAG × 0.40</p>
                <p className="text-xs text-white/50">
                  WCAG carries the highest weight because accessibility is a legal requirement in many jurisdictions
                  (EN 301 549, ADA, EAA), benefits all users (curb-cut effect), and is the most objectively verifiable
                  of the three standards via axe-core.
                </p>
              </div>
              <div className="p-6 rounded-2xl border border-white/10 bg-black/60 space-y-3">
                <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider">Refinement Loop Termination</h4>
                <ul className="text-xs text-white/60 space-y-1 list-disc list-inside">
                  <li>Score ≥ 85 → loop stops immediately, current iteration is final.</li>
                  <li>Score &lt; 85 → weakest sub-metric identified, targeted LLM fix applied, re-evaluated next iteration.</li>
                  <li>5 iterations reached without passing → best-scoring iteration across all 5 (not necessarily the last) is kept.</li>
                  <li>Regression detected → final output rolls back to the best-scoring iteration.</li>
                </ul>
              </div>

            </div>
          </div>
        )}

        {/* ── Footer Navigation ─────────────────────────────────────── */}
        <div className="p-6 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-between">
          <div>
            <p className="text-xs text-white/60">Next Stage in Pipeline: <strong>Final SRS Document (Assembler)</strong></p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate(`/pipeline/${jobId}/lld`)}
              className="px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider border border-white/20 hover:border-white/40 text-white cursor-pointer"
            >
              ← Back to LLD
            </button>
            <button
              onClick={() => navigate(`/pipeline/${jobId}/srs`)}
              className="px-5 py-2 rounded-full text-xs font-bold uppercase tracking-wider bg-cyan-400 text-black hover:bg-cyan-300 cursor-pointer"
            >
              Generate Final SRS Document →
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
