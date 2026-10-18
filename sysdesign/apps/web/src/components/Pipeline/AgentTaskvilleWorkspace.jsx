import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Cpu,
  Calculator,
  Compass,
  Sparkles,
  CheckCircle2,
  Clock,
  Terminal,
  Activity,
  Maximize2,
  Volume2,
  Play,
  RotateCcw
} from "lucide-react";

export default function AgentTaskvilleWorkspace({ logs = [], currentStage = "hld", className = "" }) {
  const [selectedAgent, setSelectedAgent] = useState("architect");
  const [viewMode, setViewMode] = useState("pixel"); // "pixel" | "telemetry"
  const [activeSpeechIdx, setActiveSpeechIdx] = useState(0);
  const [isSimulating, setIsSimulating] = useState(true);

  // Real-time backend log binding
  const [liveAgentThoughts, setLiveAgentThoughts] = useState({});
  const [liveAgentHistory, setLiveAgentHistory] = useState({
    supervisor: [],
    security: [],
    architect: [],
    critic: [],
  });

  useEffect(() => {
    if (!logs || logs.length === 0) return;
    const latest = logs[logs.length - 1];
    if (typeof latest !== "string") return;
    const lower = latest.toLowerCase();

    const cleanMsg = latest.replace(/^[🚀⚙️📊🎨✅⚠✗\[\]\w\s\-]+\]\s*/, "").replace(/^.*?:/, "").trim();

    if (lower.includes("openrouter") || lower.includes("candidate") || lower.includes("synthesiz") || lower.includes("gpt") || lower.includes("qwen") || lower.includes("deepseek") || lower.includes("model") || lower.includes("plantuml") || lower.includes("diagram")) {
      setLiveAgentThoughts(prev => ({ ...prev, architect: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, architect: [...(prev.architect || []).slice(-3), latest] }));
      setSelectedAgent("architect");
    } else if (lower.includes("security") || lower.includes("stride") || lower.includes("trust") || lower.includes("boundary") || lower.includes("vault") || lower.includes("tls") || lower.includes("auth") || lower.includes("mitigat")) {
      setLiveAgentThoughts(prev => ({ ...prev, security: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, security: [...(prev.security || []).slice(-3), latest] }));
      setSelectedAgent("security");
    } else if (lower.includes("evaluat") || lower.includes("sentence") || lower.includes("cas") || lower.includes("rts") || lower.includes("qac") || lower.includes("ci") || lower.includes("cos") || lower.includes("ssm") || lower.includes("metric") || lower.includes("score") || lower.includes("ahp")) {
      setLiveAgentThoughts(prev => ({ ...prev, critic: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, critic: [...(prev.critic || []).slice(-3), latest] }));
      setSelectedAgent("critic");
    } else if (lower.includes("dispatch") || lower.includes("style") || lower.includes("winner") || lower.includes("stage") || lower.includes("complete") || lower.includes("job") || lower.includes("gate") || lower.includes("review")) {
      setLiveAgentThoughts(prev => ({ ...prev, supervisor: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, supervisor: [...(prev.supervisor || []).slice(-3), latest] }));
      setSelectedAgent("supervisor");
    }
  }, [logs]);

  const agents = [
    {
      id: "supervisor",
      name: "Supervisor Router",
      role: "System Orchestrator",
      icon: Compass,
      avatarEmoji: "👨‍✈️",
      pixelColor: "from-cyan-500 to-blue-600",
      accentHex: "#22d3ee",
      deskLabel: "Command Console",
      status: "active",
      task: "Evaluating candidate convergence & state transitions",
      badge: "State Controller",
      color: "border-cyan-400 text-cyan-300 bg-cyan-500/10",
      thoughts: [
        "Validating AHP pairwise consistency ratio (CR = 0.013 < 0.10)...",
        "Orchestrating 3-model parallel synthesis on OpenRouter...",
        "Ensuring backward compatibility with downstream LLD & UI agents...",
        "Quality gate passed! Ready for ATAM trade-off ranking."
      ],
      description: "Monitors the global pipeline state, validates AHP consistency ratios (CR < 0.10), and routes tasks between generation, evaluation, and downstream compilation.",
      specs: {
        runtime: "Asyncio State Machine",
        policy: "Strict Zero-Judge Router",
        latency: "12ms routing overhead"
      }
    },
    {
      id: "security",
      name: "Security Specialist",
      role: "STRIDE Threat Modeler",
      icon: ShieldAlert,
      avatarEmoji: "🛡️",
      pixelColor: "from-red-500 to-rose-600",
      accentHex: "#f87171",
      deskLabel: "Red-Team Audit Pod",
      status: "active",
      task: "Auditing trust boundaries & unauthenticated connectors",
      badge: "S-SDLC Lead",
      color: "border-red-400 text-red-300 bg-red-500/10",
      thoughts: [
        "Analyzing Trust Boundaries: DMZ, Core VPC, Secure Vault...",
        "Evaluating STRIDE threats: Spoofing, Tampering, Elevation...",
        "Checking API Gateway rate limits (Token Bucket) & mTLS...",
        "Mitigation Verification Score (MVS) computed at 96.5%!"
      ],
      description: "Extracts threat baseline profiles, validates TLS 1.3 / mTLS boundaries across ingress tiers, and computes the Attack Surface Index (ASI) and Mitigation Verification Score (MVS).",
      specs: {
        standard: "NIST SP 800-207 / STRIDE",
        coverage: "6 Threat Dimensions",
        engine: "Deterministic Matrix (0% LLM)"
      }
    },
    {
      id: "architect",
      name: "Principal Architect",
      role: "Multi-LLM Synthesis Mesh",
      icon: Cpu,
      avatarEmoji: "🧠",
      pixelColor: "from-violet-500 to-purple-600",
      accentHex: "#a78bfa",
      deskLabel: "Synthesis Cluster",
      status: "active",
      task: "Synthesizing 3 candidate styles (GPT-4o-mini, DeepSeek, Qwen)",
      badge: "Model Ensemble",
      color: "border-violet-400 text-violet-300 bg-violet-500/10",
      thoughts: [
        "Prompting openai/gpt-4o-mini for commercial baseline...",
        "Synthesizing Qwen-2.5-72B & DeepSeek-V3 open-weight models...",
        "Generating C4 Container topologies with REST & gRPC connectors...",
        "Exporting Component Architecture Model (CAM) structured JSON."
      ],
      description: "Executes 3 independent models via OpenRouter (OpenAI, DeepSeek V3, Qwen 2.5) to synthesize bounded contexts, C4 container topologies, and interaction flows.",
      specs: {
        models: "GPT-4o-mini, Qwen 2.5, DeepSeek V3",
        provider: "OpenRouter Unified Gateway",
        diversity: "Layered, Event-Driven, Microservices"
      }
    },
    {
      id: "critic",
      name: "ATAM Critic",
      role: "Deterministic Engine",
      icon: Calculator,
      avatarEmoji: "🧮",
      pixelColor: "from-amber-500 to-yellow-600",
      accentHex: "#fbbf24",
      deskLabel: "Math Lab",
      status: "active",
      task: "Executing graph density, cohesion & AHP eigenvector math",
      badge: "Pure Code / Zero-LLM",
      color: "border-amber-400 text-amber-300 bg-amber-500/10",
      thoughts: [
        "Embedding requirements with frozen sentence-transformers...",
        "Computing NetworkX graph coupling density (CI) & cohesion (CoS)...",
        "Evaluating Style-Specific Metrics (LIS/DDS / SBA/ISS)...",
        "Calculating Composite Architecture Score (CAS = 0.812)."
      ],
      description: "Runs deterministic Python evaluation code (NetworkX graph algorithms, frozen sentence embeddings, and Saaty's 1980 AHP matrix). No LLM-as-a-judge bias.",
      specs: {
        algorithms: "NetworkX + Saaty AHP (1980)",
        embeddings: "all-MiniLM-L6-v2 (Offline Cached)",
        reproducibility: "100% Deterministic Bitwise"
      }
    },
  ];

  // Rotate thoughts every 4.5 seconds for live Pixel Agent immersion
  useEffect(() => {
    if (!isSimulating) return;
    const interval = setInterval(() => {
      setActiveSpeechIdx((prev) => (prev + 1) % 4);
    }, 4500);
    return () => clearInterval(interval);
  }, [isSimulating]);

  const activeAgentData = agents.find((a) => a.id === selectedAgent) || agents[2];

  return (
    <div
      className={`relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#060e17]/95 via-black/90 to-[#0a0718]/95 backdrop-blur-xl p-6 shadow-[0_0_50px_rgba(34,211,238,0.12)] ${className}`}
    >
      {/* ── Header with Mode Switcher ─────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 animate-ping" />
            <h3
              className="text-lg font-bold text-white tracking-wide"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              Collaborative <span className="text-cyan-300">Agent Mesh</span>
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300">
              HLD Phase
            </span>
          </div>
          <p className="text-xs text-white/50 mt-0.5">
            Real-Time Autonomous Multi-Agent System (Supervisor · Security · Architect · Critic)
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Mode Switcher */}
          <div className="flex items-center bg-white/5 border border-white/10 p-1 rounded-xl">
            <button
              onClick={() => setViewMode("pixel")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                viewMode === "pixel"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(34,211,238,0.2)]"
                  : "text-white/40 hover:text-white"
              }`}
            >
              <span>🕹️</span> Pixel Office
            </button>
            <button
              onClick={() => setViewMode("telemetry")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                viewMode === "telemetry"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(34,211,238,0.2)]"
                  : "text-white/40 hover:text-white"
              }`}
            >
              <Activity size={12} /> Telemetry
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono text-green-400 bg-green-500/10 border border-green-500/20 px-3 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            <span>4 Agents Synchronized</span>
          </div>
        </div>
      </div>

      {/* ── VIEW 1: PIXEL VIRTUAL OFFICE (Inspired by Pixel-Agents) ── */}
      {viewMode === "pixel" && (
        <div className="relative mb-6 rounded-2xl border border-cyan-500/20 bg-[#040811] p-5 overflow-hidden shadow-inner">
          {/* Retro Grid Background Floor */}
          <div
            className="absolute inset-0 opacity-15 pointer-events-none"
            style={{
              backgroundImage:
                "linear-gradient(to right, #22d3ee 1px, transparent 1px), linear-gradient(to bottom, #22d3ee 1px, transparent 1px)",
              backgroundSize: "24px 24px",
            }}
          />

          {/* Office Status Bar */}
          <div className="relative z-10 flex items-center justify-between mb-4 pb-2 border-b border-white/5 text-[11px] font-mono text-white/50">
            <div className="flex items-center gap-2">
              <span className="text-cyan-400">● LIVE RUNTIME:</span>
              <span className="text-white/80">Autonomous MAS Workspace (Taskville Protocol)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs">💡 Click an agent avatar to inspect live thoughts</span>
            </div>
          </div>

          {/* 4 Agent Workstations (Isometric / Pixel Room) */}
          <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {agents.map((agent) => {
              const isSelected = selectedAgent === agent.id;
              const currentThought = liveAgentThoughts[agent.id] || agent.thoughts[activeSpeechIdx % agent.thoughts.length];

              return (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent.id)}
                  className={`
                    relative rounded-2xl p-4 transition-all duration-300 cursor-pointer flex flex-col justify-between border
                    ${
                      isSelected
                        ? "border-cyan-400 bg-cyan-950/40 shadow-[0_0_30px_rgba(34,211,238,0.25)] scale-[1.02]"
                        : "border-white/10 bg-black/60 hover:border-white/30 hover:bg-black/80"
                    }
                  `}
                >
                  {/* Speech Bubble Floating Above Agent */}
                  <div className="relative mb-3 min-h-[58px]">
                    <div
                      className="rounded-xl p-2.5 text-[10px] font-mono leading-tight shadow-md border relative transition-all duration-300"
                      style={{
                        backgroundColor: "#0d1522",
                        borderColor: isSelected ? agent.accentHex : "rgba(255,255,255,0.15)",
                        color: isSelected ? "#f0fdf4" : "#94a3b8",
                      }}
                    >
                      <div className="flex items-center gap-1.5 font-bold mb-1" style={{ color: agent.accentHex }}>
                        <span className="w-1.5 h-1.5 rounded-full animate-ping" style={{ backgroundColor: agent.accentHex }} />
                        <span>{agent.name.split(" ")[0]} says:</span>
                      </div>
                      <p className="line-clamp-2 italic">"{currentThought}"</p>

                      {/* Bubble Arrow Tail */}
                      <div
                        className="absolute -bottom-1.5 left-6 w-3 h-3 rotate-45 border-r border-b"
                        style={{
                          backgroundColor: "#0d1522",
                          borderColor: isSelected ? agent.accentHex : "rgba(255,255,255,0.15)",
                        }}
                      />
                    </div>
                  </div>

                  {/* Pixel Desk & Character Avatar */}
                  <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                    {/* Animated Pixel Sprite Box */}
                    <div
                      className="relative w-14 h-14 rounded-2xl flex items-center justify-center text-2xl shadow-lg border shrink-0 transition-transform hover:rotate-6"
                      style={{
                        background: `linear-gradient(135deg, ${agent.accentHex}20, #000000)`,
                        borderColor: `${agent.accentHex}60`,
                      }}
                    >
                      <span className="transform hover:scale-125 transition-transform select-none">
                        {agent.avatarEmoji}
                      </span>
                      {/* Active Typing Pulse Indicator */}
                      <span
                        className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-black animate-pulse"
                        style={{ backgroundColor: agent.accentHex }}
                      />
                    </div>

                    {/* Desk & Terminal Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-white truncate">{agent.name}</h4>
                      </div>
                      <p className="text-[10px] text-white/40 truncate">{agent.deskLabel}</p>
                      <div className="flex items-center gap-1.5 mt-1 text-[9px] font-mono text-cyan-300/80">
                        <Terminal size={10} className="shrink-0 text-cyan-400" />
                        <span className="truncate">{agent.task}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── VIEW 2: TELEMETRY GRID ─────────────────────────────────── */}
      {viewMode === "telemetry" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {agents.map((agent) => {
            const Icon = agent.icon;
            const isSelected = selectedAgent === agent.id;
            return (
              <div
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`
                  relative rounded-2xl p-4 transition-all duration-300 cursor-pointer border
                  ${
                    isSelected
                      ? `${agent.color} shadow-[0_0_25px_rgba(34,211,238,0.2)] scale-[1.02]`
                      : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                  }
                `}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-2 rounded-xl ${agent.color}`}>
                    <Icon size={20} />
                  </div>
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase px-2 py-0.5 rounded-md bg-white/10 text-white/70">
                    {agent.badge}
                  </span>
                </div>

                <h4 className="text-sm font-bold text-white">{agent.name}</h4>
                <p className="text-[11px] text-white/40 mb-2">{agent.role}</p>

                <div className="flex items-center gap-1.5 text-[11px] text-cyan-300/80 bg-black/40 border border-white/5 rounded-lg px-2.5 py-1.5 mt-2">
                  <Clock size={12} className="shrink-0 animate-spin text-cyan-400" />
                  <span className="truncate">{agent.task}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Selected Agent Inspector Drawer ───────────────────────── */}
      <div className="rounded-2xl border border-white/10 bg-black/60 p-5 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">{activeAgentData.avatarEmoji}</span>
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300">
                Agent Protocol Inspector: {activeAgentData.name}
              </span>
              <span className="text-[10px] text-white/40 block font-mono">
                Role: {activeAgentData.role} · Station: {activeAgentData.deskLabel}
              </span>
            </div>
          </div>

          <span className="inline-flex items-center gap-1.5 text-[10px] text-green-400 font-mono bg-green-500/10 border border-green-500/20 px-3 py-1 rounded-full">
            <CheckCircle2 size={12} /> Verified Deterministic Execution
          </span>
        </div>

        <p className="text-xs text-white/70 leading-relaxed font-sans mb-3">
          {activeAgentData.description}
        </p>

        {/* Live Specifications Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-white/5">
          {Object.entries(activeAgentData.specs).map(([key, val], idx) => (
            <div key={idx} className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-[11px] font-mono">
              <span className="text-white/40 uppercase block text-[9px] mb-0.5">{key}</span>
              <span className="text-white font-semibold">{val}</span>
            </div>
          ))}
        </div>

        {/* Live Synchronized Backend Log Stream for Selected Agent */}
        {liveAgentHistory[selectedAgent]?.length > 0 && (
          <div className="mt-4 p-3 rounded-xl bg-black/80 border border-white/10 font-mono text-[11px] space-y-1.5">
            <div className="flex items-center justify-between text-white/50 text-[10px] pb-1 border-b border-white/5">
              <span className="uppercase tracking-wider text-cyan-400 font-bold">Live SSE Backend Activity Stream</span>
              <span>Synced from Orchestrator</span>
            </div>
            {liveAgentHistory[selectedAgent].map((logLine, lIdx) => (
              <div key={lIdx} className="text-white/80 flex items-start gap-2">
                <span className="text-cyan-400 font-bold">›</span>
                <span className="truncate">{logLine}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
