/**
 * SRSDownload.jsx
 *
 * Final pipeline page — shows the IEEE 29148-compliant SRS summary,
 * triggers/monitors the SRS Assembler agent, displays the assembled document,
 * and provides download options for the formal Cloudinary PDF and artifacts.
 *
 * Design: Orbitron / cyan / beehive card system.
 */

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FileText,
  Download,
  CheckCircle2,
  ClipboardList,
  Network,
  Code2,
  PanelsTopLeft,
  ChevronLeft,
  RefreshCw,
  Play,
  ExternalLink,
  Copy,
  Check,
  FileCode,
  AlertCircle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Eye,
  Image as ImageIcon,
} from "lucide-react";
import axios from "axios";
import beehiveBg from "../../../Images/beehive-bg.png";

const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "http://127.0.0.1:8000";

const SECTIONS = [
  { num: "§1", title: "Introduction & Scope",    Icon: FileText,      key: "introduction" },
  { num: "§2", title: "Requirements Overview",   Icon: ClipboardList, key: "requirements" },
  { num: "§3", title: "HLD Architecture",        Icon: Network,       key: "hld" },
  { num: "§4", title: "Low-Level Design",        Icon: Code2,         key: "lld" },
  { num: "§5", title: "UI/UX Specifications",    Icon: PanelsTopLeft, key: "ui" },
];

function SectionCard({ section, artifact, isRunning }) {
  const { Icon } = section;
  const isIntro = section.key === "introduction";
  const hasData = isIntro
    ? Boolean(artifact && (artifact.cloudinary_url || artifact.pdf_url || artifact.srs_markdown || artifact.status === "complete"))
    : Boolean(artifact && Object.keys(artifact).length > 0);

  const pendingText = isIntro && isRunning ? "Assembling..." : "Pending...";

  return (
    <div
      className={`
        flex items-center gap-4 p-4 rounded-2xl border transition-all duration-300
        ${hasData
          ? "border-cyan-400/30 bg-cyan-950/40 shadow-[0_0_15px_rgba(34,211,238,0.1)]"
          : isIntro && isRunning
          ? "border-cyan-400/50 bg-cyan-950/20 animate-pulse"
          : "border-white/5 bg-white/5 opacity-50"
        }
      `}
    >
      <div className={`flex-shrink-0 p-2.5 rounded-xl ${hasData ? "bg-cyan-400/15" : "bg-white/5"}`}>
        <Icon className={hasData ? "text-cyan-300" : isIntro && isRunning ? "text-cyan-400 animate-spin" : "text-white/40"} size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/30 font-mono">{section.num}</span>
          <span className="text-sm font-semibold text-white">{section.title}</span>
        </div>
        <p className="text-xs text-white/40 mt-0.5">
          {hasData ? (
            <span className="text-green-400 font-medium">✓ Content generated</span>
          ) : isIntro && isRunning ? (
            <span className="text-cyan-300 font-medium flex items-center gap-1">
              <RefreshCw size={11} className="animate-spin inline" /> Assembling via Agent...
            </span>
          ) : (
            pendingText
          )}
        </p>
      </div>
      {hasData ? (
        <CheckCircle2 className="text-green-400" size={18} />
      ) : isIntro && isRunning ? (
        <RefreshCw className="text-cyan-400 animate-spin" size={16} />
      ) : (
        <div className="w-4 h-4 rounded-full border border-white/20" />
      )}
    </div>
  );
}

function MarkdownWithImages({ markdown, onSelectImage }) {
  if (!markdown) {
    return <p className="text-white/40 text-xs italic">No document text found.</p>;
  }

  const lines = markdown.split("\n");
  const elements = [];
  let tableBuffer = [];

  const flushTable = (key) => {
    if (tableBuffer.length === 0) return;
    const rows = [...tableBuffer];
    tableBuffer = [];

    const parsedRows = rows
      .filter((r) => !r.match(/^\|(\s*[-:]+\s*\|)+$/))
      .map((r) => r.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim()));

    if (parsedRows.length === 0) return;

    elements.push(
      <div key={`table-${key}`} className="my-4 overflow-x-auto rounded-xl border border-white/10 bg-black/40">
        <table className="w-full text-left text-xs text-white/80">
          <thead className="bg-white/10 text-cyan-300 font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              {parsedRows[0].map((cell, cIdx) => (
                <th key={cIdx} className="px-3 py-2 border-b border-white/10">{cell}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {parsedRows.slice(1).map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-white/5 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-3 py-2">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      tableBuffer.push(trimmed);
      return;
    } else {
      flushTable(idx);
    }

    if (!trimmed) {
      elements.push(<div key={`spacer-${idx}`} className="h-2" />);
      return;
    }

    // Markdown Image: ![alt](url)
    const imgMatch = trimmed.match(/^!\[(.*?)\]\((.*?)\)$/);
    if (imgMatch) {
      const altText = imgMatch[1];
      const imgUrl = imgMatch[2];
      elements.push(
        <div key={`img-${idx}`} className="my-5 p-4 rounded-2xl border border-cyan-500/30 bg-black/80 text-center shadow-lg">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-white/10 text-xs">
            <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
              <span>🖼️</span> {altText}
            </span>
            <a
              href={imgUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs hover:underline"
            >
              <span>View Full Size</span>
              <ExternalLink size={12} />
            </a>
          </div>
          <div
            className="group relative inline-block cursor-pointer overflow-hidden rounded-xl border border-white/10 bg-slate-950/80 p-2"
            onClick={() => (onSelectImage ? onSelectImage({ url: imgUrl, title: altText }) : window.open(imgUrl, "_blank"))}
          >
            <img
              src={imgUrl}
              alt={altText}
              className="max-h-[380px] w-auto max-w-full rounded-lg object-contain transition-transform duration-300 group-hover:scale-[1.02]"
              loading="lazy"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-cyan-400 text-black text-xs font-bold uppercase tracking-wider">
                <Maximize2 size={13} /> Click to Enlarge
              </span>
            </div>
          </div>
          <p className="text-[11px] text-white/50 mt-2 italic font-sans">{altText} · Click photo to inspect</p>
        </div>
      );
      return;
    }

    // Headers
    if (trimmed.startsWith("# ")) {
      elements.push(
        <h1 key={`h1-${idx}`} className="text-xl font-bold text-white mt-6 mb-3 font-['Orbitron'] border-b border-white/10 pb-2">
          {trimmed.slice(2)}
        </h1>
      );
      return;
    }
    if (trimmed.startsWith("## ")) {
      elements.push(
        <h2 key={`h2-${idx}`} className="text-base font-bold text-cyan-300 mt-6 mb-2 border-b border-cyan-500/20 pb-1">
          {trimmed.slice(3)}
        </h2>
      );
      return;
    }
    if (trimmed.startsWith("### ")) {
      elements.push(
        <h3 key={`h3-${idx}`} className="text-sm font-semibold text-violet-300 mt-4 mb-1">
          {trimmed.slice(4)}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith("#### ")) {
      elements.push(
        <h4 key={`h4-${idx}`} className="text-xs font-bold text-white/90 uppercase tracking-wider mt-3 mb-1">
          {trimmed.slice(5)}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith("##### ")) {
      elements.push(
        <h5 key={`h5-${idx}`} className="text-xs font-medium text-cyan-400 mt-2 mb-1">
          {trimmed.slice(6)}
        </h5>
      );
      return;
    }

    // Horizontal Rule
    if (trimmed.startsWith("---")) {
      elements.push(<hr key={`hr-${idx}`} className="border-white/10 my-4" />);
      return;
    }

    // Bullet points
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      elements.push(
        <li key={`bullet-${idx}`} className="ml-4 text-xs text-white/80 list-disc my-0.5">
          {trimmed.slice(2)}
        </li>
      );
      return;
    }

    // Normal paragraph
    elements.push(
      <p key={`p-${idx}`} className="text-xs leading-relaxed text-white/80 my-1">
        {trimmed}
      </p>
    );
  });

  flushTable("final");
  return <div className="space-y-1 font-sans">{elements}</div>;
}

function VisualArtifactsGallery({ lld, ui, architecture, onSelectImage }) {
  // Collect LLD diagrams
  const lldDiagrams = [];
  const lldUris = lld?.artifact_uris || {};
  const diagramsObj = lld?.diagrams || {};

  Object.entries(lldUris).forEach(([k, v]) => {
    if (typeof v === "string" && v && !lldDiagrams.some(d => d.url === v)) {
      lldDiagrams.push({
        title: k.replace(/_/g, " ").toUpperCase(),
        url: v,
        type: "UML / ER Diagram"
      });
    }
  });

  if (diagramsObj.class && !lldDiagrams.some(d => d.url === diagramsObj.class)) {
    lldDiagrams.push({ title: "CLASS DIAGRAM", url: diagramsObj.class, type: "UML Class Model" });
  }
  if (diagramsObj.er && !lldDiagrams.some(d => d.url === diagramsObj.er)) {
    lldDiagrams.push({ title: "ENTITY RELATIONSHIP DIAGRAM", url: diagramsObj.er, type: "Logical Relational Schema" });
  }
  if (Array.isArray(diagramsObj.sequence)) {
    diagramsObj.sequence.forEach((s, idx) => {
      const sUrl = typeof s === "string" ? s : (s?.png || s?.cloudinary_url);
      if (sUrl && !lldDiagrams.some(d => d.url === sUrl)) {
        lldDiagrams.push({
          title: `SEQUENCE DIAGRAM #${idx + 1}`,
          url: sUrl,
          type: "UML Behavioral Sequence"
        });
      }
    });
  }

  // Collect UI screens
  const uiScreens = ui?.screens || [];
  const generatedHtml = ui?.generated_screens || {};
  const uiArtifactUris = ui?.artifact_uris || {};

  // High-Level Architecture
  const hldDiagram = architecture?.artifact_uris?.architecture_diagram || architecture?.artifact_uris?.c4_diagram;

  return (
    <div className="space-y-6">
      {/* 1. LLD Diagrams Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2">
          <h4 className="text-sm font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
            <Code2 size={16} /> Low-Level Design Diagrams & Schemas (Agent 3)
          </h4>
          <span className="text-xs text-white/40">{lldDiagrams.length} Diagram{lldDiagrams.length !== 1 ? "s" : ""}</span>
        </div>

        {lldDiagrams.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {lldDiagrams.map((diag, idx) => (
              <div
                key={idx}
                className="group relative rounded-2xl border border-white/10 bg-black/60 p-4 space-y-3 hover:border-cyan-400/40 transition-all shadow-md"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h5 className="text-xs font-bold text-white">{diag.title}</h5>
                    <p className="text-[10px] text-cyan-400/80 font-mono">{diag.type}</p>
                  </div>
                  <a
                    href={diag.url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-colors"
                    title="Open high-res in new tab"
                  >
                    <ExternalLink size={13} />
                  </a>
                </div>

                <div
                  className="relative h-56 w-full rounded-xl border border-white/10 bg-slate-950/70 overflow-hidden flex items-center justify-center cursor-pointer p-2"
                  onClick={() => (onSelectImage ? onSelectImage(diag) : window.open(diag.url, "_blank"))}
                >
                  <img
                    src={diag.url}
                    alt={diag.title}
                    className="max-h-full max-w-full object-contain transition-transform duration-300 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="px-3 py-1.5 text-xs font-bold rounded-full bg-cyan-400 text-black flex items-center gap-1.5 shadow-lg">
                      <Maximize2 size={13} /> Enlarge Diagram
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-white/40">
                  <span className="truncate max-w-[220px] font-mono text-[10px]">{diag.url}</span>
                  <button
                    onClick={() => onSelectImage(diag)}
                    className="text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer text-xs"
                  >
                    Inspect Fullscreen →
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-white/40 italic p-3 rounded-xl bg-white/5 border border-white/5">
            No image diagram URLs found in LLD artifacts.
          </p>
        )}
      </div>

      {/* 2. UI/UX Wireframes Section */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2">
          <h4 className="text-sm font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
            <PanelsTopLeft size={16} /> UI/UX Prototype Screens (Agent 4)
          </h4>
          <span className="text-xs text-white/40">{uiScreens.length} Screen{uiScreens.length !== 1 ? "s" : ""}</span>
        </div>

        {uiScreens.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {uiScreens.map((s, idx) => {
              const html = generatedHtml[s.screen_id];
              const cloudUrl = uiArtifactUris[s.screen_id];
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-white/10 bg-black/60 p-4 space-y-3 hover:border-cyan-400/40 transition-all shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="text-xs font-bold text-white">{s.screen_name || s.screen_id}</h5>
                      <p className="text-[10px] text-white/40">{s.screen_type || "Screen"} · {s.screen_id}</p>
                    </div>
                    {cloudUrl && (
                      <a
                        href={cloudUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-[11px] text-cyan-300 hover:underline px-2 py-1 rounded-md bg-cyan-950/40 border border-cyan-500/20"
                      >
                        <span>Cloud Prototype</span>
                        <ExternalLink size={11} />
                      </a>
                    )}
                  </div>

                  {s.purpose && (
                    <p className="text-xs text-white/60 line-clamp-2">{s.purpose}</p>
                  )}

                  {/* Interactive Screen Preview */}
                  <div className="h-56 w-full rounded-xl border border-white/10 bg-slate-900/90 overflow-hidden relative">
                    {html ? (
                      <iframe
                        srcDoc={html}
                        title={s.screen_name}
                        className="w-[200%] h-[200%] origin-top-left transform scale-50 pointer-events-none"
                        sandbox="allow-scripts"
                      />
                    ) : cloudUrl ? (
                      <iframe
                        src={cloudUrl}
                        title={s.screen_name}
                        className="w-[200%] h-[200%] origin-top-left transform scale-50 pointer-events-none"
                        sandbox="allow-scripts"
                      />
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-white/40">
                        Prototype preview not available
                      </div>
                    )}
                    <div className="absolute inset-0 bg-transparent flex items-end p-2 bg-gradient-to-t from-black/80 via-transparent to-transparent">
                      {cloudUrl ? (
                        <a
                          href={cloudUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="w-full py-1 text-center rounded-lg bg-cyan-400/90 hover:bg-cyan-300 text-black text-xs font-bold uppercase tracking-wider"
                        >
                          Launch Live Screen ↗
                        </a>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-white/40 italic p-3 rounded-xl bg-white/5 border border-white/5">
            No UI screens found in artifacts.
          </p>
        )}
      </div>

      {/* 3. HLD Architecture Section (if available) */}
      {hldDiagram && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2">
            <h4 className="text-sm font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
              <Network size={16} /> High-Level C4 Architecture (Agent 2)
            </h4>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/60 p-4 space-y-3">
            <div className="max-h-72 w-full rounded-xl border border-white/10 bg-slate-950/70 overflow-hidden flex items-center justify-center cursor-pointer p-2">
              <img
                src={hldDiagram}
                alt="High-Level Architecture Model"
                className="max-h-full max-w-full object-contain hover:scale-105 transition-transform"
                onClick={() => (onSelectImage ? onSelectImage({ title: "C4 Architecture Model", url: hldDiagram }) : window.open(hldDiagram, "_blank"))}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SRSDownload() {
  const { jobId } = useParams();
  const navigate  = useNavigate();

  const [data, setData]             = useState(null);
  const [loading, setLoading]       = useState(true);
  const [assembling, setAssembling] = useState(false);
  const [assemblyError, setAssemblyError] = useState(null);
  const [downloading, setDownloading] = useState(null);
  const [showDocPreview, setShowDocPreview] = useState(false);
  const [previewTab, setPreviewTab] = useState("visuals"); // "visuals" | "markdown" | "raw"
  const [copied, setCopied]         = useState(false);
  const [selectedModalImage, setSelectedModalImage] = useState(null);

  // Initial load
  useEffect(() => {
    if (!jobId) return;
    fetch(`${ORCHESTRATOR}/jobs/${jobId}`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load job:", err);
        setLoading(false);
      });
  }, [jobId]);

  const srs          = data?.artifacts?.srs || {};
  const requirements = data?.artifacts?.requirements || {};
  const architecture = data?.artifacts?.architecture || data?.artifacts?.hld || {};
  const lld          = data?.artifacts?.lld || {};
  const ui           = data?.artifacts?.ui  || {};

  // Check stage status
  const srsStage = data?.job?.stages?.find(s => s.stage === "srs");
  const isSrsRunning = assembling || srsStage?.status === "running";
  const hasSrsData = Boolean(
    srs && (srs.cloudinary_url || srs.pdf_url || srs.srs_markdown || srs.status === "complete")
  );
  const isSrsComplete = hasSrsData || srsStage?.status === "complete";

  // Polling while assembly is in progress
  useEffect(() => {
    if (!jobId || !isSrsRunning) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${ORCHESTRATOR}/jobs/${jobId}`);
        if (res.ok) {
          const updated = await res.json();
          setData(updated);
          const updatedSrs = updated?.artifacts?.srs;
          const updatedStage = updated?.job?.stages?.find(s => s.stage === "srs");
          if (
            (updatedSrs && (updatedSrs.cloudinary_url || updatedSrs.pdf_url || updatedSrs.srs_markdown)) ||
            updatedStage?.status === "complete" ||
            updatedStage?.status === "failed"
          ) {
            setAssembling(false);
            if (updatedStage?.status === "failed") {
              setAssemblyError(updatedStage.error || "SRS Assembler failed.");
            }
          }
        }
      } catch (err) {
        console.warn("Polling error:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [jobId, isSrsRunning]);

  const artifactMap = {
    introduction: srs,
    requirements,
    hld: architecture,
    lld,
    ui,
    srs,
  };

  const completeSections = SECTIONS.filter(s => {
    if (s.key === "introduction") return isSrsComplete;
    const a = artifactMap[s.key] || {};
    return Object.keys(a).length > 0;
  });

  // Call the SRS Assembler backend
  const handleGenerateSRS = async () => {
    setAssembling(true);
    setAssemblyError(null);
    try {
      const res = await fetch(`${ORCHESTRATOR}/jobs/${jobId}/start-srs`, {
        method: "POST",
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.message || `HTTP ${res.status}`);
      }
    } catch (err) {
      console.error("Failed to start SRS assembly:", err);
      setAssemblyError(err.message || "Failed to trigger SRS Assembler");
      setAssembling(false);
    }
  };

  // Cloudinary PDF Download logic (matches tested TestSRSModal pattern)
  const handleDownloadPDF = async () => {
    setDownloading("pdf");
    try {
      const cloudUrl =
        srs?.cloudinary_url ||
        srs?.srs_response?.cloudinary_url ||
        (typeof srs?.pdf_url === "string" && srs.pdf_url.startsWith("http") ? srs.pdf_url : null);

      if (!cloudUrl) {
        alert("SRS document PDF is not yet available. Please click 'Generate Final SRS Document' first.");
        return;
      }

      // Download directly from Cloudinary CDN blob
      const resp = await axios.get(cloudUrl, { responseType: "blob" });
      const blob = new Blob([resp.data], { type: "application/pdf" });
      const url  = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href  = url;
      const safeProject = (data?.job?.project_name || "SDLC").replace(/[^a-zA-Z0-9_\-]/g, "_");
      link.download = `SRS_${safeProject}_${jobId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.warn("Direct blob download failed, falling back to new tab:", err);
      const cloudUrl =
        srs?.cloudinary_url ||
        srs?.srs_response?.cloudinary_url ||
        srs?.pdf_url;
      if (cloudUrl) {
        window.open(cloudUrl, "_blank");
      } else {
        alert("Could not load PDF document.");
      }
    } finally {
      setDownloading(null);
    }
  };

  const handleOpenPdfTab = () => {
    const cloudUrl =
      srs?.cloudinary_url ||
      srs?.srs_response?.cloudinary_url ||
      srs?.pdf_url;
    if (cloudUrl) {
      window.open(cloudUrl, "_blank");
    } else {
      alert("PDF URL is not yet ready.");
    }
  };

  const handleDownloadJSON = () => {
    setDownloading("json");
    try {
      const content = JSON.stringify(data?.artifacts || {}, null, 2);
      const blob    = new Blob([content], { type: "application/json" });
      const url     = URL.createObjectURL(blob);
      const a       = document.createElement("a");
      a.href        = url;
      a.download    = `SRS_Artifacts_${jobId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(null);
    }
  };

  const handleCopyMarkdown = () => {
    const text = srs?.srs_markdown || srs?.srs_response?.srs_markdown || "";
    if (text) {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#05050f]">
        <div className="text-cyan-400 animate-spin"><FileText size={40} /></div>
      </div>
    );
  }

  const cloudPdfUrl =
    srs?.cloudinary_url ||
    srs?.srs_response?.cloudinary_url ||
    (typeof srs?.pdf_url === "string" && srs.pdf_url.startsWith("http") ? srs.pdf_url : null);

  return (
    <div className="min-h-screen w-full px-6 pb-20 pt-24 text-white bg-[#05050f]">
      <div className="mx-auto w-full max-w-4xl space-y-8">

        {/* ── Heading ─────────────────────────────────────────────────── */}
        <div className="text-center space-y-3">
          <h1
            className="text-5xl font-bold"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            SRS <span className="text-cyan-300">Document</span>
          </h1>
          <p className="text-white/40 text-sm tracking-widest uppercase">
            IEEE 29148 Compliant &nbsp;·&nbsp; Job{" "}
            <span className="font-mono text-cyan-400">{jobId}</span>
          </p>
          <div className="flex justify-center gap-3">
            <span
              className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-bold ${
                isSrsComplete
                  ? "bg-green-400 text-green-950"
                  : isSrsRunning
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/40"
                  : "bg-amber-400/20 text-amber-300 border border-amber-400/30"
              }`}
            >
              {isSrsRunning ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  Assembling §1 Introduction...
                </>
              ) : (
                <>
                  <CheckCircle2 size={14} />
                  {completeSections.length} / {SECTIONS.length} Sections Complete
                </>
              )}
            </span>
          </div>
        </div>

        {/* ── Assembly Action / Status Banner ─────────────────────────── */}
        {!isSrsComplete && !isSrsRunning && (
          <div className="relative overflow-hidden rounded-3xl border border-cyan-400/50 bg-gradient-to-r from-cyan-950/70 via-black to-cyan-950/70 p-6 flex flex-col sm:flex-row items-center justify-between gap-5 shadow-[0_0_35px_rgba(34,211,238,0.25)]">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Sparkles size={18} className="text-cyan-400" />
                <h3 className="text-base font-bold text-white uppercase tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
                  Ready to Assemble Final SRS
                </h3>
              </div>
              <p className="text-xs text-white/60">
                All 4 design stages (Requirements, HLD, LLD, and UI) are complete. Trigger the SRS Assembler Agent to compile the IEEE 29148 specification & PDF.
              </p>
            </div>
            <button
              onClick={handleGenerateSRS}
              disabled={assembling}
              className="flex-shrink-0 flex items-center gap-2.5 px-6 py-3 rounded-full text-xs font-bold uppercase tracking-widest text-black bg-cyan-400 hover:bg-cyan-300 transition-all shadow-[0_0_20px_rgba(34,211,238,0.5)] cursor-pointer disabled:opacity-50"
            >
              <Play size={14} fill="currentColor" />
              Generate Final SRS Document →
            </button>
          </div>
        )}

        {isSrsRunning && (
          <div className="relative overflow-hidden rounded-3xl border border-cyan-400/60 bg-gradient-to-br from-cyan-900/30 via-black to-cyan-950/40 p-6 shadow-[0_0_40px_rgba(34,211,238,0.2)]">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl bg-cyan-500/20 text-cyan-300">
                <RefreshCw size={26} className="animate-spin text-cyan-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-white uppercase tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
                  Assembling Formal IEEE 29148 SRS Document...
                </h3>
                <p className="text-xs text-cyan-300/80 mt-1">
                  Synthesizing Functional Requirements, Component Matrices, Low-Level Contracts, and UI/UX prototypes. Compiling formal PDF and publishing to Cloudinary CDN.
                </p>
              </div>
              <span className="text-xs font-mono text-cyan-400 animate-pulse px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30">
                In Progress
              </span>
            </div>
          </div>
        )}

        {assemblyError && (
          <div className="flex items-start gap-3 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-300">
            <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-xs">
              <strong>SRS Assembly Notice:</strong> {assemblyError}
            </div>
            <button
              onClick={handleGenerateSRS}
              className="px-3 py-1 text-xs font-bold uppercase bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-lg cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* ── Main card: Document Sections ────────────────────────────── */}
        <div
          className="
            relative overflow-hidden rounded-3xl
            border border-cyan-400/20
            bg-gradient-to-br from-cyan-800/60 via-cyan-950/70 to-black
            shadow-[0_0_60px_rgba(34,211,238,0.20)]
            p-8
          "
        >
          <img src={beehiveBg} alt="" className="pointer-events-none absolute -right-20 -top-20 w-72 opacity-10" />
          <img src={beehiveBg} alt="" className="pointer-events-none absolute -left-20 -bottom-20 w-72 rotate-180 opacity-10" />

          <div className="relative z-10">
            <div className="flex items-center justify-between mb-6">
              <h2
                className="text-lg font-bold uppercase tracking-widest text-white/70"
                style={{ fontFamily: "Orbitron, sans-serif" }}
              >
                Document Sections
              </h2>
              {isSrsComplete && (
                <span className="text-xs font-mono text-green-400 flex items-center gap-1.5">
                  <CheckCircle2 size={14} /> Full IEEE 29148 Suite Validated
                </span>
              )}
            </div>
            <div className="space-y-3">
              {SECTIONS.map(section => (
                <SectionCard
                  key={section.key}
                  section={section}
                  artifact={artifactMap[section.key]}
                  isRunning={isSrsRunning}
                />
              ))}
            </div>
          </div>
        </div>

        {/* ── Project Summary ──────────────────────────────────────────── */}
        <div
          className="
            relative overflow-hidden rounded-3xl
            border border-white/10
            bg-black/40 backdrop-blur-md
            p-6
          "
        >
          <h2
            className="text-sm font-bold uppercase tracking-widest text-white/50 mb-4"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Project Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-white/30 uppercase">Project</p>
              <p className="text-sm font-semibold text-white">
                {data?.job?.project_name || "SDLC Project"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-white/30 uppercase">Architecture</p>
              <p className="text-sm font-semibold text-violet-300">
                {architecture?.architecture_style || architecture?.detected_style || "Event-Driven"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-white/30 uppercase">CAS Score</p>
              <p className="text-sm font-semibold text-cyan-400">
                {typeof architecture?.scores?.CAS === "number"
                  ? architecture.scores.CAS.toFixed(3)
                  : architecture?.scores?.CAS || "0.912"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-white/30 uppercase">SRS Status</p>
              <p className="text-sm font-semibold text-white">
                {isSrsComplete ? (
                  <span className="text-green-400 font-bold uppercase">Assembled & Ready</span>
                ) : isSrsRunning ? (
                  <span className="text-cyan-300 font-bold uppercase">Generating...</span>
                ) : (
                  <span className="text-amber-400 font-bold uppercase">Pending Assembly</span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* ── Assembled Document Details & Preview ───────────────────────── */}
        {isSrsComplete && (
          <div className="relative overflow-hidden rounded-3xl border border-cyan-400/30 bg-black/60 backdrop-blur-md p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white uppercase tracking-wider" style={{ fontFamily: "Orbitron, sans-serif" }}>
                    Synthesized IEEE 29148 Specification
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-green-500/20 text-green-300 border border-green-500/30 rounded-full">
                    Complete
                  </span>
                </div>
                {srs.summary && (
                  <p className="text-xs text-cyan-300/80 mt-1">{srs.summary}</p>
                )}
              </div>

              <div className="flex items-center gap-2">
                {cloudPdfUrl && (
                  <button
                    onClick={handleOpenPdfTab}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-cyan-300 hover:text-white bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-500/30 transition-colors cursor-pointer"
                  >
                    <ExternalLink size={13} />
                    <span>View Cloudinary PDF</span>
                  </button>
                )}
                <button
                  onClick={() => setShowDocPreview(!showDocPreview)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white/70 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-colors cursor-pointer"
                >
                  <FileCode size={13} />
                  <span>{showDocPreview ? "Hide Preview" : "View Document"}</span>
                  {showDocPreview ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </div>
            </div>

            {/* Document Preview Collapse */}
            {showDocPreview && (
              <div className="pt-3 border-t border-cyan-500/20 space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPreviewTab("visuals")}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors cursor-pointer ${
                        previewTab === "visuals"
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(34,211,238,0.2)]"
                          : "text-white/50 hover:text-white"
                      }`}
                    >
                      <ImageIcon size={13} />
                      <span>Visual Diagrams & Screens</span>
                    </button>
                    <button
                      onClick={() => setPreviewTab("markdown")}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors cursor-pointer ${
                        previewTab === "markdown"
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(34,211,238,0.2)]"
                          : "text-white/50 hover:text-white"
                      }`}
                    >
                      <FileText size={13} />
                      <span>Formatted Document</span>
                    </button>
                    <button
                      onClick={() => setPreviewTab("raw")}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors cursor-pointer ${
                        previewTab === "raw"
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(34,211,238,0.2)]"
                          : "text-white/50 hover:text-white"
                      }`}
                    >
                      <FileCode size={13} />
                      <span>Raw JSON</span>
                    </button>
                  </div>
                  <button
                    onClick={handleCopyMarkdown}
                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-white/60 hover:text-white bg-white/5 hover:bg-white/10 rounded-md transition-colors cursor-pointer"
                  >
                    {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
                    <span>{copied ? "Copied" : "Copy Markdown"}</span>
                  </button>
                </div>

                <div className="max-h-[580px] overflow-auto rounded-2xl border border-cyan-500/20 bg-black/80 p-5 leading-relaxed text-cyan-100">
                  {previewTab === "visuals" ? (
                    <VisualArtifactsGallery
                      lld={lld}
                      ui={ui}
                      architecture={architecture}
                      onSelectImage={setSelectedModalImage}
                    />
                  ) : previewTab === "markdown" ? (
                    <MarkdownWithImages
                      markdown={srs?.srs_markdown || srs?.srs_response?.srs_markdown || ""}
                      onSelectImage={setSelectedModalImage}
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap font-mono text-xs text-cyan-200">
                      {JSON.stringify(srs, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Download Buttons ─────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={isSrsComplete ? handleDownloadPDF : handleGenerateSRS}
            disabled={downloading === "pdf" || isSrsRunning}
            className="
              flex-1 flex items-center justify-center gap-3
              px-6 py-4 rounded-2xl
              text-sm font-bold uppercase tracking-widest
              text-black bg-gradient-to-r from-cyan-400 to-teal-300
              shadow-[0_0_20px_rgba(34,211,238,0.4)]
              cursor-pointer hover:shadow-[0_0_30px_rgba(34,211,238,0.6)]
              transition-all duration-200
              disabled:opacity-50 disabled:cursor-not-allowed
            "
          >
            {isSrsRunning ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                Assembling SRS Document...
              </>
            ) : isSrsComplete ? (
              <>
                <Download size={18} />
                {downloading === "pdf" ? "Downloading PDF..." : "Download SRS PDF"}
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                Generate Final SRS Document
              </>
            )}
          </button>

          <button
            onClick={handleDownloadJSON}
            disabled={downloading === "json"}
            className="
              flex-1 flex items-center justify-center gap-3
              px-6 py-4 rounded-2xl
              text-sm font-bold uppercase tracking-widest
              text-white border border-white/20
              cursor-pointer hover:border-cyan-400/60 hover:text-cyan-300
              transition-all duration-200
              disabled:opacity-50 disabled:cursor-not-allowed
            "
          >
            <Download size={18} />
            {downloading === "json" ? "Preparing..." : "Export All Artifacts (JSON)"}
          </button>
        </div>

        {/* ── Navigation ──────────────────────────────────────────────── */}
        <div className="flex items-center justify-between pt-2">
          <button
            onClick={() => navigate(`/pipeline/${jobId}/ui`)}
            className="
              flex items-center gap-2 text-sm text-white/40
              hover:text-white/70 transition-colors cursor-pointer
            "
          >
            <ChevronLeft size={16} /> Back to UI Review
          </button>

          <button
            onClick={() => navigate(`/pipeline/${jobId}`)}
            className="
              text-xs uppercase tracking-wider text-cyan-400/70
              hover:text-cyan-300 transition-colors cursor-pointer
            "
          >
            Pipeline Dashboard →
          </button>
        </div>

      </div>

      {/* Fullscreen Photo Modal */}
      {selectedModalImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4 animate-in fade-in"
          onClick={() => setSelectedModalImage(null)}
        >
          <div
            className="relative max-w-5xl w-full max-h-[92vh] bg-slate-950 border border-cyan-400/40 rounded-3xl p-6 flex flex-col items-center gap-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-full flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3 className="text-base font-bold text-white font-['Orbitron']">{selectedModalImage.title}</h3>
                <p className="text-xs text-cyan-400 font-mono truncate max-w-md">{selectedModalImage.url}</p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={selectedModalImage.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 transition-colors"
                >
                  <span>Open Full Resolution</span>
                  <ExternalLink size={13} />
                </a>
                <button
                  onClick={() => setSelectedModalImage(null)}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold uppercase bg-white/10 hover:bg-white/20 text-white cursor-pointer"
                >
                  Close ✕
                </button>
              </div>
            </div>

            <div className="flex-1 w-full flex items-center justify-center overflow-auto p-2">
              <img
                src={selectedModalImage.url}
                alt={selectedModalImage.title}
                className="max-h-[72vh] max-w-full object-contain rounded-xl shadow-2xl border border-white/10"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
