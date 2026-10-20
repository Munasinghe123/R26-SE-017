import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Cpu,
  Calculator,
  Compass,
  CheckCircle2,
  Terminal,
  ArrowRight,
  Sparkles,
} from "lucide-react";

/**
 * Strips timestamps, emojis, and raw log prefixes to display pure, human-readable agent status.
 */
function sanitizeLogMessage(raw) {
  if (!raw || typeof raw !== "string") return "";
  let text = raw.trim();
  // Strip timestamps like "4:55:26 PM — ", "27:18 PM - ", "12:45:21 [INFO] "
  text = text.replace(/^\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\s*[-—–]\s*/i, "");
  text = text.replace(/^\d{1,2}:\d{2}:\d{2}\s*\[[A-Z]+\]\s*/i, "");
  // Strip leading icons / emojis
  text = text.replace(/^[🚀⚙️📊🎨✅⚠✗🛡️💡👨‍✈️🧠🧮]+\s*/, "");
  // Strip stage tags like "[HLD] ", "[REQUIREMENTS] → "
  text = text.replace(/^\[(HLD|REQUIREMENTS|LLD|UI|SRS)\]\s*[-—–→:]*\s*/i, "");
  text = text.replace(/^HLA-Agent:\s*/i, "");
  return text.trim();
}

export default function AgentTaskvilleWorkspace({ logs = [], currentStage = "hld", className = "" }) {
  const [selectedAgent, setSelectedAgent] = useState("architect");
  const [activeSpeechIdx, setActiveSpeechIdx] = useState(0);

  // Real-time backend log binding
  const [liveAgentThoughts, setLiveAgentThoughts] = useState({});
  const [liveAgentHistory, setLiveAgentHistory] = useState({
    supervisor: [],
    security: [],
    architect: [],
    critic: [],
  });
  const [activeAgentId, setActiveAgentId] = useState("architect");

  useEffect(() => {
    if (!logs || logs.length === 0) return;
    const latest = logs[logs.length - 1];
    if (typeof latest !== "string") return;
    const lower = latest.toLowerCase();
    const cleanMsg = sanitizeLogMessage(latest);

    if (
      lower.includes("openrouter") ||
      lower.includes("candidate") ||
      lower.includes("synthesiz") ||
      lower.includes("llama") ||
      lower.includes("qwen") ||
      lower.includes("deepseek") ||
      lower.includes("model") ||
      lower.includes("plantuml") ||
      lower.includes("diagram")
    ) {
      setLiveAgentThoughts(prev => ({ ...prev, architect: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, architect: [...(prev.architect || []).slice(-3), cleanMsg || latest] }));
      setActiveAgentId("architect");
    } else if (
      lower.includes("security") ||
      lower.includes("stride") ||
      lower.includes("trust") ||
      lower.includes("boundary") ||
      lower.includes("vault") ||
      lower.includes("tls") ||
      lower.includes("auth") ||
      lower.includes("mitigat")
    ) {
      setLiveAgentThoughts(prev => ({ ...prev, security: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, security: [...(prev.security || []).slice(-3), cleanMsg || latest] }));
      setActiveAgentId("security");
    } else if (
      lower.includes("evaluat") ||
      lower.includes("sentence") ||
      lower.includes("cas") ||
      lower.includes("rts") ||
      lower.includes("qac") ||
      lower.includes("ci") ||
      lower.includes("cos") ||
      lower.includes("ssm") ||
      lower.includes("metric") ||
      lower.includes("score") ||
      lower.includes("ahp")
    ) {
      setLiveAgentThoughts(prev => ({ ...prev, critic: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, critic: [...(prev.critic || []).slice(-3), cleanMsg || latest] }));
      setActiveAgentId("critic");
    } else if (
      lower.includes("dispatch") ||
      lower.includes("style") ||
      lower.includes("winner") ||
      lower.includes("stage") ||
      lower.includes("complete") ||
      lower.includes("job") ||
      lower.includes("gate") ||
      lower.includes("review")
    ) {
      setLiveAgentThoughts(prev => ({ ...prev, supervisor: cleanMsg || latest }));
      setLiveAgentHistory(prev => ({ ...prev, supervisor: [...(prev.supervisor || []).slice(-3), cleanMsg || latest] }));
      setActiveAgentId("supervisor");
    }
  }, [logs]);

  const agents = [
    {
      id: "supervisor",
      name: "Supervisor Router",
      role: "Pipeline & AHP Coordinator",
      icon: Compass,
      avatarEmoji: "👨‍✈️",
      accentHex: "#22d3ee",
      stepNumber: "01",
      status: "active",
      task: "Phase gate management & AHP consistency (CR < 0.10)",
      badge: "Orchestrator",
      thoughts: [
        "Coordinating multi-model execution and enforcing AHP pairwise weights (CR < 0.10)...",
        "Dispatched requirements package to Principal Architect synthesis cluster.",
        "Awaiting architecture candidates and candidate rankings...",
        "Phase quality gates verified. Ready for downstream handover."
      ],
      description: "Controls the pipeline state machine, enforces AHP eigenvector consistency limits (CR < 0.10), and routes candidate payloads between generation, security audit, and mathematical evaluation.",
      specs: {
        runtime: "Asyncio State Coordinator",
        verification: "AHP Consistency Ratio (CR < 0.10)",
        role: "Deterministic Router"
      }
    },
    {
      id: "architect",
      name: "Principal Architect",
      role: "Multi-Model Synthesis Mesh",
      icon: Cpu,
      avatarEmoji: "🧠",
      accentHex: "#a78bfa",
      stepNumber: "02",
      status: "active",
      task: "Concurrent synthesis across LLaMA 3.3 70B, Qwen Coder 32B & DeepSeek V3",
      badge: "3-Model Ensemble",
      thoughts: [
        "Prompting meta-llama/llama-3.3-70b-instruct for high-capacity open foundation baseline...",
        "Synthesizing qwen/qwen-2.5-coder-32b-instruct for precise code/boundary contracts...",
        "Synthesizing deepseek/deepseek-chat-v3-0324 for decoupled multi-layer reasoning...",
        "Architecture packages generated and transmitted for S-SDLC security audit."
      ],
      description: "Executes 3 independent LLMs concurrently through the OpenRouter gateway. Produces structured Component Architecture Models (CAM) covering components, boundaries, and connectors.",
      specs: {
        models: "LLaMA 3.3 70B · Qwen Coder 32B · DeepSeek V3",
        topology: "C4 Container / Microservices / Layered",
        mode: "Parallel Non-Blocking Synthesis"
      }
    },
    {
      id: "security",
      name: "Security Specialist",
      role: "S-SDLC & STRIDE Modeler",
      icon: ShieldAlert,
      avatarEmoji: "🛡️",
      accentHex: "#f87171",
      stepNumber: "03",
      status: "active",
      task: "Trust boundary mapping & STRIDE mitigation verification",
      badge: "Security Audit",
      thoughts: [
        "Partitioning components into Public DMZ, Core VPC, and Secure Vault...",
        "Auditing STRIDE threat dimensions: Spoofing, Tampering, Elevation of Privilege...",
        "Verifying mTLS 1.3 encryption, token buckets, and RBAC policies...",
        "Mitigation Verification Score (MVS) computed and verified."
      ],
      description: "Applies automated S-SDLC threat modeling. Partitions components across 3 distinct trust zones, builds the 6-dimension STRIDE threat matrix, and computes the Attack Surface Index (ASI).",
      specs: {
        standard: "NIST SP 800-207 / STRIDE",
        zones: "Public DMZ · Core VPC · Data Vault",
        scoring: "Attack Surface Index (ASI) & MVS"
      }
    },
    {
      id: "critic",
      name: "ATAM Critic",
      role: "Deterministic Quality Engine",
      icon: Calculator,
      avatarEmoji: "🧮",
      accentHex: "#fbbf24",
      stepNumber: "04",
      status: "active",
      task: "SentenceTransformers semantic alignment & NetworkX graph metrics",
      badge: "Math Lab (Zero-LLM)",
      thoughts: [
        "Encoding requirements using offline sentence-transformers/all-MiniLM-L6-v2...",
        "Calculating graph density (Coupling Index CI) and Cohesion of Services (CoS)...",
        "Evaluating style metrics (LIS/DDS for Layered, SBA/ISS for Microservices)...",
        "Computing final Composite Architecture Score (CAS) using AHP eigenvector math."
      ],
      description: "100% deterministic Python evaluation. Measures requirement traceability (RTS), quality coverage (QAC), coupling, cohesion, and computes the Composite Architecture Score (CAS) without LLM bias.",
      specs: {
        embeddings: "all-MiniLM-L6-v2 (Offline)",
        math: "NetworkX Graph Density + Saaty AHP",
        verdict: "Mathematical CAS Ranking"
      }
    },
  ];

  // Rotate thought cycle for active agent
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveSpeechIdx((prev) => (prev + 1) % 4);
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  const activeAgentData = agents.find((a) => a.id === selectedAgent) || agents[1];

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-white/10 bg-[#070b13]/90 backdrop-blur-xl p-5 shadow-2xl ${className}`}
    >
      {/* ── Council Header ────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            <h3
              className="text-base font-bold text-white tracking-wide"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              Collaborative <span className="text-cyan-300">Architecture Council</span>
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300">
              HLD Autonomous Mesh
            </span>
          </div>
          <p className="text-xs text-white/50 mt-1">
            Real-time collaboration across 4 specialized roles: Orchestration · LLM Synthesis · S-SDLC Audit · ATAM Evaluation
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-500/30 px-3 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            <span>4 Specialized Roles Active</span>
          </div>
        </div>
      </div>

      {/* ── Collaborative Data Flow Track ─────────────────────────────── */}
      <div className="relative mb-4 hidden md:flex items-center justify-between px-6 py-2 rounded-xl bg-black/40 border border-white/5 text-[10px] font-mono text-white/40">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
          <span className="text-white/80">01. Pipeline Gate</span>
        </div>
        <ArrowRight size={12} className="text-white/20" />
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
          <span className="text-white/80">02. 3-Model Synthesis</span>
        </div>
        <ArrowRight size={12} className="text-white/20" />
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
          <span className="text-white/80">03. S-SDLC STRIDE Audit</span>
        </div>
        <ArrowRight size={12} className="text-white/20" />
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          <span className="text-white/80">04. Mathematical CAS Scoring</span>
        </div>
      </div>

      {/* ── 4 Agent Workstations Grid ─────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-5">
        {agents.map((agent) => {
          const isSelected = selectedAgent === agent.id;
          const isCurrentlyActive = activeAgentId === agent.id;
          
          // Honest status computation: only show active thoughts if the stage has actually reached or run
          const stepOrder = ["supervisor", "architect", "security", "critic"];
          const currentStepIdx = stepOrder.indexOf(activeAgentId);
          const thisStepIdx = stepOrder.indexOf(agent.id);

          let currentThought = "";
          if (liveAgentThoughts[agent.id]) {
            currentThought = liveAgentThoughts[agent.id];
          } else if (thisStepIdx < currentStepIdx) {
            currentThought = "Verified & Completed";
          } else if (thisStepIdx === currentStepIdx) {
            currentThought = agent.thoughts[activeSpeechIdx % agent.thoughts.length];
          } else {
            currentThought = "Standing by — awaiting previous pipeline stage";
          }

          return (
            <div
              key={agent.id}
              onClick={() => setSelectedAgent(agent.id)}
              className={`
                relative rounded-xl p-3.5 transition-all duration-200 cursor-pointer flex flex-col justify-between border
                ${
                  isSelected
                    ? "border-cyan-400/80 bg-cyan-950/30 shadow-[0_0_20px_rgba(34,211,238,0.15)] ring-1 ring-cyan-400/50"
                    : "border-white/10 bg-black/40 hover:border-white/25 hover:bg-black/60"
                }
              `}
            >
              {/* Agent Live Speech Bubble */}
              <div className="relative mb-3 min-h-[64px]">
                <div
                  className="rounded-lg p-2.5 text-[11px] font-mono leading-relaxed border relative transition-all"
                  style={{
                    backgroundColor: "#0b121e",
                    borderColor: isSelected ? `${agent.accentHex}80` : "rgba(255,255,255,0.1)",
                    color: isSelected ? "#f8fafc" : "#94a3b8",
                  }}
                >
                  <div className="flex items-center justify-between font-semibold mb-1 text-[10px]" style={{ color: agent.accentHex }}>
                    <div className="flex items-center gap-1.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${isCurrentlyActive ? "animate-ping" : ""}`} style={{ backgroundColor: agent.accentHex }} />
                      <span>{agent.name}</span>
                    </div>
                    <span className="text-[9px] opacity-60 font-mono">Step {agent.stepNumber}</span>
                  </div>
                  <p className="line-clamp-2 text-[10.5px]">"{currentThought}"</p>

                  {/* Bubble Pointer */}
                  <div
                    className="absolute -bottom-1 left-5 w-2 h-2 rotate-45 border-r border-b"
                    style={{
                      backgroundColor: "#0b121e",
                      borderColor: isSelected ? `${agent.accentHex}80` : "rgba(255,255,255,0.1)",
                    }}
                  />
                </div>
              </div>

              {/* Agent Identity & Current Task */}
              <div className="flex items-center gap-3 pt-2.5 border-t border-white/5">
                <div
                  className="relative w-11 h-11 rounded-xl flex items-center justify-center text-xl border shrink-0"
                  style={{
                    background: `linear-gradient(135deg, ${agent.accentHex}15, #000000)`,
                    borderColor: `${agent.accentHex}40`,
                  }}
                >
                  <span className="select-none">{agent.avatarEmoji}</span>
                  {isCurrentlyActive && (
                    <span
                      className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border border-black animate-pulse"
                      style={{ backgroundColor: agent.accentHex }}
                    />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-white truncate">{agent.name}</h4>
                  </div>
                  <p className="text-[10px] text-white/40 truncate">{agent.role}</p>
                  <div className="flex items-center gap-1.5 mt-1 text-[9.5px] font-mono text-cyan-300/80">
                    <Terminal size={10} className="shrink-0 text-cyan-400" />
                    <span className="truncate">{agent.task}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Selected Agent Technical Specification Drawer ───────────── */}
      <div className="rounded-xl border border-white/10 bg-black/40 p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">{activeAgentData.avatarEmoji}</span>
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300">
                Council Member: {activeAgentData.name}
              </span>
              <span className="text-[10px] text-white/40 block font-mono">
                Role: {activeAgentData.role} · Execution: {activeAgentData.badge}
              </span>
            </div>
          </div>

          <span className="inline-flex items-center gap-1.5 text-[10px] text-green-400 font-mono bg-green-500/10 border border-green-500/20 px-2.5 py-0.5 rounded-full">
            <CheckCircle2 size={12} /> Deterministic Pipeline Component
          </span>
        </div>

        <p className="text-xs text-white/70 leading-relaxed font-sans mb-3">
          {activeAgentData.description}
        </p>

        {/* Live Specifications Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2 border-t border-white/5">
          {Object.entries(activeAgentData.specs).map(([key, val], idx) => (
            <div key={idx} className="p-2.5 rounded-lg bg-white/[0.03] border border-white/5 text-[11px] font-mono">
              <span className="text-white/40 uppercase block text-[9px] mb-0.5">{key}</span>
              <span className="text-white font-medium">{val}</span>
            </div>
          ))}
        </div>

        {/* Live Synchronized Backend Log Stream for Selected Agent */}
        {liveAgentHistory[selectedAgent]?.length > 0 && (
          <div className="mt-3 p-2.5 rounded-lg bg-black/70 border border-white/10 font-mono text-[10.5px] space-y-1">
            <div className="flex items-center justify-between text-white/40 text-[9.5px] pb-1 border-b border-white/5">
              <span className="uppercase tracking-wider text-cyan-400 font-bold">Recent SSE Backend Activity</span>
              <span>Synced with Orchestrator</span>
            </div>
            {liveAgentHistory[selectedAgent].map((logLine, lIdx) => (
              <div key={lIdx} className="text-white/80 flex items-start gap-1.5">
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
