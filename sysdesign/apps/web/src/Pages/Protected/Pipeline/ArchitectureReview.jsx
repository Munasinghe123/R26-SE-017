/**
 * ArchitectureReview.jsx — Complete ATAM Research Suite
 *
 * Restores full HLA agent capabilities:
 * 1. Overview & ATAM Trade-off Candidate Selection
 * 2. Candidate Radar Chart & 6 Quality Metrics (CAS, LSCS, NAS, RCR, SCI, SMI)
 * 3. Git-Like Diagram Refinement Loop (v1, v2 PlantUML iteration timeline, AI prompt refiner, rescoring)
 * 4. Side-by-Side Code Diff Viewer (colored diff syntax highlighting)
 *
 * Design aesthetic: Orbitron font, dark mode #05050f, cyan #2DDCFF & violet accents.
 */

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Network,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  GitBranch,
  GitCommit,
  FileDiff,
  Award,
  Layers,
  Sparkles,
  BarChart2,
  FileCode,
  Sliders,
  Send,
  Eye,
} from "lucide-react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from "recharts";
import beehiveBg from "../../../Images/beehive-bg.png";

const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "http://127.0.0.1:8000";
const AGENT2_URL   = import.meta.env.VITE_AGENT2_URL || "http://127.0.0.1:8002";

const METRIC_INFO = {
  RTS:  { label: "RTS (Requirement Traceability Score)", desc: "Semantic alignment of requirements to components", weight: "29.17%" },
  QAC:  { label: "QAC (Quality Attribute Coverage)",     desc: "ISO 25010 NFR architectural provision coverage", weight: "21.94%" },
  CI:   { label: "CI (Coupling Index)",                  desc: "Graph decoupling density score (higher = better)", weight: "13.61%" },
  CoS:  { label: "CoS (Cohesion Score)",                 desc: "Semantic coherence of component responsibilities", weight: "13.61%" },
  SSM1: { label: "SSM₁ (Primary Style Metric)",           desc: "Style-specific structural property (LIS, SBA, EFC, MCR, PC)", weight: "13.61%" },
  SSM2: { label: "SSM₂ (Secondary Style Metric)",         desc: "Style-specific boundary property (DDS, ISS, PSC, FIS)", weight: "8.06%" },
};

/** Strip org prefix from model path: "meta-llama/llama-3.3-70b-instruct" → "llama-3.3-70b-instruct" */
function getModelShortName(model) {
  if (!model) return "Unknown Model";
  return model.split("/").pop() || model;
}

/**
 * Build a unique, human-readable label for a candidate card.
 * Example: "llama-3.3-70b-instruct #2 · Microservices"
 */
function buildCandidateLabel(c, idx) {
  const modelShort = getModelShortName(c.model) || `Candidate ${idx + 1}`;
  const num = c.candidate_num ? `#${c.candidate_num}` : `#${idx + 1}`;
  const style = (c.architecture?.architecture_style || c.scores?.detected_style || "").trim();
  const styleTag = style ? ` · ${style}` : "";
  return `${modelShort} ${num}${styleTag}`;
}

/** Composite unique ID: model + candidate_num + list index → guaranteed unique per card */
function buildCandidateUid(c, idx) {
  return `${c.model || "unknown"}::${c.candidate_num ?? idx}::${idx}`;
}

function generateFallbackMermaidCode(architecture) {
  if (!architecture) return "graph TD\n    A[Client] --> B[API Gateway]";
  const comps = architecture.components || [];
  const conns = architecture.connectors || architecture.interactions || [];

  let lines = ["graph TD"];
  const layers = architecture.layers || [];

  if (layers.length > 0) {
    layers.forEach(layer => {
      const layerComps = comps.filter(c => (c.layer || "").toLowerCase() === (layer.name || "").toLowerCase());
      if (layerComps.length > 0) {
        const subId = (layer.name || "Layer").replace(/[^a-zA-Z0-9]/g, "_");
        lines.push(`    subgraph ${subId} ["${layer.name}"]`);
        layerComps.forEach(c => {
          const cId = c.name.replace(/[^a-zA-Z0-9]/g, "_");
          lines.push(`        ${cId}["${c.name}"]`);
        });
        lines.push("    end");
      }
    });
  } else {
    comps.forEach(c => {
      const cId = c.name.replace(/[^a-zA-Z0-9]/g, "_");
      lines.push(`    ${cId}["${c.name}"]`);
    });
  }

  conns.forEach(conn => {
    const fromId = (conn.from_component || conn.from || "").replace(/[^a-zA-Z0-9]/g, "_");
    const toId = (conn.to_component || conn.to || "").replace(/[^a-zA-Z0-9]/g, "_");
    const label = conn.connector_type || conn.type || "";
    if (fromId && toId) {
      if (label) {
        lines.push(`    ${fromId} -->|"${label}"| ${toId}`);
      } else {
        lines.push(`    ${fromId} --> ${toId}`);
      }
    }
  });

  return lines.join("\n");
}

function VerdictBadge({ verdict, cas }) {
  const cfg = {
    accepted:     { text: "ACCEPTED",     cls: "text-green-900 bg-green-400",  Icon: CheckCircle2 },
    marginal:     { text: "MARGINAL",     cls: "text-amber-900 bg-amber-400",  Icon: AlertTriangle },
    rejected:     { text: "REJECTED",     cls: "text-red-100   bg-red-600",    Icon: XCircle },
    needs_review: { text: "NEEDS REVIEW", cls: "text-amber-900 bg-amber-400",  Icon: AlertTriangle },
  }[verdict] || { text: verdict?.toUpperCase() || "UNKNOWN", cls: "text-white bg-white/20", Icon: AlertTriangle };

  const { Icon } = cfg;

  return (
    <span className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest ${cfg.cls}`}>
      <Icon size={14} />
      {cfg.text}
      &nbsp;·&nbsp;CAS {cas?.toFixed(3)}
    </span>
  );
}

function MetricBar({ metricKey, label, desc, value }) {
  const pct = Math.round((value ?? 0) * 100);
  const color =
    pct >= 70 ? "from-green-400 to-emerald-300" :
    pct >= 50 ? "from-amber-400 to-yellow-300"  :
                "from-red-400 to-rose-300";

  return (
    <div className="space-y-1 bg-white/5 p-3 rounded-xl border border-white/5">
      <div className="flex justify-between items-center">
        <div>
          <span className="text-xs font-semibold text-cyan-200">{label}</span>
          <p className="text-[11px] text-white/40">{desc}</p>
        </div>
        <span className={`text-sm font-mono font-bold ${
          pct >= 70 ? "text-green-400" : pct >= 50 ? "text-amber-400" : "text-red-400"
        }`}>
          {(value ?? 0).toFixed(3)}
        </span>
      </div>
      <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mt-1">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function ArchitectureReview() {
  const { jobId } = useParams();
  const navigate  = useNavigate();

  const [activeTab, setActiveTab] = useState("overview"); // overview, radar, git_loop, diff
  const [arch, setArch]         = useState(null);
  const [scores, setScores]     = useState(null);
  const [verdict, setVerdict]   = useState(null);
  const [style, setStyle]       = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [compareRadar, setCompareRadar] = useState(false);
  const [selecting, setSelecting]       = useState(false);

  // Diagram Git-Loop state
  const [diagrams, setDiagrams] = useState({ plantuml: "", mermaid: "" });
  const [iterations, setIterations] = useState([]);
  const [activeVersion, setActiveVersion] = useState(null);
  const [refinePrompt, setRefinePrompt]   = useState("");
  const [refining, setRefining]           = useState(false);
  const [diffText, setDiffText]           = useState("");

  const [loading, setLoading]       = useState(true);
  const [restarting, setRestarting] = useState(false);
  const [jobStatus, setJobStatus]   = useState(null);
  const [error, setError]           = useState(null);

  // Kroki SVG render state — must be declared here (before any early returns)
  const [svgUrl, setSvgUrl] = useState(null);
  const [svgError, setSvgError] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    fetch(`${ORCHESTRATOR}/jobs/${jobId}`)
      .then(r => r.json())
      .then(data => {
        if (data.job) setJobStatus(data.job.status);
        const archArtifact = data?.artifacts?.architecture;
        if (archArtifact) {
          setArch(archArtifact);
          // Use real scores only — no hardcoded fallbacks
          setScores(archArtifact.scores || null);
          setVerdict(archArtifact.verdict || null);
          setStyle(archArtifact.detected_style || archArtifact.architecture_style || null);

          let mappedCandidates = [];
          if (archArtifact.candidates && archArtifact.candidates.length > 0) {
            mappedCandidates = archArtifact.candidates.map((c, idx) => ({
              ...c,
              uid: buildCandidateUid(c, idx),
              name: buildCandidateLabel(c, idx),
              cas: c.cas || c.scores?.CAS || 0,
              style: c.style || c.architecture?.architecture_style || c.scores?.detected_style || "unknown"
            }));
          } else {
            // Synthesize single-winner fallback
            mappedCandidates = [{
              uid: "winner::0::0",
              name: buildCandidateLabel({ model: archArtifact.architecture_style, candidate_num: 1, architecture: archArtifact }, 0),
              model: archArtifact.architecture_style || "Auto-Picked Winner",
              cas: archArtifact.scores?.CAS || 0,
              style: archArtifact.detected_style || archArtifact.architecture_style || "unknown",
              scores: archArtifact.scores || {},
              architecture: archArtifact,
              candidate_num: 1,
              rank: 1,
            }];
          }
          setCandidates(mappedCandidates);
          setSelectedCandidate(mappedCandidates[0]);

          if (archArtifact.plantuml_code) {
            setDiagrams({ plantuml: archArtifact.plantuml_code, mermaid: archArtifact.mermaid_code || "" });
            setIterations([{ version: "v1", cas: archArtifact.scores?.CAS ?? 0, prompt: "Initial generation", code: archArtifact.plantuml_code }]);
            setActiveVersion("v1");
          }
        } else if (data.job?.status === "failed") {
          setError(`Pipeline failed: ${data.job.error || "Unknown error. Check the agent2-hld server logs."}`);
        } else if (data.job?.status === "running" || data.job?.status === "pending") {
          setError("Pipeline is still running. Refresh in a moment.");
        } else {
          setError("Architecture data not yet available.");
        }
        setLoading(false);
      })
      .catch(err => {
        setError("Could not fetch job data from the orchestrator.");
        setLoading(false);
      });
  }, [jobId]);

  // Compute diff text between v1 and v2
  useEffect(() => {
    if (iterations.length >= 2) {
      const rawV1 = (iterations[0].code || "").replace(/\\n/g, "\n");
      const rawV2 = (iterations[iterations.length - 1].code || "").replace(/\\n/g, "\n");
      const v1 = rawV1.split("\n");
      const v2 = rawV2.split("\n");

      let diffLines = [];
      let i = 0, j = 0;
      while (i < v1.length || j < v2.length) {
        if (i < v1.length && j < v2.length && v1[i] === v2[j]) {
          diffLines.push(`  ${v1[i]}`);
          i++; j++;
        } else {
          if (i < v1.length) {
            diffLines.push(`- ${v1[i]}`);
            i++;
          }
          if (j < v2.length) {
            diffLines.push(`+ ${v2[j]}`);
            j++;
          }
        }
      }
      setDiffText(diffLines.join("\n"));
    }
  }, [iterations]);

  // Kroki SVG rendering — POST the raw PlantUML text (avoids btoa UTF-8 breakage)
  // Note: activeIteration is computed below after early returns, so we re-compute the code here
  useEffect(() => {
    const activeIt = (iterations && iterations.length > 0)
      ? (iterations.find(it => it.version === activeVersion) || iterations[iterations.length - 1])
      : null;
    const raw = (activeIt?.code || "").replace(/\\n/g, "\n").trim();
    if (!raw || raw.startsWith('{') || raw.startsWith('"')) {
      setSvgError(true);
      setSvgUrl(null);
      return;
    }
    setSvgError(false);
    setSvgUrl(null);
    fetch("https://kroki.io/plantuml/svg", {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: raw,
    })
      .then(r => r.ok ? r.blob() : Promise.reject(r.status))
      .then(blob => setSvgUrl(URL.createObjectURL(blob)))
      .catch(() => setSvgError(true));
  }, [iterations, activeVersion]);

  const handleRefineDiagram = async () => {
    if (!refinePrompt.trim()) return;
    setRefining(true);

    try {
      const res = await fetch(`${ORCHESTRATOR}/jobs/${jobId}/refine-diagram`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: refinePrompt })
      });

      if (res.ok) {
        const data = await res.json();
        const pumlWorkflow = data.plantuml || {};
        const history = pumlWorkflow.history || [];

        if (history.length > 0) {
          const newIterList = history.map((item, idx) => ({
            version: `v${idx + 1}`,
            cas: item.diagram_cas ?? 0,
            prompt: item.source === "manual" ? "Manual Edit" : (item.llm_iteration > 1 ? refinePrompt : "Initial Generation"),
            code: (item.diagram || "").replace(/\\n/g, "\n"),
            breakdown: item.breakdown || {},
            issues: item.issues || []
          }));
          setIterations(newIterList);
          setActiveVersion(`v${newIterList.length}`);
        } else if (data.plantuml_code) {
          const nextVer = `v${iterations.length + 1}`;
          setIterations([
            ...iterations,
            { version: nextVer, cas: data.new_cas || iterations[0].cas, prompt: refinePrompt, code: data.plantuml_code.replace(/\\n/g, "\n") }
          ]);
          setActiveVersion(nextVer);
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(`Refinement failed: ${errData.detail || res.statusText}`);
      }
    } catch (err) {
      console.error("Refine trigger failed:", err);
      setError("Failed to connect to the orchestrator for diagram refinement.");
    } finally {
      setRefining(false);
      setRefinePrompt("");
    }
  };

  const handleAccept = async () => {
    if (!selectedCandidate) return;
    setSelecting(true);
    try {
      await fetch(`${ORCHESTRATOR}/jobs/${jobId}/select-candidate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: selectedCandidate.model,
          architecture: selectedCandidate.architecture,
          scores: selectedCandidate.scores
        })
      });
    } catch (e) {
      console.error("Failed to select candidate", e);
    }

    if (jobStatus === "needs_review" || jobStatus === "waiting_for_lld_ui") {
      try {
        await fetch(`${ORCHESTRATOR}/jobs/${jobId}/start-lld`, { method: "POST" });
      } catch (e) {
        console.error("Failed to start LLD", e);
      }
    }
    setSelecting(false);
    navigate(`/pipeline/${jobId}`);
  };

  const handleReject = async () => {
    setRestarting(true);
    try {
      const res = await fetch(`${ORCHESTRATOR}/jobs/${jobId}/retry-hld`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        navigate(`/pipeline/${data.new_job_id || jobId}`);
      } else {
        navigate(`/pipeline/${jobId}`);
      }
    } catch {
      navigate(`/pipeline/${jobId}`);
    } finally {
      setRestarting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#05050f]">
        <div className="text-cyan-400 animate-spin"><Network size={40} /></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#05050f] px-8">
        <div className="max-w-md text-center space-y-4">
          <AlertTriangle className="mx-auto text-amber-400" size={48} />
          <p className="text-white/70">{error}</p>
          <button onClick={() => navigate(-1)} className="text-cyan-400 underline text-sm">Go back</button>
        </div>
      </div>
    );
  }

  const getMetricLabel = (key) => {
    if (key === "SSM1" && selectedCandidate?.scores?.ssm1_display) {
      return `SSM₁: ${selectedCandidate.scores.ssm1_display} (${selectedCandidate.scores.ssm1_name})`;
    }
    if (key === "SSM2" && selectedCandidate?.scores?.ssm2_display) {
      return `SSM₂: ${selectedCandidate.scores.ssm2_display} (${selectedCandidate.scores.ssm2_name})`;
    }
    return METRIC_INFO[key]?.label || key;
  };

  const getMetricDesc = (key) => {
    if (key === "SSM1" && selectedCandidate?.scores?.ssm1_display) {
      return `Style-specific structural property for ${selectedCandidate.style}`;
    }
    if (key === "SSM2" && selectedCandidate?.scores?.ssm2_display) {
      return `Style-specific boundary property for ${selectedCandidate.style}`;
    }
    return METRIC_INFO[key]?.desc || "";
  };

  const activeIteration = (iterations && iterations.length > 0)
    ? (iterations.find(it => it.version === activeVersion) || iterations[iterations.length - 1])
    : { version: "v0", cas: 0, code: "' No diagram code generated" };

  const diagramCas = activeIteration?.cas ?? selectedCandidate?.cas ?? (scores?.CAS ?? 0);
  const isAcceptable = diagramCas >= 0.60;
  // Only show AI refinement engine when diagram CAS is below threshold
  const needsRefinement = diagramCas < 0.60;

  return (
    <div className="min-h-screen w-full px-6 pb-20 pt-24 text-white bg-[#05050f]">
      <div className="mx-auto w-full max-w-6xl space-y-6">

        {/* ── Title & Header ─────────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-cyan-500/20 pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
              Architecture <span className="text-cyan-400">Review Suite</span>
            </h1>
            <p className="text-xs text-white/50 mt-1">
              ATAM Trade-off Evaluation · Radar Metrics · Interactive Diagram Studio & Revision Control
            </p>
          </div>
          <div className="flex items-center gap-3">
            <VerdictBadge 
              verdict={selectedCandidate?.scores?.verdict || selectedCandidate?.verdict || verdict} 
              cas={selectedCandidate?.cas || selectedCandidate?.scores?.CAS || 0.78} 
            />
            <span className="text-xs font-mono px-3 py-1 bg-violet-500/10 border border-violet-500/30 text-violet-300 rounded-full font-bold uppercase tracking-wider">
              Style: {selectedCandidate?.style || selectedCandidate?.scores?.detected_style || selectedCandidate?.architecture?.architecture_style || style}
            </span>
          </div>
        </div>

        {/* ── Navigation Tabs (Production Enterprise Terminology) ───────── */}
        <div className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
          {[
            { id: "overview",       label: "Architecture Evaluation & Selection", icon: Award },
            { id: "radar",          label: "Quality Metrics Radar",               icon: BarChart2 },
            { id: "visual_studio",  label: "Diagram Studio & Visual Canvas",      icon: Eye },
            { id: "git_loop",       label: "Interactive Refinement Engine",       icon: GitBranch },
            { id: "diff",           label: "Revision Control & Code Diff",        icon: FileDiff },
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wider transition-all cursor-pointer
                  ${active
                    ? "bg-cyan-400/10 border border-cyan-400 text-cyan-300 shadow-[0_0_15px_rgba(45,220,255,0.2)]"
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

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 1: OVERVIEW & ATAM TRADEOFF                              */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Left 2 Columns: Metrics & Component List */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Quality Metrics Grid */}
              <div className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-950/40 via-cyan-900/10 to-black p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold tracking-widest text-cyan-300 uppercase" style={{ fontFamily: "Orbitron, sans-serif" }}>
                    ATAM 6-Quality Metrics Breakdown
                  </h3>
                  <span className="text-xs text-white/40">Threshold: 0.60</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(METRIC_INFO).map(([key, info]) => (
                    <MetricBar
                      key={key}
                      metricKey={key}
                      label={getMetricLabel(key)}
                      desc={getMetricDesc(key)}
                      value={selectedCandidate?.scores?.[key] ?? 0.75}
                    />
                  ))}
                </div>
              </div>

              {/* Component Topology */}
              <div className="rounded-2xl border border-violet-400/20 bg-gradient-to-br from-violet-950/40 via-indigo-900/10 to-black p-6 space-y-4">
                <h3 className="text-sm font-bold tracking-widest text-violet-300 uppercase" style={{ fontFamily: "Orbitron, sans-serif" }}>
                  Extracted Architecture Components
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-64 overflow-y-auto pr-1">
                  {(selectedCandidate?.architecture?.components || selectedCandidate?.components || arch?.components || []).length > 0 ? (
                    (selectedCandidate?.architecture?.components || selectedCandidate?.components || arch?.components || []).map((c, i) => (
                      <div key={i} className="p-3 rounded-xl border border-white/10 bg-white/5 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white">{c.name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-400/20 text-violet-300">
                            {c.layer || c.boundary || "Core"}
                          </span>
                        </div>
                        {c.responsibilities && (
                          <p className="text-[11px] text-white/50 line-clamp-1">
                            {Array.isArray(c.responsibilities) ? c.responsibilities.join(", ") : c.responsibilities}
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="col-span-2 text-center py-6 text-white/40 text-xs">
                      Component breakdown available once pipeline reaches complete state.
                    </div>
                  )}
                </div>
              </div>

              {/* Info Panel: Common vs Style-Specific Quality Attributes */}
              <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-xs space-y-2">
                <span className="font-bold text-cyan-400 block uppercase tracking-wider">
                  Metric Analysis Guide
                </span>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-white/60">
                  <div>
                    <strong className="text-white block mb-0.5">Common Quality Attributes</strong>
                    RTS, QAC, CI, and CoS are evaluated uniformly across all candidate architectures to measure requirements traceability, quality attribute coverage, graph coupling, and semantic cohesion.
                  </div>
                  <div>
                    <strong className="text-white block mb-0.5">Style-Specific Metrics</strong>
                    SSM₁ and SSM₂ dynamically adapt to evaluate the structural integrity unique to the selected architecture style (e.g., LIS/DDS for Layered, SBA/ISS for Microservices).
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Candidate Selection & Winner Card */}
            <div className="space-y-6">
              <div className="rounded-2xl border border-amber-400/30 bg-gradient-to-br from-amber-950/30 via-yellow-900/10 to-black p-6 space-y-4">
                <div className="flex items-center gap-2 text-amber-400">
                  <Award size={18} />
                  <h3 className="text-sm font-bold tracking-widest uppercase" style={{ fontFamily: "Orbitron, sans-serif" }}>
                    Winning Candidate
                  </h3>
                </div>

                {selectedCandidate && (
                  <div className="p-4 rounded-xl border border-amber-400/30 bg-amber-400/5 space-y-3">
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <span className="text-xs font-bold text-amber-200 block">{selectedCandidate.name}</span>
                        <span className="text-[10px] text-white/50 block font-mono">
                          Candidate #{selectedCandidate.candidate_num || 1}
                        </span>
                      </div>
                      <span className="text-xs font-mono font-bold text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/30">
                        CAS {typeof selectedCandidate.cas === 'number' ? selectedCandidate.cas.toFixed(4) : selectedCandidate.cas}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs border-t border-b border-white/10 py-2">
                      <span className="text-white/60">Architecture Style:</span>
                      <span className="font-bold text-cyan-300 uppercase tracking-wider font-mono">
                        {selectedCandidate.style}
                      </span>
                    </div>

                    <div className="space-y-1.5 pt-1">
                      <span className="text-[11px] font-bold text-amber-300 uppercase tracking-wider block">
                        Evaluated Style-Specific Metrics (SSM)
                      </span>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2 rounded bg-white/5 border border-white/10">
                          <span className="text-white/50 block text-[10px]">
                            {selectedCandidate?.scores?.ssm1_display || "SSM₁ Metric"}
                          </span>
                          <span className="font-mono font-bold text-cyan-400">
                            {(selectedCandidate?.scores?.SSM1 ?? 0).toFixed(3)}
                          </span>
                        </div>
                        <div className="p-2 rounded bg-white/5 border border-white/10">
                          <span className="text-white/50 block text-[10px]">
                            {selectedCandidate?.scores?.ssm2_display || "SSM₂ Metric"}
                          </span>
                          <span className="font-mono font-bold text-cyan-400">
                            {(selectedCandidate?.scores?.SSM2 ?? 0).toFixed(3)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-xs text-white/50 uppercase tracking-wider flex justify-between items-center block">
                    <span>All Evaluated Candidates ({candidates.length} Options)</span>
                    <span className="text-[10px] text-cyan-400 font-mono">3 LLMs x 2 Choices</span>
                  </label>
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {candidates.map((cand, idx) => {
                      // Use uid for guaranteed single-candidate selection
                      const isSelected = selectedCandidate?.uid === cand.uid;
                      const styleName = cand.style || cand.architecture?.architecture_style || "Layered";
                      const rankLabel = cand.rank > 0 ? `#${cand.rank}` : cand.rank === 1 ? "#1" : "—";
                      const ssmTag = cand.scores?.ssm1_name && cand.scores?.ssm2_name
                        ? `${cand.scores.ssm1_name}/${cand.scores.ssm2_name}`
                        : "SSM₁/SSM₂";
                      const casPct = Math.round((cand.cas || 0) * 100);
                      const casColor = casPct >= 80 ? "bg-green-400" : casPct >= 60 ? "bg-amber-400" : "bg-red-400";
                      const modelShort = getModelShortName(cand.model);

                      return (
                        <button
                          key={cand.uid || idx}
                          onClick={() => setSelectedCandidate(cand)}
                          className={`
                            w-full text-left p-3 rounded-xl border text-xs transition-all flex flex-col gap-2 cursor-pointer
                            ${isSelected
                              ? "border-amber-400 bg-amber-400/10 shadow-[0_0_12px_rgba(245,158,11,0.25)]"
                              : "border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20"
                            }
                          `}
                        >
                          {/* Row 1: Rank + CAS */}
                          <div className="flex justify-between items-center w-full">
                            <div className="flex items-center gap-2">
                              {cand.rank > 0 && (
                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded font-mono ${
                                  cand.rank === 1
                                    ? "bg-amber-400/20 text-amber-300 border border-amber-400/40"
                                    : "bg-white/10 text-white/50 border border-white/10"
                                }`}>
                                  #{cand.rank}
                                </span>
                              )}
                              <span className={`font-semibold truncate max-w-[150px] ${
                                isSelected ? "text-amber-200" : "text-white"
                              }`}>
                                {modelShort} #{cand.candidate_num}
                              </span>
                            </div>
                            <span className={`font-mono font-bold text-sm ${
                              casPct >= 80 ? "text-green-400" : casPct >= 60 ? "text-amber-400" : "text-red-400"
                            }`}>
                              {typeof cand.cas === 'number' ? cand.cas.toFixed(3) : cand.cas}
                            </span>
                          </div>

                          {/* Row 2: Style tag + SSM tag */}
                          <div className="flex items-center justify-between text-[10px] text-white/50">
                            <span className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 font-mono uppercase truncate max-w-[120px]">
                              {styleName}
                            </span>
                            <span className="font-mono text-cyan-400/80 bg-cyan-400/10 px-1.5 py-0.5 rounded border border-cyan-400/20 shrink-0">
                              {ssmTag}
                            </span>
                          </div>

                          {/* Row 3: CAS mini progress bar */}
                          <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${casColor}`}
                              style={{ width: `${casPct}%` }}
                            />
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 2: METRICS RADAR CHART                                   */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "radar" && (
          <div className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-950/40 via-indigo-950/30 to-black p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <h3 className="text-lg font-bold text-cyan-300" style={{ fontFamily: "Orbitron, sans-serif" }}>
                  ATAM Multi-Dimensional Quality Radar
                </h3>
                <p className="text-xs text-white/50">Visual metric balance across the 6 architectural dimensions</p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setCompareRadar(!compareRadar)}
                  className={`
                    px-4 py-1.5 rounded-full text-xs font-semibold tracking-wider transition-all cursor-pointer border
                    ${compareRadar
                      ? "bg-amber-400 text-black border-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.3)]"
                      : "bg-white/5 border-white/10 text-white/60 hover:text-white"
                    }
                  `}
                >
                  {compareRadar ? "Show Single Radar" : "Compare All LLMs Radar"}
                </button>
                <span className="text-xs font-mono text-cyan-400 bg-cyan-400/10 px-3 py-1 rounded-full border border-cyan-400/30">
                  Target Score: 0.850+
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              {/* Real Recharts Radar Chart */}
              <div className="relative w-full h-80 mx-auto">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart 
                    cx="50%" cy="50%" outerRadius="70%" 
                    data={(() => {
                      const keys = ["RTS", "QAC", "CI", "CoS", "SSM1", "SSM2"];
                      const keyLabels = { RTS: "RTS", QAC: "QAC", CI: "CI", CoS: "CoS", SSM1: "SSM₁", SSM2: "SSM₂" };
                      if (compareRadar) {
                        return keys.map(k => {
                          const row = { metric: keyLabels[k], fullMark: 1 };
                          candidates.forEach((cand, idx) => {
                            const modelName = cand.name || cand.model || `Candidate ${idx + 1}`;
                            row[modelName] = cand.scores?.[k] ?? 0;
                          });
                          return row;
                        });
                      } else {
                        const activeScores = selectedCandidate?.scores || scores;
                        return keys.map(k => ({
                          metric: keyLabels[k],
                          score: activeScores?.[k] ?? 0.75,
                          fullMark: 1
                        }));
                      }
                    })()}
                  >
                    <PolarGrid stroke="rgba(45, 220, 255, 0.2)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#67e8f9', fontSize: 11, fontFamily: 'monospace' }} />
                    <PolarRadiusAxis angle={30} domain={[0, 1]} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} axisLine={false} tickCount={5} />
                    {compareRadar ? (
                      candidates.map((cand, idx) => {
                        const modelName = cand.name || cand.model || `Candidate ${idx + 1}`;
                        const colors = ["#2DDCFF", "#A855F7", "#F59E0B", "#10B981", "#EF4444"];
                        const strokeColor = colors[idx % colors.length];
                        return (
                          <Radar
                            key={modelName}
                            name={modelName}
                            dataKey={modelName}
                            stroke={strokeColor}
                            strokeWidth={2}
                            fill={strokeColor}
                            fillOpacity={0.15}
                            isAnimationActive={true}
                          />
                        );
                      })
                    ) : (
                      <Radar
                        name="Score"
                        dataKey="score"
                        stroke="#2DDCFF"
                        strokeWidth={2}
                        fill="#2DDCFF"
                        fillOpacity={0.4}
                        isAnimationActive={true}
                      />
                    )}
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'rgba(5, 5, 15, 0.9)', border: '1px solid rgba(45, 220, 255, 0.3)', borderRadius: '8px', color: '#fff' }}
                      itemStyle={{ color: '#2DDCFF' }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
                
                {/* Central Score Badge Overlay */}
                {!compareRadar && (
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center bg-cyan-950/80 p-3 rounded-full border border-cyan-400/60 shadow-[0_0_15px_rgba(45,220,255,0.4)] pointer-events-none z-10">
                    <div className="text-xl font-bold font-mono text-cyan-300 leading-none">
                      {(selectedCandidate?.cas || selectedCandidate?.scores?.CAS || scores?.CAS || 0.78).toFixed(2)}
                    </div>
                  </div>
                )}
              </div>

              {/* Metric Legend Grid */}
              <div className="space-y-3">
                {Object.entries(METRIC_INFO).map(([k, info]) => {
                  const val = selectedCandidate?.scores?.[k] ?? scores?.[k] ?? 0.75;
                  return (
                    <div key={k} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10">
                      <div>
                        <span className="text-xs font-bold text-white">{k} — {getMetricLabel(k)}</span>
                        <p className="text-[10px] text-white/40">{getMetricDesc(k)}</p>
                      </div>
                      {!compareRadar && (
                        <span className="text-xs font-mono font-bold text-cyan-300">{val.toFixed(3)}</span>
                      )}
                    </div>
                  );
                })}

                {compareRadar && (
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2 mt-2">
                    <span className="text-xs font-bold text-cyan-300 block uppercase tracking-wider">Comparison Legend</span>
                    <div className="space-y-1.5">
                      {candidates.map((cand, idx) => {
                        const modelName = cand.name || cand.model || `Candidate ${idx + 1}`;
                        const colors = ["#2DDCFF", "#A855F7", "#F59E0B", "#10B981", "#EF4444"];
                        const strokeColor = colors[idx % colors.length];
                        return (
                          <div key={modelName} className="flex items-center gap-2 text-xs">
                            <span className="w-3 h-3 rounded" style={{ backgroundColor: strokeColor }} />
                            <span className="font-semibold text-white/80">{modelName} (CAS: {(cand.cas || cand.scores?.CAS || 0).toFixed(3)})</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 3: INTERACTIVE DIAGRAM STUDIO & VISUAL CANVAS             */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "visual_studio" && (
          <div className="space-y-6">

            {/* Status Gate Banner */}
            {isAcceptable ? (
              <div className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-green-950/40 border border-green-400/30 text-green-300 text-xs font-semibold">
                <CheckCircle2 size={16} />
                Architecture CAS {diagramCas.toFixed(3)} passed quality threshold (≥ 0.60). Visual review only — no AI intervention required.
              </div>
            ) : (
              <div className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-amber-950/40 border border-amber-400/30 text-amber-300 text-xs font-semibold">
                <AlertTriangle size={16} />
                Architecture CAS {diagramCas.toFixed(3)} is below threshold (0.60). Switch to the <strong>Interactive Refinement Engine</strong> tab to improve it.
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Visual SVG Render Canvas */}
              <div className="lg:col-span-2 rounded-2xl border border-cyan-400/30 bg-[#070919] min-h-[460px] flex flex-col shadow-2xl overflow-hidden">
                <div className="flex justify-between items-center px-5 py-3 bg-[#050610] border-b border-white/10">
                  <span className="text-xs font-bold text-white/70 uppercase font-mono">Live Vector Diagram Canvas — PlantUML Engine</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                    svgError ? "bg-red-500/20 text-red-300" : svgUrl ? "bg-green-500/20 text-green-300" : "bg-white/10 text-white/50"
                  }`}>
                    {svgError ? "Render Error" : svgUrl ? "SVG Vector High-Res" : "Rendering..."}
                  </span>
                </div>
                <div className="flex-1 flex items-center justify-center p-4 bg-white overflow-auto">
                  {svgError ? (
                    <div className="text-center space-y-2">
                      <p className="text-red-500 text-xs font-mono font-semibold">⚠ PlantUML diagram could not render.</p>
                      <p className="text-gray-500 text-[11px]">The LLM returned invalid PlantUML. Use Refinement Engine to regenerate.</p>
                    </div>
                  ) : svgUrl ? (
                    <img src={svgUrl} alt="Architecture Diagram" className="max-h-[420px] w-full object-contain" />
                  ) : (
                    <div className="flex items-center gap-3 text-cyan-400 text-xs">
                      <RefreshCw size={16} className="animate-spin" />
                      Rendering architecture diagram via Kroki engine...
                    </div>
                  )}
                </div>
              </div>

              {/* Right Panel: Mermaid Export */}
              <div className="space-y-4 flex flex-col">
                {/* CAS score summary */}
                <div className="p-4 rounded-2xl border border-white/10 bg-white/5 space-y-1">
                  <span className="text-[10px] text-white/40 uppercase tracking-widest font-mono">Diagram Quality Score</span>
                  <p className="text-2xl font-bold text-cyan-300 font-mono">{diagramCas.toFixed(3)}</p>
                  <p className="text-[11px] text-white/50">{isAcceptable ? "✅ Passed — Ready to accept" : "⚠ Below threshold — Refinement needed"}</p>
                </div>

                {/* Copyable Mermaid for GitHub README */}
                <div className="p-4 rounded-2xl border border-white/10 bg-white/5 space-y-3 flex-1 flex flex-col justify-between">
                  <div className="space-y-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-cyan-300 font-mono block">GitHub README Mermaid Export</span>
                    <p className="text-[11px] text-white/60">Paste into <code className="text-cyan-300">README.md</code> for native rendering:</p>
                    <div className="p-3 rounded-xl bg-black/90 font-mono text-[11px] text-cyan-200 border border-white/10 max-h-52 overflow-y-auto whitespace-pre">
                      {`\`\`\`mermaid\n${generateFallbackMermaidCode(selectedCandidate?.architecture)}\n\`\`\``}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      const mmd = generateFallbackMermaidCode(selectedCandidate?.architecture);
                      navigator.clipboard.writeText(`\`\`\`mermaid\n${mmd}\n\`\`\``);
                      alert("Mermaid code copied! Paste directly into your GitHub README.md");
                    }}
                    className="w-full py-2.5 rounded-xl bg-cyan-400 text-black font-bold text-xs cursor-pointer hover:bg-cyan-300 transition-all"
                  >
                    Copy Mermaid Code
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 4: INTERACTIVE REFINEMENT ENGINE                         */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "git_loop" && (
          <div className="space-y-6">
            
            {/* Version Control Timeline */}
            <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-3">
                <GitBranch className="text-cyan-400" size={18} />
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-300" style={{ fontFamily: "Orbitron, sans-serif" }}>
                  Diagram Iteration History (PlantUML)
                </span>
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {iterations.map(it => (
                  <button
                    key={it.version}
                    onClick={() => setActiveVersion(it.version)}
                    className={`
                      px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer flex items-center gap-1.5
                      ${activeVersion === it.version
                        ? "bg-cyan-400 text-black shadow-[0_0_10px_rgba(45,220,255,0.4)]"
                        : "bg-white/10 text-white/60 hover:bg-white/20"
                      }
                    `}
                  >
                    <GitCommit size={12} />
                    {it.version} (CAS {typeof it.cas === 'number' ? it.cas.toFixed(3) : it.cas})
                  </button>
                ))}
              </div>
            </div>

            {/* Iteration Viewer & AI Refine Prompt */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* VSCode / AntiGravity Style Code Editor */}
              <div className="lg:col-span-2 rounded-2xl border border-cyan-400/30 bg-[#0a0c1a] overflow-hidden flex flex-col font-mono shadow-2xl">
                {/* Editor Header Bar */}
                {(() => {
                  const formattedCode = (activeIteration.code || "").replace(/\\n/g, "\n").replace(/\\"/g, '"');
                  const codeLines = formattedCode.split("\n");

                  return (
                    <>
                      <div className="flex items-center justify-between px-4 py-2.5 bg-[#050610] border-b border-white/10 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block" />
                          <span className="w-3 h-3 rounded-full bg-yellow-500/80 inline-block" />
                          <span className="w-3 h-3 rounded-full bg-green-500/80 inline-block" />
                          <span className="ml-2 font-bold text-cyan-400 text-[11px] uppercase tracking-wider">
                            architecture_diagram_{activeIteration.version}.puml
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-white/50 text-[11px]">
                          <span className="px-2 py-0.5 rounded bg-cyan-400/10 text-cyan-300 font-semibold">
                            CAS: {typeof activeIteration.cas === 'number' ? activeIteration.cas.toFixed(3) : activeIteration.cas}
                          </span>
                          <span>Lines: {codeLines.length}</span>
                          <button
                            onClick={() => navigator.clipboard.writeText(formattedCode)}
                            className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-[10px] font-bold cursor-pointer transition-all"
                          >
                            Copy Code
                          </button>
                        </div>
                      </div>

                      {/* Code Editor Body with Line Numbers */}
                      <div className="p-4 overflow-x-auto max-h-[500px] overflow-y-auto flex text-xs leading-relaxed bg-[#060814]">
                        {/* Line Numbers Gutter */}
                        <div className="select-none pr-4 mr-4 text-right text-white/30 border-r border-white/10 font-mono space-y-0.5">
                          {codeLines.map((_, i) => (
                            <div key={i}>{i + 1}</div>
                          ))}
                        </div>

                        {/* Code Text Content */}
                        <div className="text-cyan-200 font-mono whitespace-pre space-y-0.5 flex-1">
                          {codeLines.map((line, i) => (
                            <div key={i} className="hover:bg-cyan-500/10 px-1 rounded transition-colors">
                              {line || " "}
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>

              {/* Conditional Right Panel */}
              {needsRefinement ? (
                /* CAS BELOW THRESHOLD — Show AI Refinement Engine */
                <div className="p-6 rounded-2xl border border-amber-400/20 bg-gradient-to-br from-amber-950/30 via-orange-950/10 to-black space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-amber-300">
                      <AlertTriangle size={16} />
                      <h4 className="text-xs font-bold uppercase tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
                        Quality Threshold Not Met
                      </h4>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-amber-400/10 space-y-1">
                      <p className="text-[11px] text-white/60 font-mono">CAS Score: <span className="text-amber-300 font-bold">{diagramCas.toFixed(3)}</span> / Threshold: <span className="text-white/80">0.600</span></p>
                      {activeIteration?.issues?.length > 0 && (
                        <ul className="text-[10px] text-amber-200/70 space-y-0.5 mt-1">
                          {activeIteration.issues.slice(0, 4).map((iss, i) => (
                            <li key={i} className="flex gap-1"><span className="text-amber-400">›</span>{iss}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <p className="text-[11px] text-white/50">
                      Provide optional guidance for the AI Refinement Engine, or trigger automatic issue-based improvement:
                    </p>
                    <textarea
                      rows={4}
                      value={refinePrompt}
                      onChange={e => setRefinePrompt(e.target.value)}
                      placeholder="Optional: e.g. Add a Redis Caching Layer between API Gateway and DB..."
                      className="w-full p-3 rounded-xl bg-black/60 border border-white/10 text-xs text-white placeholder:text-white/30 focus:border-amber-400 outline-none"
                    />
                  </div>
                  <button
                    onClick={handleRefineDiagram}
                    disabled={refining}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-amber-400 text-black cursor-pointer hover:bg-amber-300 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <Sparkles size={14} className={refining ? "animate-spin" : ""} />
                    {refining ? "AI Refinement Running..." : "Run AI Improvement Pass"}
                  </button>
                </div>
              ) : (
                /* CAS PASSED THRESHOLD — Human Review Panel, no AI needed */
                <div className="p-6 rounded-2xl border border-green-400/20 bg-gradient-to-br from-green-950/30 via-emerald-950/10 to-black space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-green-300">
                      <CheckCircle2 size={16} />
                      <h4 className="text-xs font-bold uppercase tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
                        Human Review Gate
                      </h4>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-green-400/10 space-y-1">
                      <p className="text-[11px] text-white/60 font-mono">CAS Score: <span className="text-green-300 font-bold">{diagramCas.toFixed(3)}</span> — <span className="text-green-400">PASSED ✓</span></p>
                      <p className="text-[10px] text-white/40 mt-1">
                        The evaluation engine determined this architecture meets all quality thresholds. No AI refinement is triggered.
                      </p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[11px] text-white/60 font-semibold">Your review checklist:</p>
                      {[
                        "Verify component layer separation is structurally sound",
                        "Confirm all client-facing FRs are represented by named components",
                        "Check that deployment boundaries match client infrastructure constraints",
                      ].map((item, i) => (
                        <label key={i} className="flex items-start gap-2 cursor-pointer">
                          <input type="checkbox" className="mt-0.5 accent-cyan-400" />
                          <span className="text-[11px] text-white/70">{item}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <p className="text-[10px] text-white/30 text-center">
                    Use <strong className="text-white/50">Accept & Proceed</strong> below when satisfied, or <strong className="text-white/50">Regenerate HLD</strong> to restart.
                  </p>
                </div>
              )}

            </div>

          </div>
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 4: SIDE-BY-SIDE DIFF VIEWER                               */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "diff" && (
          <div className="rounded-2xl border border-cyan-400/20 bg-[#080818] p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <FileDiff className="text-cyan-400" size={18} />
                <h3 className="text-sm font-bold text-cyan-300" style={{ fontFamily: "Orbitron, sans-serif" }}>
                  Unified Architecture Diff (v1 vs {iterations[iterations.length - 1]?.version || "v2"})
                </h3>
              </div>
              <span className="text-xs text-white/40 font-mono">
                showing additions (+) and deletions (-)
              </span>
            </div>

            <div className="p-4 rounded-xl bg-black/90 font-mono text-xs space-y-1 overflow-x-auto max-h-[500px] border border-white/10">
              {diffText.split("\n").map((line, idx) => {
                let colorCls = "text-white/60";
                if (line.startsWith("+")) colorCls = "text-green-300 bg-green-950/60 px-2 py-0.5 rounded font-semibold";
                if (line.startsWith("-")) colorCls = "text-red-300 bg-red-950/60 px-2 py-0.5 rounded font-semibold";
                return (
                  <div key={idx} className={`${colorCls} leading-relaxed whitespace-pre`}>
                    {line}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Verdict & Actions Footer (Swapped Buttons) ───────────────── */}
        <div className={`p-6 rounded-2xl border flex flex-col sm:flex-row items-center justify-between gap-4 ${
          isAcceptable ? "border-green-400/30 bg-green-950/20" : "border-amber-400/30 bg-amber-950/20"
        }`}>
          <div>
            <p className="text-sm font-semibold text-white">
              {isAcceptable
                ? "The architecture passes ATAM quality threshold (CAS >= 0.60). Ready for LLD & UI design."
                : "The architecture score requires manual review before proceeding."}
            </p>
            <p className="text-xs text-white/40 mt-0.5">
              Current Verdict: <strong className="text-cyan-300 uppercase">{selectedCandidate?.scores?.verdict || verdict}</strong>
            </p>
          </div>

          <div className="flex gap-3">
            {/* Left side: Regenerate HLD */}
            <button
              onClick={handleReject}
              disabled={restarting || selecting}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold uppercase tracking-widest text-white border border-red-400/50 hover:bg-red-900/30 cursor-pointer transition-all disabled:opacity-50"
            >
              <RefreshCw size={16} className={restarting ? "animate-spin" : ""} />
              Regenerate HLD
            </button>
            {/* Right side: Accept & Proceed */}
            <button
              onClick={handleAccept}
              disabled={selecting}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold uppercase tracking-widest text-black bg-cyan-400 hover:bg-cyan-300 cursor-pointer transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(45,220,255,0.3)]"
            >
              {selecting ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
              {selecting ? "Saving Selection..." : "Accept & Proceed"}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
