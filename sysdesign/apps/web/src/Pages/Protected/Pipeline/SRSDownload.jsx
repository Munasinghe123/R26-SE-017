/**
 * SRSDownload.jsx
 *
 * Final pipeline page — shows the IEEE 29148-compliant SRS summary
 * and provides download buttons for the complete document.
 *
 * Design: same Orbitron / cyan / beehive card system.
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
} from "lucide-react";
import beehiveBg from "../../../Images/beehive-bg.png";

const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "http://127.0.0.1:8000";
const AGENT1       = import.meta.env.VITE_AGENT1_URL || "http://127.0.0.1:8001";

const SECTIONS = [
  { num: "§1", title: "Introduction",            Icon: FileText,    key: "introduction" },
  { num: "§2", title: "Requirements Overview",   Icon: ClipboardList, key: "requirements" },
  { num: "§3", title: "HLD Architecture",        Icon: Network,     key: "hld" },
  { num: "§4", title: "Low-Level Design",        Icon: Code2,       key: "lld" },
  { num: "§5", title: "UI/UX Specifications",    Icon: PanelsTopLeft, key: "ui" },
];

function SectionCard({ section, artifact }) {
  const { Icon } = section;
  const hasData  = artifact && Object.keys(artifact).length > 0;

  return (
    <div
      className={`
        flex items-center gap-4 p-4 rounded-2xl border transition-all duration-300
        ${hasData
          ? "border-cyan-400/20 bg-cyan-950/30"
          : "border-white/5 bg-white/5 opacity-50"
        }
      `}
    >
      <div className="flex-shrink-0 p-2.5 rounded-xl bg-cyan-400/10">
        <Icon className="text-cyan-400" size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/30 font-mono">{section.num}</span>
          <span className="text-sm font-semibold text-white">{section.title}</span>
        </div>
        <p className="text-xs text-white/40 mt-0.5">
          {hasData ? "✓ Content generated" : "Pending..."}
        </p>
      </div>
      <CheckCircle2
        className={hasData ? "text-green-400" : "text-white/20"}
        size={18}
      />
    </div>
  );
}

export default function SRSDownload() {
  const { jobId } = useParams();
  const navigate  = useNavigate();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    if (!jobId) return;
    fetch(`${ORCHESTRATOR}/jobs/${jobId}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [jobId]);

  const srs          = data?.artifacts?.srs || {};
  const requirements = data?.artifacts?.requirements || {};
  const architecture = data?.artifacts?.architecture || {};
  const lld          = data?.artifacts?.lld || {};
  const ui           = data?.artifacts?.ui  || {};

  const artifactMap = {
    requirements,
    hld: architecture,
    lld,
    ui,
    srs,
  };

  const handleDownloadPDF = async () => {
    setDownloading("pdf");
    try {
      const resp = await fetch(`${ORCHESTRATOR}/jobs/${jobId}/srs/pdf`);
      if (resp.ok) {
        const blob = await resp.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href     = url;
        a.download = `SRS_${jobId}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert("PDF not yet generated. The SRS service may still be processing.");
      }
    } catch {
      alert("Could not download PDF. Ensure the SRS Assembler service is running.");
    } finally {
      setDownloading(null);
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-cyan-400 animate-spin"><FileText size={40} /></div>
      </div>
    );
  }

  const completeSections = SECTIONS.filter(s => {
    const a = artifactMap[s.key] || {};
    return Object.keys(a).length > 0;
  });

  return (
    <div className="min-h-screen w-full px-6 pb-20 pt-24 text-white">
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
          <div className="flex justify-center">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-bold bg-green-400 text-green-900">
              <CheckCircle2 size={14} />
              {completeSections.length} / {SECTIONS.length} Sections Complete
            </span>
          </div>
        </div>

        {/* ── Main card ────────────────────────────────────────────────── */}
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
            <h2
              className="text-lg font-bold uppercase tracking-widest text-white/70 mb-6"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              Document Sections
            </h2>
            <div className="space-y-3">
              {SECTIONS.map(section => (
                <SectionCard
                  key={section.key}
                  section={section}
                  artifact={artifactMap[section.key]}
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
                {data?.job?.project_name || "—"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-white/30 uppercase">Architecture</p>
              <p className="text-sm font-semibold text-violet-300">
                {architecture?.detected_style || "—"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-white/30 uppercase">CAS Score</p>
              <p className="text-sm font-semibold text-cyan-400">
                {architecture?.scores?.CAS?.toFixed(3) || "—"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-white/30 uppercase">Components</p>
              <p className="text-sm font-semibold text-white">
                {architecture?.components?.length ?? "—"}
              </p>
            </div>
          </div>
        </div>

        {/* ── Download Buttons ─────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={handleDownloadPDF}
            disabled={downloading === "pdf"}
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
            <Download size={18} />
            {downloading === "pdf" ? "Generating PDF..." : "Download SRS PDF"}
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
        <div className="flex justify-start">
          <button
            onClick={() => navigate(`/pipeline/${jobId}/artifacts`)}
            className="
              flex items-center gap-2 text-sm text-white/40
              hover:text-white/70 transition-colors cursor-pointer
            "
          >
            <ChevronLeft size={16} /> Back to Artifacts
          </button>
        </div>

      </div>
    </div>
  );
}
