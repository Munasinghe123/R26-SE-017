/**
 * PipelineDashboard.jsx
 *
 * Real-time 5-stage pipeline tracker connected to the Orchestrator SSE stream.
 * Matches the Requirement Agent design system exactly:
 *   - StarBackground (provided by App.jsx)
 *   - Orbitron headings, cyan palette
 *   - Beehive-overlay glassmorphism cards
 *   - GSAP animations
 */

import React, { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ClipboardList,
  Network,
  Code2,
  PanelsTopLeft,
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertTriangle,
  ChevronRight,
} from "lucide-react";
import beehiveBg from "../../../Images/beehive-bg.png";

const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "http://127.0.0.1:8000";

const STAGES = [
  { key: "requirements", label: "Requirements",      icon: ClipboardList, color: "from-cyan-500 to-teal-400" },
  { key: "hld",          label: "Architecture",      icon: Network,       color: "from-violet-500 to-purple-400" },
  { key: "lld",          label: "Low-Level Design",  icon: Code2,         color: "from-blue-500 to-indigo-400" },
  { key: "ui",           label: "UI Prototypes",     icon: PanelsTopLeft, color: "from-pink-500 to-rose-400" },
  { key: "srs",          label: "SRS Document",      icon: FileText,      color: "from-amber-500 to-orange-400" },
];

function StatusIcon({ status }) {
  if (status === "complete")  return <CheckCircle2  className="text-green-400 animate-pulse" size={20} />;
  if (status === "running")   return <Loader2       className="text-cyan-400 animate-spin"   size={20} />;
  if (status === "failed")    return <XCircle       className="text-red-400"                  size={20} />;
  if (status === "needs_review") return <AlertTriangle className="text-amber-400 animate-bounce" size={20} />;
  return <div className="w-5 h-5 rounded-full border border-white/20 bg-white/5" />;
}

function StageCard({ stage, stageData, isActive }) {
  const Icon = stage.icon;
  const status = stageData?.status || "pending";
  const ms     = stageData?.duration_ms;

  return (
    <div
      className={`
        relative flex flex-col items-center gap-2 p-4 rounded-2xl
        border transition-all duration-500
        ${isActive
          ? "border-cyan-400/60 shadow-[0_0_25px_rgba(34,211,238,0.3)] bg-cyan-950/60"
          : status === "complete"
          ? "border-green-400/30 bg-green-950/20"
          : status === "failed"
          ? "border-red-400/30 bg-red-950/20"
          : "border-white/10 bg-white/5"
        }
      `}
    >
      <div className={`p-2.5 rounded-xl bg-gradient-to-br ${stage.color} bg-opacity-20`}>
        <Icon size={22} className="text-white" />
      </div>
      <span className="text-xs font-medium text-white/80 text-center leading-tight">
        {stage.label}
      </span>
      <StatusIcon status={status} />
      {ms && (
        <span className="text-[10px] text-white/40">{(ms / 1000).toFixed(1)}s</span>
      )}
    </div>
  );
}

export default function PipelineDashboard() {
  const { jobId } = useParams();
  const navigate  = useNavigate();
  const [job, setJob]         = useState(null);
  const [stages, setStages]   = useState({});
  const [logs, setLogs]       = useState([]);
  const [event, setEvent]     = useState(null);
  const [architecture, setArchitecture] = useState(null);
  const logsRef = useRef(null);
  const esRef   = useRef(null);

  const addLog = useCallback((msg) =>
    setLogs(prev => [...prev.slice(-49), `${new Date().toLocaleTimeString()} — ${msg}`]),
  []);

  useEffect(() => {
    if (!jobId) return;

    // Fetch initial job state
    fetch(`${ORCHESTRATOR}/jobs/${jobId}`)
      .then(r => r.json())
      .then(data => {
        if (data.job) {
          setJob(data.job);
          const stageMap = {};
          (data.job.stages || []).forEach(s => {
            stageMap[s.stage] = s;
            if (s.status === "complete" || s.status === "running") {
              addLog(`[${s.stage.toUpperCase()}] → ${s.status}${s.duration_ms ? ` (${(s.duration_ms/1000).toFixed(1)}s)` : ""}`);
            }
          });
          setStages(stageMap);
        }
      })
      .catch(() => {});

    // Open SSE stream
    const es = new EventSource(`${ORCHESTRATOR}/jobs/${jobId}/stream`);
    esRef.current = es;

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setEvent(data.event);

      if (data.job) {
        setJob(data.job);
        // Build stages map from array
        const stageMap = {};
        (data.job.stages || []).forEach(s => { stageMap[s.stage] = s; });
        setStages(stageMap);
      }

      if (data.stage) addLog(`[${data.stage.toUpperCase()}] → ${data.status}`);
      if (data.reason) addLog(`⚠ ${data.reason}`);
      if (data.error)  addLog(`✗ Error: ${data.error}`);
      if (data.architecture) setArchitecture(data.architecture);

      if (data.event === "complete") {
        addLog("✓ Pipeline complete! Redirecting to results...");
        setTimeout(() => navigate(`/pipeline/${jobId}/architecture`), 1800);
      }

      if (data.event === "needs_review") {
        addLog("⚠ Architecture quality gate triggered. Review required.");
        setTimeout(() => navigate(`/pipeline/${jobId}/architecture`), 2000);
      }
    };

    es.onerror = () => addLog("SSE connection lost — reconnecting...");

    return () => es.close();
  }, [jobId, navigate, addLog]);

  // Auto-scroll logs
  useEffect(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, [logs]);

  const currentStageIndex = STAGES.findIndex(
    s => s.key === job?.current_stage
  );

  const statusLabel = {
    running:      { text: "RUNNING",      cls: "text-cyan-400" },
    complete:     { text: "COMPLETE",     cls: "text-green-400" },
    failed:       { text: "FAILED",       cls: "text-red-400"  },
    needs_review: { text: "NEEDS REVIEW", cls: "text-amber-400"},
    queued:       { text: "QUEUED",       cls: "text-white/60" },
  };

  const sl = statusLabel[job?.status] || { text: "LOADING...", cls: "text-white/40" };

  // Calculate overall progress %
  const completeCount = STAGES.filter(s =>
    stages[s.key]?.status === "complete"
  ).length;
  const progress = Math.round((completeCount / STAGES.length) * 100);

  return (
    <div className="min-h-screen w-full px-6 pb-20 pt-24 text-white">
      <div className="mx-auto w-full max-w-6xl space-y-8">

        {/* ── Heading ───────────────────────────────────────────────────── */}
        <div className="text-center space-y-2">
          <h1
            className="text-5xl font-bold text-white"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Pipeline <span className="text-cyan-300">Dashboard</span>
          </h1>
          <p className="text-white/50 text-sm tracking-widest uppercase">
            Job ID: <span className="text-cyan-400 font-mono">{jobId}</span>
            &nbsp;&nbsp;·&nbsp;&nbsp;
            Status: <span className={`font-bold ${sl.cls}`}>{sl.text}</span>
          </p>
        </div>

        {/* ── Main Pipeline Card ────────────────────────────────────────── */}
        <div
          className="
            relative w-full overflow-hidden rounded-3xl
            border border-cyan-400/20
            bg-gradient-to-br from-cyan-800/60 via-cyan-950/70 to-black
            shadow-[0_0_60px_rgba(34,211,238,0.20)]
            p-8
          "
        >
          {/* Beehive decorations */}
          <img src={beehiveBg} alt="" className="pointer-events-none absolute -left-20 -top-20 w-72 opacity-10" />
          <img src={beehiveBg} alt="" className="pointer-events-none absolute -bottom-20 -right-20 w-72 rotate-180 opacity-10" />

          {/* Progress bar */}
          <div className="relative z-10 mb-8">
            <div className="flex justify-between text-xs text-white/40 mb-1">
              <span>Overall Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-400 to-teal-300 rounded-full transition-all duration-700"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Stage cards */}
          <div className="relative z-10 grid grid-cols-5 gap-3">
            {STAGES.map((stage, idx) => (
              <React.Fragment key={stage.key}>
                <StageCard
                  stage={stage}
                  stageData={stages[stage.key]}
                  isActive={idx === currentStageIndex && job?.status === "running"}
                />
                {idx < STAGES.length - 1 && (
                  <div className="hidden" /> /* spacer handled by grid gap */
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Connector arrows */}
          <div className="relative z-10 mt-3 flex items-center justify-between px-8">
            {STAGES.map((_, idx) =>
              idx < STAGES.length - 1 ? (
                <ChevronRight
                  key={idx}
                  size={16}
                  className={`mx-auto text-cyan-400/30 transition-all duration-300 ${
                    idx < completeCount ? "text-cyan-400" : ""
                  }`}
                />
              ) : null
            )}
          </div>
        </div>

        {/* ── Live Logs Card ────────────────────────────────────────────── */}
        <div
          className="
            relative w-full overflow-hidden rounded-3xl
            border border-white/10
            bg-black/50 backdrop-blur-md
            shadow-[0_0_30px_rgba(34,211,238,0.05)]
            p-6
          "
        >
          <h2
            className="text-lg font-semibold text-white/70 mb-3 uppercase tracking-widest"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Live Logs
          </h2>
          <div
            ref={logsRef}
            className="h-48 overflow-y-auto font-mono text-xs text-green-300/80 space-y-1 pr-2"
          >
            {logs.length === 0 ? (
              <span className="text-white/30">Waiting for pipeline events...</span>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="opacity-90">{log}</div>
              ))
            )}
          </div>
        </div>

        {/* ── Status-specific Action Cards ─────────────────────────────── */}
        {job?.status === "running" && (
          <div className="relative overflow-hidden rounded-3xl border border-cyan-400/40 bg-gradient-to-br from-cyan-900/30 to-black shadow-[0_0_40px_rgba(34,211,238,0.15)] p-6 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Loader2 className="text-cyan-400 animate-spin" size={24} />
              <div>
                <h2 className="text-xl font-bold text-cyan-300" style={{ fontFamily: "Orbitron, sans-serif" }}>
                  Executing {STAGES[currentStageIndex]?.label || "Pipeline Stage"}...
                </h2>
                <p className="text-white/50 text-sm">Multi-agent models are synthesizing diagrams and architecture in real-time.</p>
              </div>
            </div>
          </div>
        )}

        {job?.status === "waiting_for_hld" && (
          <div className="relative overflow-hidden rounded-3xl border border-cyan-400/40 bg-gradient-to-br from-cyan-900/30 to-black shadow-[0_0_40px_rgba(34,211,238,0.15)] p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-cyan-300" style={{ fontFamily: "Orbitron, sans-serif" }}>Requirements Approved</h2>
              <p className="text-white/50 text-sm">Ready to generate High-Level Design Architecture.</p>
            </div>
            <button onClick={() => fetch(`${ORCHESTRATOR}/jobs/${jobId}/start-hld`, { method: "POST" })} className="flex items-center gap-2 px-5 py-3 text-sm font-medium uppercase tracking-widest text-cyan-900 bg-cyan-400 rounded-full cursor-pointer hover:bg-cyan-300 transition-colors duration-200">
              Generate HLD <ChevronRight size={16} />
            </button>
          </div>
        )}

        {job?.status === "waiting_for_lld_ui" && (
          <div className="relative overflow-hidden rounded-3xl border border-violet-400/40 bg-gradient-to-br from-violet-900/30 to-black shadow-[0_0_40px_rgba(139,92,246,0.15)] p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-violet-300" style={{ fontFamily: "Orbitron, sans-serif" }}>Architecture Generated</h2>
              <p className="text-white/50 text-sm">Review the architecture and confirm to proceed to Low-Level Design.</p>
            </div>
            <button onClick={() => navigate(`/pipeline/${jobId}/architecture`)} className="flex items-center gap-2 px-5 py-3 text-sm font-medium uppercase tracking-widest text-violet-900 bg-violet-400 rounded-full cursor-pointer hover:bg-violet-300 transition-colors duration-200">
              Review Architecture <ChevronRight size={16} />
            </button>
          </div>
        )}

        {job?.status === "waiting_for_ui" && (
          <div className="relative overflow-hidden rounded-3xl border border-blue-400/40 bg-gradient-to-br from-blue-900/30 to-black shadow-[0_0_40px_rgba(59,130,246,0.15)] p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-blue-300" style={{ fontFamily: "Orbitron, sans-serif" }}>Low-Level Design Complete</h2>
              <p className="text-white/50 text-sm">Review the multi-model UML generation and proceed to UI Prototypes.</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => navigate(`/pipeline/${jobId}/lld`)} className="flex items-center gap-2 px-5 py-3 text-sm font-medium uppercase tracking-widest text-white/90 bg-blue-950/80 border border-blue-400/50 rounded-full cursor-pointer hover:bg-blue-900 transition-colors duration-200">
                Review LLD <ChevronRight size={16} />
              </button>
              <button onClick={() => fetch(`${ORCHESTRATOR}/jobs/${jobId}/start-ui`, { method: "POST" })} className="flex items-center gap-2 px-5 py-3 text-sm font-medium uppercase tracking-widest text-blue-900 bg-blue-400 rounded-full cursor-pointer hover:bg-blue-300 transition-colors duration-200">
                Generate UI <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}

        {job?.status === "waiting_for_srs" && (
          <div className="relative overflow-hidden rounded-3xl border border-pink-400/40 bg-gradient-to-br from-pink-900/30 to-black shadow-[0_0_40px_rgba(236,72,153,0.15)] p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-pink-300" style={{ fontFamily: "Orbitron, sans-serif" }}>UI Prototypes Complete</h2>
              <p className="text-white/50 text-sm">Review the interactive UI prototypes or assemble the final SRS.</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => navigate(`/pipeline/${jobId}/ui`)} className="flex items-center gap-2 px-5 py-3 text-sm font-medium uppercase tracking-widest text-white/90 bg-pink-950/80 border border-pink-400/50 rounded-full cursor-pointer hover:bg-pink-900 transition-colors duration-200">
                Review UI <ChevronRight size={16} />
              </button>
              <button onClick={() => fetch(`${ORCHESTRATOR}/jobs/${jobId}/start-srs`, { method: "POST" })} className="flex items-center gap-2 px-5 py-3 text-sm font-medium uppercase tracking-widest text-pink-900 bg-pink-400 rounded-full cursor-pointer hover:bg-pink-300 transition-colors duration-200">
                Assemble SRS <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}

        {job?.status === "needs_review" && (
          <div
            className="
              relative overflow-hidden rounded-3xl
              border border-amber-400/40
              bg-gradient-to-br from-amber-900/30 to-black
              shadow-[0_0_40px_rgba(245,158,11,0.15)]
              p-6
            "
          >
            <div className="flex items-center gap-3 mb-2">
              <AlertTriangle className="text-amber-400" size={24} />
              <h2
                className="text-xl font-bold text-amber-300"
                style={{ fontFamily: "Orbitron, sans-serif" }}
              >
                Architecture Review Required
              </h2>
            </div>
            <p className="text-white/60 text-sm mb-4">
              The Composite Architecture Score did not meet the quality threshold.
              Review the metrics and decide whether to accept or request regeneration.
            </p>
            <button
              onClick={() => navigate(`/pipeline/${jobId}/architecture`)}
              className="
                flex items-center gap-2 px-5 py-3
                text-sm font-medium uppercase tracking-widest
                text-amber-900 bg-amber-400
                rounded-full cursor-pointer
                hover:bg-amber-300 transition-colors duration-200
              "
            >
              Review Architecture <ChevronRight size={16} />
            </button>
          </div>
        )}

        {job?.status === "complete" && (
          <div
            className="
              relative overflow-hidden rounded-3xl
              border border-green-400/40
              bg-gradient-to-br from-green-900/30 to-black
              shadow-[0_0_40px_rgba(34,197,94,0.15)]
              p-6 flex items-center justify-between
            "
          >
            <div className="flex items-center gap-3">
              <CheckCircle2 className="text-green-400" size={28} />
              <div>
                <h2
                  className="text-xl font-bold text-green-300"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  Pipeline Complete
                </h2>
                <p className="text-white/50 text-sm">All artifacts generated successfully</p>
              </div>
            </div>
            <button
              onClick={() => navigate(`/pipeline/${jobId}/artifacts`)}
              className="
                flex items-center gap-2 px-5 py-3
                text-sm font-medium uppercase tracking-widest
                text-green-900 bg-green-400
                rounded-full cursor-pointer
                hover:bg-green-300 transition-colors duration-200
              "
            >
              View Artifacts <ChevronRight size={16} />
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
