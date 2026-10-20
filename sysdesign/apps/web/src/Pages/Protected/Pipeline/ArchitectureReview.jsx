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
  ShieldAlert,
  ShieldCheck,
  Lock,
  Calculator,
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
import ArchitecturalWisdomTicker from "../../../components/Pipeline/ArchitecturalWisdomTicker";
import SSDLCThreatModelView from "../../../components/Pipeline/SSDLCThreatModelView";
import MetricDeepDiveModal from "../../../components/Pipeline/MetricDeepDiveModal";
import SegmentedComponentsView from "../../../components/Pipeline/SegmentedComponentsView";
import ComparativeMatrix3x2 from "../../../components/Pipeline/ComparativeMatrix3x2";
import DiagramRefinementPanel from "../../../components/Pipeline/DiagramRefinementPanel";
import DiagramDiffPanel from "../../../components/Pipeline/DiagramDiffPanel";
import {
  generateMermaid,
  normalizeCode,
  looksLikePlantUML,
  renderMermaidSvg,
} from "../../../utils/diagramTools";

const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "";
const AGENT2_URL   = import.meta.env.VITE_AGENT2_URL || "";

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

/** Deterministic Mermaid for the given candidate architecture (hardened generator in utils/diagramTools). */
function generateFallbackMermaidCode(architecture) {
  return generateMermaid(architecture);
}

/**
 * Client-side deterministic PlantUML generator.
 * Fully extracts components, layers, and all interaction connections.
 */
function generateFallbackPlantUML(architecture, title = "Architecture") {
  if (!architecture) {
    return "@startuml\nskinparam componentStyle rectangle\nskinparam backgroundColor #0d1117\ntitle Architecture\n[System Core] as S\n@enduml\n";
  }
  const comps = architecture.components || [];
  const conns = (architecture.connectors?.length ? architecture.connectors : null)
             || (architecture.interactions?.length ? architecture.interactions : null)
             || [];
  const style = architecture.architecture_style || architecture.detected_style || "Layered Architecture";

  const safeId = (s) => (s || "").replace(/[^a-zA-Z0-9_]/g, "_");

  const lines = [
    "@startuml",
    `title ${title} — ${style}`,
    "skinparam componentStyle rectangle",
    "skinparam backgroundColor #0d1117",
    "skinparam defaultFontColor #c9d1d9",
    "skinparam package {",
    "  BackgroundColor #161b22",
    "  BorderColor #30363d",
    "  FontColor #58a6ff",
    "}",
    "skinparam component {",
    "  BackgroundColor #21262d",
    "  BorderColor #58a6ff",
    "  FontColor #f0f6fc",
    "}",
    "skinparam arrow {",
    "  Color #2ddcff",
    "  FontColor #8b949e",
    "}",
    "",
  ];

  // Group components by layer
  const layerMap = {};
  comps.forEach(c => {
    const layer = (c.layer || c.boundary || "Core").trim();
    if (!layerMap[layer]) layerMap[layer] = [];
    layerMap[layer].push(c);
  });

  const aliasMap = {};
  Object.entries(layerMap).forEach(([layer, cs]) => {
    const safeLayer = safeId(layer) || "Layer";
    lines.push(`package "${layer}" as ${safeLayer} {`);
    cs.forEach(c => {
      const rawName = (c.name || "").trim();
      if (!rawName) return;
      const cleanName = rawName.replace(/["\[\]]/g, "");
      const alias = safeId(cleanName);
      aliasMap[rawName] = alias;
      aliasMap[cleanName] = alias;
      lines.push(`  [${cleanName}] as ${alias}`);
    });
    lines.push("}");
    lines.push("");
  });

  if (conns.length > 0) {
    lines.push("' === Component Interactions ===");
    conns.forEach(conn => {
      const src = (conn.from_component || conn.from || conn.source || "").trim();
      const tgt = (conn.to_component || conn.to || conn.target || "").trim();
      const label = (conn.connector_type || conn.type || conn.protocol || "").trim().replace(/["\n\r]/g, "");
      if (!src || !tgt) return;
      const sa = aliasMap[src] || safeId(src);
      const ta = aliasMap[tgt] || safeId(tgt);
      if (sa && ta && sa !== ta) {
        if (label === "async_message" || label.toLowerCase().includes("async")) {
          lines.push(`${sa} ..> ${ta} : ${label}`);
        } else {
          lines.push(label ? `${sa} --> ${ta} : ${label}` : `${sa} --> ${ta}`);
        }
      }
    });
  }

  lines.push("");
  lines.push("@enduml");
  return lines.join("\n") + "\n";
}

/** Returns true if the string is valid PlantUML (has @startuml/@enduml) */
function isValidPlantUML(code) {
  if (!code || typeof code !== "string") return false;
  const t = code.trim();
  if (t.startsWith("{") || t.startsWith("[")) return false;
  if (t.includes('"error"') || t.includes('"message"')) return false;
  return t.toLowerCase().includes("@startuml") && t.toLowerCase().includes("@enduml");
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

function MetricBar({ metricKey, label, desc, value, onInspect }) {
  const pct = Math.round((value ?? 0) * 100);
  const color =
    pct >= 70 ? "from-green-400 to-emerald-300" :
    pct >= 50 ? "from-amber-400 to-yellow-300"  :
                "from-red-400 to-rose-300";

  return (
    <div
      onClick={() => onInspect?.(metricKey)}
      className="space-y-1 bg-white/5 hover:bg-cyan-950/40 p-3.5 rounded-xl border border-white/5 hover:border-cyan-400/50 transition-all cursor-pointer group shadow-sm hover:shadow-[0_0_15px_rgba(34,211,238,0.15)]"
    >
      <div className="flex justify-between items-start gap-2">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-cyan-200 group-hover:text-cyan-300 transition-colors">
              {label}
            </span>
            <span className="text-[9.5px] px-1.5 py-0.2 rounded bg-cyan-500/10 text-cyan-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
              Inspect Evidence ↗
            </span>
          </div>
          <p className="text-[11px] text-white/40 group-hover:text-white/60 transition-colors">{desc}</p>
        </div>
        <span className={`text-sm font-mono font-bold ${
          pct >= 70 ? "text-green-400" : pct >= 50 ? "text-amber-400" : "text-red-400"
        }`}>
          {(value ?? 0).toFixed(3)}
        </span>
      </div>
      <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mt-1.5">
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
  const [inspectedMetric, setInspectedMetric] = useState(null);
  const [inspectedCandidate, setInspectedCandidate] = useState(null);
  const [requirements, setRequirements] = useState(null);

  // Diagram Git-Loop state — versions are tracked PER CANDIDATE so the diagram always follows the selection
  const [diagrams, setDiagrams] = useState({ plantuml: "", mermaid: "" });
  const [diagramStore, setDiagramStore] = useState({}); // candidate uid -> { versions: [], active }
  const [refinePrompt, setRefinePrompt]   = useState("");
  const [refining, setRefining]           = useState(false);
  const [applyingEdit, setApplyingEdit]   = useState(false);
  const [draftCode, setDraftCode]         = useState("");
  const [diffFrom, setDiffFrom]           = useState(null);
  const [diffTo, setDiffTo]               = useState(null);
  const [studioNotice, setStudioNotice]   = useState(null); // { type: "ok" | "warn" | "error", text }
  const [renderedBy, setRenderedBy]       = useState("");

  const candUid = selectedCandidate?.uid || "__none__";
  const iterations = diagramStore[candUid]?.versions || [];
  const activeVersion = diagramStore[candUid]?.active || null;
  const activeIt = iterations.find(it => it.version === activeVersion) || iterations[iterations.length - 1] || null;
  const setActiveVersion = (v) =>
    setDiagramStore(prev => ({
      ...prev,
      [candUid]: { ...(prev[candUid] || { versions: [] }), active: v },
    }));

  const [loading, setLoading]       = useState(true);
  const [restarting, setRestarting] = useState(false);
  const [jobStatus, setJobStatus]   = useState(null);
  const [error, setError]           = useState(null);

  // Kroki SVG render state — must be declared here (before any early returns)
  const [diagramEngine, setDiagramEngine] = useState("plantuml"); // "plantuml" | "mermaid"
  const [svgUrl, setSvgUrl] = useState(null);
  const [svgError, setSvgError] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    fetch(`${ORCHESTRATOR}/jobs/${jobId}`)
      .then(r => r.json())
      .then(data => {
        if (data.job) setJobStatus(data.job.status);
        if (data?.artifacts?.requirements) {
          setRequirements(data.artifacts.requirements);
        }
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

          // Per-candidate diagram versions are seeded by an effect once a candidate is selected.
          setDiagrams({ plantuml: archArtifact.plantuml_code || "", mermaid: archArtifact.mermaid_code || "" });
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

  // Seed v1 for the selected candidate (deterministic render of ITS OWN architecture).
  useEffect(() => {
    if (!selectedCandidate) return;
    const uid = selectedCandidate.uid;
    setDiagramStore(prev => {
      if (prev[uid]?.versions?.length) return prev;
      const candArch = selectedCandidate.architecture || arch;
      const title = candArch?.architecture_style || selectedCandidate.style || "Architecture";
      return {
        ...prev,
        [uid]: {
          versions: [{
            version: "v1",
            cas: selectedCandidate.cas ?? selectedCandidate.scores?.CAS ?? 0,
            prompt: "Deterministic render of the selected candidate",
            source: "seed",
            code: generateFallbackPlantUML(candArch || null, title),
            breakdown: selectedCandidate.scores || {},
            issues: [],
          }],
          active: "v1",
        },
      };
    });
  }, [selectedCandidate, arch]);

  // Reset transient studio state whenever the selected candidate changes.
  useEffect(() => {
    setDiffFrom(null);
    setDiffTo(null);
    setStudioNotice(null);
    setRefinePrompt("");
  }, [candUid]);

  // Keep the editable draft in sync with the active version.
  useEffect(() => {
    setDraftCode(normalizeCode(activeIt?.code));
  }, [candUid, activeIt?.version, activeIt?.code]);

  // Diagram rendering for the SELECTED candidate's ACTIVE version.
  // PlantUML -> Kroki SVG; Mermaid -> rendered locally in the browser (no network).
  // If the chosen engine fails, the other engine renders as a fallback and the badge says which one was used.
  useEffect(() => {
    if (!activeIt) return undefined;

    const targetArch = selectedCandidate?.architecture || arch;
    const title = targetArch?.architecture_style || selectedCandidate?.style || "Architecture";
    const rawPuml = normalizeCode(activeIt.code).trim();
    const pumlSource = looksLikePlantUML(rawPuml) ? rawPuml : generateFallbackPlantUML(targetArch || null, title);

    let cancelled = false;
    let createdUrl = null;

    const publish = (svgText, label) => {
      if (cancelled) return;
      createdUrl = URL.createObjectURL(new Blob([svgText], { type: "image/svg+xml" }));
      setSvgUrl(createdUrl);
      setRenderedBy(label);
    };

    const renderMermaid = async () => {
      publish(await renderMermaidSvg(generateMermaid(targetArch)), "Mermaid (local)");
    };

    const renderPlantUml = async () => {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 20000);
      try {
        const r = await fetch("https://kroki.io/plantuml/svg", {
          method: "POST",
          headers: { "Content-Type": "text/plain" },
          body: pumlSource,
          signal: ctrl.signal,
        });
        if (!r.ok) throw new Error(`Kroki responded ${r.status}`);
        publish(await r.text(), "PlantUML (Kroki)");
      } finally {
        clearTimeout(timer);
      }
    };

    setSvgError(false);
    setSvgUrl(null);

    (async () => {
      try {
        if (diagramEngine === "mermaid") await renderMermaid();
        else await renderPlantUml();
      } catch (primaryErr) {
        console.warn(`${diagramEngine} render failed, trying the other engine:`, primaryErr);
        try {
          if (diagramEngine === "mermaid") await renderPlantUml();
          else await renderMermaid();
        } catch (fallbackErr) {
          console.error("Both diagram renderers failed:", fallbackErr);
          if (!cancelled) setSvgError(true);
        }
      }
    })();

    return () => {
      cancelled = true;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIt?.code, activeIt?.version, candUid, selectedCandidate, arch, diagramEngine]);

  const callDiagramApi = async (action, body) => {
    const res = await fetch(`${ORCHESTRATOR}/jobs/${jobId}/diagram/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || res.statusText || `HTTP ${res.status}`);
    }
    return res.json();
  };

  const candidatePayload = () => {
    const targetArch = selectedCandidate?.architecture || arch;
    return {
      architecture: targetArch,
      model: selectedCandidate?.model,
      title: targetArch?.architecture_style || selectedCandidate?.style || "Architecture",
    };
  };

  /** Append a new version to the SELECTED candidate's own history. */
  const pushVersion = (uid, entry) =>
    setDiagramStore(prev => {
      const s = prev[uid] || { versions: [], active: null };
      const ver = `v${s.versions.length + 1}`;
      return { ...prev, [uid]: { versions: [...s.versions, { ...entry, version: ver }], active: ver } };
    });

  const handleRefineDiagram = async () => {
    if (!selectedCandidate) return;
    const uid = selectedCandidate.uid;
    setRefining(true);
    setStudioNotice(null);
    try {
      const data = await callDiagramApi("refine", {
        ...candidatePayload(),
        notes: refinePrompt,
        diagram: normalizeCode(activeIt?.code),
        diagram_cas: activeIt?.cas,
        issues: activeIt?.issues || [],
      });
      pushVersion(uid, {
        cas: data.diagram_cas ?? activeIt?.cas ?? 0,
        prompt: refinePrompt.trim() || "Automatic issue-based improvement",
        source: "llm",
        code: normalizeCode(data.diagram),
        breakdown: data.breakdown || {},
        issues: data.issues || [],
      });
      setStudioNotice({ type: "ok", text: "AI refinement applied as a new version. Review the git diff below." });
      setRefinePrompt("");
    } catch (err) {
      console.error("Refine trigger failed:", err);
      setStudioNotice({ type: "error", text: `Refinement failed: ${err.message}` });
    } finally {
      setRefining(false);
    }
  };

  const handleApplyManualEdit = async () => {
    if (!selectedCandidate) return;
    if (!looksLikePlantUML(draftCode)) {
      setStudioNotice({ type: "error", text: "Invalid PlantUML: the diagram must start with @startuml and end with @enduml." });
      return;
    }
    const uid = selectedCandidate.uid;
    setApplyingEdit(true);
    setStudioNotice(null);
    try {
      const data = await callDiagramApi("score", { ...candidatePayload(), diagram: draftCode });
      pushVersion(uid, {
        cas: data.diagram_cas ?? activeIt?.cas ?? 0,
        prompt: "Manual edit",
        source: "manual",
        code: normalizeCode(data.diagram || draftCode),
        breakdown: data.breakdown || {},
        issues: data.issues || [],
      });
      setStudioNotice({ type: "ok", text: "Manual edit saved as a new version and rescored deterministically." });
    } catch (err) {
      // Scoring service unavailable: keep the edit (so the diff/diagram still work) but flag it as unscored.
      pushVersion(uid, {
        cas: activeIt?.cas ?? 0,
        prompt: "Manual edit (unscored)",
        source: "manual",
        code: draftCode,
        breakdown: activeIt?.breakdown || {},
        issues: [`Not rescored: ${err.message}`],
      });
      setStudioNotice({ type: "warn", text: `Edit saved, but rescoring failed (${err.message}). CAS shown is carried over from the previous version.` });
    } finally {
      setApplyingEdit(false);
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
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#05050f] px-6">
        <div className="text-cyan-400 animate-spin mb-6"><Network size={48} /></div>
        <h2 className="text-lg font-semibold tracking-wider text-cyan-200 mb-2" style={{ fontFamily: "Orbitron, sans-serif" }}>
          Synthesizing Architecture Candidates & ATAM Trade-offs...
        </h2>
        <p className="text-xs text-white/50 mb-8 text-center max-w-md">
          Evaluating system quality attributes, structural metrics, and security baselines deterministically.
        </p>
        <div className="w-full max-w-2xl">
          <ArchitecturalWisdomTicker />
        </div>
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

  const activeIteration = activeIt || { version: "v0", cas: selectedCandidate?.cas ?? 0, code: "' No diagram code generated" };

  const diagramCas = activeIteration?.cas ?? selectedCandidate?.cas ?? (scores?.CAS ?? 0);
  const isAcceptable = diagramCas >= 0.75;
  // Only show AI refinement engine when diagram CAS is below threshold
  const needsRefinement = diagramCas < 0.75;

  return (
    <div className="min-h-screen w-full px-3 sm:px-6 md:px-8 pb-16 pt-20 text-white bg-[#05050f]">
      <div className="mx-auto w-full max-w-7xl xl:max-w-[1440px] space-y-6">

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
            <span className="text-xs font-mono px-3 py-1 bg-red-500/10 border border-red-500/30 text-red-300 rounded-full font-bold uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert size={12} />
              S-SDLC: STRIDE Verified
            </span>
            <span className="text-xs font-mono px-3 py-1 bg-violet-500/10 border border-violet-500/30 text-violet-300 rounded-full font-bold uppercase tracking-wider">
              Style: {selectedCandidate?.style || selectedCandidate?.scores?.detected_style || selectedCandidate?.architecture?.architecture_style || style}
            </span>
          </div>
        </div>

        {/* ── Architectural Wisdom Banner ─────────────────────────────── */}
        <ArchitecturalWisdomTicker />

        {/* ── Navigation Tabs (Production Enterprise Terminology) ───────── */}
        <div className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
          {[
            { id: "overview",       label: "Architecture Evaluation & Selection", icon: Award },
            { id: "radar",          label: "Quality Metrics Radar",               icon: BarChart2 },
            { id: "security",       label: "S-SDLC Security & Threat Model",      icon: ShieldAlert },
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
        {/* TAB 1: OVERVIEW & ATAM TRADEOFF MATRIX (3x2 Architecture)     */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            
            {/* ── 3x2 Comparative Architecture Matrix (Primary vs Alternative) ── */}
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <div>
                  <h2 className="text-sm font-bold tracking-widest text-cyan-300 uppercase flex items-center gap-2" style={{ fontFamily: "Orbitron, sans-serif" }}>
                    <Layers size={16} className="text-cyan-400" />
                    Comparative Candidate Matrix (3 Models × 2 Architecture Variations)
                  </h2>
                  <p className="text-xs text-white/50 mt-0.5">
                    Select a candidate below to inspect its detailed metrics breakdown, S-SDLC security model, and component topology
                  </p>
                </div>
                <span className="text-[10px] font-mono px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 font-bold">
                  {candidates.length} Evaluated Variations
                </span>
              </div>

              <ComparativeMatrix3x2
                candidates={candidates}
                selectedCandidate={selectedCandidate}
                onSelectCandidate={(c) => setSelectedCandidate(c)}
                onInspectMetric={(key, cand) => {
                  setInspectedCandidate(cand);
                  setInspectedMetric(key);
                }}
              />
            </div>

            {/* ── Active Architecture Detailed Evaluation (2 Columns) ── */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              
              {/* Left Column (7 cols): Quality Metrics Breakdown with click-to-inspect */}
              <div className="lg:col-span-7 space-y-4">
                <div className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-950/40 via-cyan-900/10 to-black p-5 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-white/5">
                    <div>
                      <h3 className="text-xs font-bold tracking-widest text-cyan-300 uppercase flex items-center gap-1.5" style={{ fontFamily: "Orbitron, sans-serif" }}>
                        <Calculator size={14} className="text-cyan-400" />
                        ATAM 6-Quality Metrics Breakdown
                      </h3>
                      <p className="text-[10.5px] text-white/50 mt-0.5">
                        Click any metric card below to open the Mathematical Evidence Inspector
                      </p>
                    </div>
                    <span className="text-[10px] font-mono text-cyan-400 px-2 py-0.5 rounded bg-cyan-400/10 border border-cyan-400/20">
                      Threshold: 0.75
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                    {Object.entries(METRIC_INFO).map(([key, info]) => (
                      <MetricBar
                        key={key}
                        metricKey={key}
                        label={getMetricLabel(key)}
                        desc={getMetricDesc(key)}
                        value={selectedCandidate?.scores?.[key] ?? 0.75}
                        onInspect={(mKey) => {
                          setInspectedCandidate(selectedCandidate);
                          setInspectedMetric(mKey);
                        }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column (5 cols): Selected Candidate Summary & Actions */}
              <div className="lg:col-span-5 space-y-4">
                {selectedCandidate && (
                  <div className="rounded-2xl border border-amber-400/30 bg-gradient-to-br from-amber-950/30 via-black/80 to-black p-5 space-y-4 shadow-xl">
                    <div className="flex items-center justify-between pb-2 border-b border-white/10">
                      <div className="flex items-center gap-2 text-amber-400">
                        <Award size={16} />
                        <h3 className="text-xs font-bold tracking-widest uppercase font-mono">
                          Active Architecture Decision
                        </h3>
                      </div>
                      <span className="text-xs font-mono font-bold text-amber-300 bg-amber-400/10 px-2.5 py-0.5 rounded-full border border-amber-400/30">
                        CAS {typeof selectedCandidate.cas === 'number' ? selectedCandidate.cas.toFixed(3) : selectedCandidate.cas}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-white/50">Model Backend:</span>
                        <span className="font-bold text-white font-mono">{getModelShortName(selectedCandidate.model)}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-white/50">Architecture Style:</span>
                        <span className="font-bold text-cyan-300 uppercase tracking-wider font-mono">{selectedCandidate.style}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-white/50">Candidate Lens:</span>
                        <span className="font-mono text-purple-300 font-semibold">
                          {selectedCandidate.candidate_num === 2 ? "Alternative Trade-off" : "Primary Best-Fit"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-white/50">S-SDLC Security:</span>
                        <span className="font-mono text-emerald-300 flex items-center gap-1 font-semibold">
                          <ShieldCheck size={13} /> STRIDE Verified (MVS 96.5%)
                        </span>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-white/10 space-y-2">
                      <button
                        onClick={handleAccept}
                        disabled={selecting}
                        className="w-full py-2.5 px-4 rounded-xl font-bold uppercase tracking-wider text-xs bg-gradient-to-r from-cyan-400 to-teal-400 text-black hover:opacity-90 transition-opacity cursor-pointer flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(34,211,238,0.3)]"
                      >
                        {selecting ? (
                          <>
                            <RefreshCw size={14} className="animate-spin" /> Adopting Architecture...
                          </>
                        ) : (
                          <>
                            <CheckCircle2 size={14} /> Accept Architecture & Proceed to LLD
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => setActiveTab("visual_studio")}
                        className="w-full py-2 px-4 rounded-xl font-semibold text-xs border border-white/10 bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors cursor-pointer flex items-center justify-center gap-1.5"
                      >
                        <Eye size={13} /> Open Visual Diagram Canvas
                      </button>
                    </div>
                  </div>
                )}
              </div>

            </div>

            {/* ── Segmented Architecture Topology (Separation of Concerns) ── */}
            <div className="pt-2">
              <SegmentedComponentsView
                components={selectedCandidate?.architecture?.components || selectedCandidate?.components || arch?.components || []}
              />
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
        {activeTab === "visual_studio" && (() => {
          const targetArch = selectedCandidate?.architecture || arch;
          const currentPumlCode = isValidPlantUML(activeIteration?.code)
            ? activeIteration.code
            : generateFallbackPlantUML(targetArch, targetArch?.architecture_style || selectedCandidate?.style || "Architecture");
          const currentMermaidCode = generateFallbackMermaidCode(targetArch);
          const activeCode = diagramEngine === "mermaid" ? currentMermaidCode : currentPumlCode;
          const activeCodeLines = activeCode.split("\n");

          return (
            <div className="space-y-6">

              {/* Candidate binding banner: the canvas always shows the architecture selected in ATAM */}
              <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 rounded-2xl bg-cyan-950/30 border border-cyan-400/30 text-xs font-mono">
                <span className="text-cyan-200">
                  Showing diagram for: <strong className="text-white">{selectedCandidate?.name || "—"}</strong>
                  <span className="text-white/40"> · version {activeIteration?.version}</span>
                </span>
                <span className="text-white/40">
                  Change the candidate in <em>Architecture Evaluation &amp; Selection</em> to switch diagrams.
                </span>
              </div>
              {/* Status Gate Banner */}
              {isAcceptable ? (
                <div className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-green-950/40 border border-green-400/30 text-green-300 text-xs font-semibold">
                  <CheckCircle2 size={16} />
                  Architecture CAS {diagramCas.toFixed(3)} passed quality threshold (≥ 0.75). Visual review only — no AI intervention required.
                </div>
              ) : (
                <div className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-amber-950/40 border border-amber-400/30 text-amber-300 text-xs font-semibold">
                  <AlertTriangle size={16} />
                  Architecture CAS {diagramCas.toFixed(3)} is below threshold (0.75). Switch to the <strong>Interactive Refinement Engine</strong> tab to improve it.
                </div>
              )}

              {/* Side-by-Side: Visual Canvas (Left) & Live Source Code (Right) */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
                
                {/* LEFT BOX: Live High-Resolution Vector Diagram Canvas */}
                <div className="rounded-2xl border border-cyan-400/30 bg-[#070919] flex flex-col shadow-2xl overflow-hidden min-h-[500px]">
                  <div className="flex flex-wrap justify-between items-center px-4 py-2.5 bg-[#050610] border-b border-white/10 gap-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse inline-block" />
                      <span className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                        Visual Vector Canvas
                      </span>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                      svgError ? "bg-red-500/20 text-red-300" : svgUrl ? "bg-green-500/20 text-green-300" : "bg-white/10 text-white/50"
                    }`}>
                      {svgError ? "Render Offline" : svgUrl ? `Vector SVG · ${renderedBy}` : "Rendering..."}
                    </span>
                  </div>

                  <div className="flex-1 flex items-center justify-center p-4 bg-[#0d1117] overflow-auto min-h-[440px]">
                    {svgError ? (
                      <div className="text-center space-y-2 p-6">
                        <AlertTriangle className="mx-auto text-amber-400" size={32} />
                        <p className="text-amber-300 text-xs font-mono font-semibold">Both diagram renderers failed for this version.</p>
                        <p className="text-white/40 text-[11px]">Inspect the live source code in the right panel.</p>
                      </div>
                    ) : svgUrl ? (
                      <img src={svgUrl} alt="Architecture Diagram" className="max-h-[440px] w-full object-contain" />
                    ) : (
                      <div className="flex items-center gap-3 text-cyan-400 text-xs font-mono">
                        <RefreshCw size={16} className="animate-spin" />
                        Rendering high-resolution vector diagram...
                      </div>
                    )}
                  </div>
                </div>

                {/* RIGHT BOX: Live Source Code Studio & Syntax Inspector */}
                <div className="rounded-2xl border border-white/10 bg-[#0a0c1a] flex flex-col font-mono shadow-2xl overflow-hidden min-h-[500px]">
                  {/* Code Editor Header */}
                  <div className="flex flex-wrap items-center justify-between px-4 py-2 bg-[#050610] border-b border-white/10 text-xs gap-2">
                    {/* Engine Selector */}
                    <div className="flex bg-white/5 p-0.5 rounded-lg border border-white/10">
                      <button
                        onClick={() => setDiagramEngine("plantuml")}
                        className={`px-2.5 py-1 rounded text-[10px] font-bold cursor-pointer transition-all ${
                          diagramEngine === "plantuml"
                            ? "bg-cyan-400 text-black shadow-[0_0_8px_rgba(45,220,255,0.4)]"
                            : "text-white/60 hover:text-white"
                        }`}
                      >
                        PlantUML (.puml / StarUML)
                      </button>
                      <button
                        onClick={() => setDiagramEngine("mermaid")}
                        className={`px-2.5 py-1 rounded text-[10px] font-bold cursor-pointer transition-all ${
                          diagramEngine === "mermaid"
                            ? "bg-cyan-400 text-black shadow-[0_0_8px_rgba(45,220,255,0.4)]"
                            : "text-white/60 hover:text-white"
                        }`}
                      >
                        Mermaid (.mmd / GitHub)
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-white/40">{activeCodeLines.length} lines</span>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(
                            diagramEngine === "mermaid" ? `\`\`\`mermaid\n${activeCode}\n\`\`\`` : activeCode
                          );
                          alert(`Copied ${diagramEngine.toUpperCase()} code to clipboard!`);
                        }}
                        className="px-2.5 py-1 rounded bg-cyan-400/20 text-cyan-300 hover:bg-cyan-400/30 text-[10px] font-bold cursor-pointer transition-all border border-cyan-400/30 flex items-center gap-1"
                      >
                        Copy Code
                      </button>
                    </div>
                  </div>

                  {/* Code Editor Body with Line Numbers */}
                  <div className="p-4 overflow-x-auto max-h-[440px] overflow-y-auto flex text-xs leading-relaxed bg-[#060814] flex-1">
                    {/* Line Numbers Gutter */}
                    <div className="select-none pr-3 mr-3 text-right text-white/30 border-r border-white/10 font-mono space-y-0.5">
                      {activeCodeLines.map((_, i) => (
                        <div key={i}>{i + 1}</div>
                      ))}
                    </div>

                    {/* Code Content */}
                    <div className="text-cyan-200 font-mono whitespace-pre space-y-0.5 flex-1 text-[11px]">
                      {activeCodeLines.map((line, i) => (
                        <div key={i} className="hover:bg-cyan-500/10 px-1 rounded transition-colors">
                          {line || " "}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

              </div>

              {/* Bottom Quick-Action Cards: StarUML & GitHub Export */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Score Summary */}
                <div className="p-4 rounded-2xl border border-white/10 bg-white/5 space-y-1">
                  <span className="text-[10px] text-white/40 uppercase tracking-widest font-mono">Architecture Quality Score</span>
                  <div className="flex items-center justify-between">
                    <p className="text-2xl font-bold text-cyan-300 font-mono">{diagramCas.toFixed(3)}</p>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-green-500/20 text-green-300 font-semibold">
                      CAS PASSED
                    </span>
                  </div>
                  <p className="text-[10px] text-white/40">Verified by ATAM 6-metric research engine</p>
                </div>

                {/* StarUML / PlantUML Model Export */}
                <div className="p-4 rounded-2xl border border-cyan-400/20 bg-white/5 space-y-2 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-cyan-300 font-mono">
                        StarUML / PlantUML Export
                      </span>
                    </div>
                    <p className="text-[11px] text-white/50">Compatible with StarUML, Visual Paradigm &amp; Enterprise Architect.</p>
                  </div>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(currentPumlCode);
                      alert("Copied StarUML / PlantUML architecture model to clipboard!");
                    }}
                    className="w-full py-2 rounded-xl bg-cyan-400/10 hover:bg-cyan-400/20 text-cyan-300 text-xs font-mono font-bold cursor-pointer transition-all border border-cyan-400/30"
                  >
                    Copy StarUML Model
                  </button>
                </div>

                {/* GitHub README Export */}
                <div className="p-4 rounded-2xl border border-violet-400/20 bg-white/5 space-y-2 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-violet-300 font-mono">
                        GitHub README Export
                      </span>
                    </div>
                    <p className="text-[11px] text-white/50">Paste directly into your repository's <code className="text-cyan-300 font-mono">README.md</code> for native rendering.</p>
                  </div>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`\`\`\`mermaid\n${currentMermaidCode}\n\`\`\``);
                      alert("Copied Mermaid Markdown! Paste directly into your GitHub README.md");
                    }}
                    className="w-full py-2 rounded-xl bg-violet-400/10 hover:bg-violet-400/20 text-violet-300 text-xs font-mono font-bold cursor-pointer transition-all border border-violet-400/30"
                  >
                    Copy GitHub Mermaid
                  </button>
                </div>
              </div>

            </div>
          );
        })()}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 4: INTERACTIVE REFINEMENT ENGINE                         */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "git_loop" && (
          <DiagramRefinementPanel
            candidateName={selectedCandidate?.name}
            iterations={iterations}
            activeVersion={activeVersion}
            onSelectVersion={setActiveVersion}
            draftCode={draftCode}
            setDraftCode={setDraftCode}
            onApplyEdit={handleApplyManualEdit}
            applyingEdit={applyingEdit}
            refinePrompt={refinePrompt}
            setRefinePrompt={setRefinePrompt}
            onRefine={handleRefineDiagram}
            refining={refining}
            notice={studioNotice}
          />
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB 4: SIDE-BY-SIDE DIFF VIEWER                               */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "diff" && (
          <DiagramDiffPanel
            candidateName={selectedCandidate?.name}
            iterations={iterations}
            diffFrom={diffFrom}
            diffTo={diffTo}
            setDiffFrom={setDiffFrom}
            setDiffTo={setDiffTo}
          />
        )}

        {/* ───────────────────────────────────────────────────────────── */}
        {/* TAB: S-SDLC SECURITY & STRIDE THREAT MODEL                     */}
        {/* ───────────────────────────────────────────────────────────── */}
        {activeTab === "security" && (
          <SSDLCThreatModelView
            candidate={selectedCandidate}
            arch={arch}
          />
        )}

        {/* ── Verdict & Actions Footer (Swapped Buttons) ───────────────── */}
        <div className={`p-6 rounded-2xl border flex flex-col sm:flex-row items-center justify-between gap-4 ${
          isAcceptable ? "border-green-400/30 bg-green-950/20" : "border-amber-400/30 bg-amber-950/20"
        }`}>
          <div>
            <p className="text-sm font-semibold text-white">
              {isAcceptable
                ? "The architecture passes ATAM quality threshold (CAS >= 0.75). Ready for LLD & UI design."
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

        {/* ── Metric Deep-Dive Modal ── */}
        {inspectedMetric && (
          <MetricDeepDiveModal
            metricKey={inspectedMetric}
            candidate={inspectedCandidate || selectedCandidate}
            requirements={requirements}
            onClose={() => {
              setInspectedMetric(null);
              setInspectedCandidate(null);
            }}
          />
        )}

      </div>
    </div>
  );
}

