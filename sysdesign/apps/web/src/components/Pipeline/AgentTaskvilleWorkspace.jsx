import React, { useState } from "react";
import { ShieldAlert, Cpu, Calculator, Compass, Sparkles, CheckCircle2, Clock } from "lucide-react";

export default function AgentTaskvilleWorkspace({ currentStage = "hld", className = "" }) {
  const [selectedAgent, setSelectedAgent] = useState("architect");

  const agents = [
    {
      id: "supervisor",
      name: "Supervisor Router",
      role: "System Orchestrator",
      icon: Compass,
      status: "active",
      task: "Evaluating candidate convergence & state transitions",
      badge: "State Controller",
      color: "border-cyan-400 text-cyan-300 bg-cyan-500/10",
      description: "Monitors the global pipeline state, validates AHP consistency ratios (CR < 0.10), and routes tasks between generation, evaluation, and downstream compilation.",
    },
    {
      id: "security",
      name: "Security Specialist",
      role: "STRIDE Threat Modeler",
      icon: ShieldAlert,
      status: "active",
      task: "Auditing trust boundaries & unauthenticated connectors",
      badge: "S-SDLC Lead",
      color: "border-red-400 text-red-300 bg-red-500/10",
      description: "Extracts threat baseline profiles, validates TLS 1.3 / mTLS boundaries across ingress tiers, and computes the Attack Surface Index (ASI) and Mitigation Verification Score (MVS).",
    },
    {
      id: "architect",
      name: "Principal Architect",
      role: "Multi-LLM Synthesis Mesh",
      icon: Cpu,
      status: "active",
      task: "Synthesizing 3 candidate styles (GPT-4o-mini, DeepSeek, Qwen)",
      badge: "Model Ensemble",
      color: "border-violet-400 text-violet-300 bg-violet-500/10",
      description: "Executes 3 independent models via OpenRouter (OpenAI, DeepSeek V3, Qwen 2.5) to synthesize bounded contexts, C4 container topologies, and interaction flows.",
    },
    {
      id: "critic",
      name: "ATAM Critic",
      role: "Deterministic Engine",
      icon: Calculator,
      status: "active",
      task: "Executing graph density, cohesion & AHP eigenvector math",
      badge: "Pure Code / Zero-LLM",
      color: "border-amber-400 text-amber-300 bg-amber-500/10",
      description: "Runs deterministic Python evaluation code (NetworkX graph algorithms, frozen sentence embeddings, and Saaty's 1980 AHP matrix). No LLM-as-a-judge bias.",
    },
  ];

  return (
    <div
      className={`relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#07131b]/90 via-black/80 to-[#0c0a1a]/90 backdrop-blur-xl p-6 shadow-[0_0_40px_rgba(34,211,238,0.1)] ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 animate-ping" />
            <h3
              className="text-lg font-bold text-white tracking-wide"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              Collaborative <span className="text-cyan-300">Agent Mesh</span>
            </h3>
          </div>
          <p className="text-xs text-white/50 mt-0.5">
            Interactive multi-agent workspace (Supervisor · Security · Architect · ATAM Critic)
          </p>
        </div>

        <div className="flex items-center gap-2 text-[11px] font-mono text-cyan-400/80 bg-cyan-500/10 border border-cyan-400/20 px-3 py-1 rounded-full">
          <Sparkles size={13} />
          <span>4 Autonomous Workers Online</span>
        </div>
      </div>

      {/* Agents Grid (Taskville Style Stations) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
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

      {/* Selected Agent Inspector Drawer */}
      {selectedAgent && (
        <div className="rounded-2xl border border-white/10 bg-black/40 p-4 transition-all">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300">
              Agent Protocol Inspector: {agents.find((a) => a.id === selectedAgent)?.name}
            </span>
            <span className="inline-flex items-center gap-1 text-[10px] text-green-400 font-mono">
              <CheckCircle2 size={12} /> Verified Deterministic
            </span>
          </div>
          <p className="text-xs text-white/70 leading-relaxed font-sans">
            {agents.find((a) => a.id === selectedAgent)?.description}
          </p>
        </div>
      )}
    </div>
  );
}
