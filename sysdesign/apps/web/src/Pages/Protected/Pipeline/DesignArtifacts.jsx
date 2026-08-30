/**
 * DesignArtifacts.jsx
 *
 * Tabbed view of all design artifacts from Agents 3 (LLD) and 4 (UI):
 *   Tab 1: Architecture diagram (Mermaid / PlantUML image from Agent 2)
 *   Tab 2: Class Diagram (PNG from Agent 3)
 *   Tab 3: Sequence Diagram (PNG from Agent 3)
 *   Tab 4: UI Screens (HTML iframes from Agent 4)
 *
 * Design: same Orbitron / cyan / beehive card system.
 */

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Network,
  Code2,
  GitBranch,
  PanelsTopLeft,
  FileText,
  Download,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import beehiveBg from "../../../Images/beehive-bg.png";

const ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL || "http://127.0.0.1:8000";

const TABS = [
  { key: "architecture", label: "Architecture",   Icon: Network },
  { key: "class",        label: "Class Diagram",  Icon: Code2   },
  { key: "sequence",     label: "Sequence Diag.", Icon: GitBranch },
  { key: "screens",      label: "UI Screens",     Icon: PanelsTopLeft },
];

function TabButton({ tab, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium
        transition-all duration-200 cursor-pointer
        ${active
          ? "bg-cyan-400/20 border border-cyan-400/60 text-cyan-300"
          : "border border-white/10 text-white/50 hover:border-white/30 hover:text-white/80"
        }
      `}
    >
      <tab.Icon size={15} />
      {tab.label}
    </button>
  );
}

function ArtifactImage({ uri, alt }) {
  if (!uri) {
    return (
      <div className="flex items-center justify-center h-64 text-white/30 text-sm border border-white/10 rounded-2xl">
        Artifact not yet generated.
      </div>
    );
  }

  // Local file paths — can't be loaded in browser. Show the path + download hint.
  if (uri.startsWith("D:/") || uri.startsWith("d:/") || uri.includes("AgentOutputs")) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 p-3 rounded-xl bg-white/5 border border-white/10">
          <FileText className="text-cyan-400 flex-shrink-0" size={18} />
          <span className="font-mono text-xs text-white/60 break-all">{uri}</span>
        </div>
        <p className="text-xs text-white/30">
          This artifact is saved locally. View it in your file explorer or deploy to Cloudflare R2 for in-browser preview.
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      <img
        src={uri}
        alt={alt}
        className="w-full rounded-2xl border border-white/10 bg-black/30"
        onError={e => {
          e.target.style.display = "none";
          e.target.nextSibling.style.display = "flex";
        }}
      />
      <div className="hidden items-center justify-center h-64 text-white/30 text-sm border border-white/10 rounded-2xl">
        Could not load image from: {uri}
      </div>
    </div>
  );
}

function ScreenTabs({ screens }) {
  const [activeScreen, setActiveScreen] = useState(0);
  if (!screens || screens.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-white/30 text-sm border border-white/10 rounded-2xl">
        UI screens not yet generated.
      </div>
    );
  }

  const screen = screens[activeScreen];

  return (
    <div className="space-y-4">
      {/* Screen selector */}
      <div className="flex flex-wrap gap-2">
        {screens.map((s, i) => (
          <button
            key={i}
            onClick={() => setActiveScreen(i)}
            className={`
              px-3 py-1.5 text-xs rounded-full border transition-all duration-200 cursor-pointer
              ${i === activeScreen
                ? "border-pink-400/60 text-pink-300 bg-pink-400/10"
                : "border-white/10 text-white/40 hover:text-white/70"
              }
            `}
          >
            {s.screen_name || s.name || `Screen ${i + 1}`}
          </button>
        ))}
      </div>

      {/* HTML preview iframe */}
      {screen?.html_content ? (
        <iframe
          srcDoc={screen.html_content}
          className="w-full h-[500px] rounded-2xl border border-white/10 bg-white"
          title={screen.screen_name || "UI Screen"}
          sandbox="allow-scripts"
        />
      ) : screen?.uri ? (
        <ArtifactImage uri={screen.uri} alt={screen.screen_name || "UI Screen"} />
      ) : (
        <div className="flex items-center justify-center h-64 text-white/30 text-sm border border-white/10 rounded-2xl">
          Screen content unavailable.
        </div>
      )}

      {/* Screen metadata */}
      {screen?.usability_score !== undefined && (
        <div className="flex items-center gap-4 text-sm text-white/50">
          <span>Usability: <strong className="text-cyan-400">{(screen.usability_score * 100).toFixed(0)}%</strong></span>
          {screen?.wcag_pass !== undefined && (
            <span>WCAG: <strong className={screen.wcag_pass ? "text-green-400" : "text-red-400"}>{screen.wcag_pass ? "Pass" : "Fail"}</strong></span>
          )}
        </div>
      )}
    </div>
  );
}

export default function DesignArtifacts() {
  const { jobId }   = useParams();
  const navigate    = useNavigate();
  const [activeTab, setActiveTab] = useState("architecture");
  const [artifacts, setArtifacts] = useState({});
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    if (!jobId) return;
    fetch(`${ORCHESTRATOR}/jobs/${jobId}`)
      .then(r => r.json())
      .then(data => {
        setArtifacts(data.artifacts || {});
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [jobId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-cyan-400 animate-spin"><Network size={40} /></div>
      </div>
    );
  }

  const arch = artifacts.architecture || {};
  const lld  = artifacts.lld || {};
  const ui   = artifacts.ui  || {};

  // Extract artifact URIs from each agent's output
  const archDiagramUri  = arch?.artifact_uris?.mermaid || arch?.artifact_uris?.plantuml || arch?.artifact_uris?.diagram;
  const classUri        = lld?.artifact_uris?.class_diagram || lld?.diagrams?.class;
  const sequenceUri     = lld?.artifact_uris?.sequence_diagram || lld?.diagrams?.sequence;
  const screens         = ui?.screens || ui?.artifact_uris?.screens || [];

  return (
    <div className="min-h-screen w-full px-6 pb-20 pt-24 text-white">
      <div className="mx-auto w-full max-w-5xl space-y-8">

        {/* ── Heading ─────────────────────────────────────────────────── */}
        <div className="text-center space-y-2">
          <h1
            className="text-5xl font-bold"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Design <span className="text-cyan-300">Artifacts</span>
          </h1>
          <p className="text-white/40 text-sm tracking-widest">
            Job <span className="font-mono text-cyan-400">{jobId}</span>
          </p>
        </div>

        {/* ── Tab Navigation ───────────────────────────────────────────── */}
        <div className="flex flex-wrap gap-2">
          {TABS.map(tab => (
            <TabButton
              key={tab.key}
              tab={tab}
              active={activeTab === tab.key}
              onClick={() => setActiveTab(tab.key)}
            />
          ))}
        </div>

        {/* ── Content Card ─────────────────────────────────────────────── */}
        <div
          className="
            relative overflow-hidden rounded-3xl
            border border-cyan-400/20
            bg-gradient-to-br from-cyan-800/40 via-cyan-950/60 to-black
            shadow-[0_0_50px_rgba(34,211,238,0.12)]
            p-8
          "
        >
          <img src={beehiveBg} alt="" className="pointer-events-none absolute -right-20 -top-20 w-72 opacity-8" />
          <img src={beehiveBg} alt="" className="pointer-events-none absolute -left-20 -bottom-20 w-72 rotate-180 opacity-8" />

          <div className="relative z-10">
            {activeTab === "architecture" && (
              <div className="space-y-4">
                <h2
                  className="text-lg font-bold uppercase tracking-widest text-white/70"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  System Architecture Diagram
                </h2>
                <ArtifactImage uri={archDiagramUri} alt="System Architecture" />
                {arch?.detected_style && (
                  <p className="text-xs text-white/40">
                    Style: <strong className="text-violet-300">{arch.detected_style}</strong>
                    &nbsp;·&nbsp;
                    Components: <strong className="text-cyan-300">{arch.components?.length || "—"}</strong>
                  </p>
                )}
              </div>
            )}

            {activeTab === "class" && (
              <div className="space-y-4">
                <h2
                  className="text-lg font-bold uppercase tracking-widest text-white/70"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  Class Diagram
                </h2>
                <ArtifactImage uri={classUri} alt="Class Diagram" />
              </div>
            )}

            {activeTab === "sequence" && (
              <div className="space-y-4">
                <h2
                  className="text-lg font-bold uppercase tracking-widest text-white/70"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  Sequence Diagram
                </h2>
                <ArtifactImage uri={sequenceUri} alt="Sequence Diagram" />
              </div>
            )}

            {activeTab === "screens" && (
              <div className="space-y-4">
                <h2
                  className="text-lg font-bold uppercase tracking-widest text-white/70"
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                >
                  UI Screen Prototypes
                </h2>
                <ScreenTabs screens={Array.isArray(screens) ? screens : []} />
              </div>
            )}
          </div>
        </div>

        {/* ── Actions ─────────────────────────────────────────────────── */}
        <div className="flex justify-end gap-4">
          <button
            onClick={() => navigate(`/pipeline/${jobId}/architecture`)}
            className="
              flex items-center gap-2 px-5 py-2.5
              text-sm font-semibold uppercase tracking-widest
              text-white border border-white/20 rounded-full cursor-pointer
              hover:border-cyan-400/60 hover:text-cyan-300 transition-colors
            "
          >
            ← Architecture
          </button>
          <button
            onClick={() => navigate(`/pipeline/${jobId}/srs`)}
            className="
              flex items-center gap-2 px-5 py-2.5
              text-sm font-semibold uppercase tracking-widest
              text-black bg-cyan-400 rounded-full cursor-pointer
              hover:bg-cyan-300 transition-colors
            "
          >
            Download SRS <ChevronRight size={16} />
          </button>
        </div>

      </div>
    </div>
  );
}
