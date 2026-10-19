import React, { useState, useMemo } from "react";
import {
  Globe,
  Cpu,
  Lock,
  Database,
  Layers,
  Search,
  Filter,
  CheckCircle2,
  Terminal,
  Server
} from "lucide-react";

/**
 * Classify any component into its architectural Separation of Concern tier.
 */
function classifyComponentTier(comp) {
  const name = (comp.name || "").toLowerCase();
  const layer = (comp.layer || comp.boundary || "").toLowerCase();

  // 1. Security & Identity
  if (
    layer.includes("security") ||
    layer.includes("auth") ||
    name.includes("auth") ||
    name.includes("security") ||
    name.includes("token") ||
    name.includes("vault") ||
    name.includes("iam")
  ) {
    return {
      id: "security",
      label: "Security & Identity",
      icon: Lock,
      color: "border-red-400/40 text-red-300 bg-red-500/10",
      accent: "#f87171"
    };
  }

  // 2. Ingress & Edge
  if (
    layer.includes("presentation") ||
    layer.includes("ingress") ||
    layer.includes("edge") ||
    name.includes("gateway") ||
    name.includes("ingress") ||
    name.includes("proxy") ||
    name.includes("controller") ||
    name.includes("router") ||
    name.includes("client")
  ) {
    return {
      id: "ingress",
      label: "Edge & Ingress",
      icon: Globe,
      color: "border-cyan-400/40 text-cyan-300 bg-cyan-500/10",
      accent: "#22d3ee"
    };
  }

  // 3. Persistence & Infrastructure
  if (
    layer.includes("data_access") ||
    layer.includes("persistence") ||
    layer.includes("infrastructure") ||
    name.includes("repository") ||
    name.includes("database") ||
    name.includes("db") ||
    name.includes("cache") ||
    name.includes("redis") ||
    name.includes("store") ||
    name.includes("bus") ||
    name.includes("broker") ||
    name.includes("queue")
  ) {
    return {
      id: "persistence",
      label: "Data & Event Store",
      icon: Database,
      color: "border-amber-400/40 text-amber-300 bg-amber-500/10",
      accent: "#fbbf24"
    };
  }

  // 4. Core Business Services (Default)
  return {
    id: "services",
    label: "Core Business Services",
    icon: Cpu,
    color: "border-violet-400/40 text-violet-300 bg-violet-500/10",
    accent: "#a78bfa"
  };
}

export default function SegmentedComponentsView({ components = [] }) {
  const [selectedTier, setSelectedTier] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const classifiedComponents = useMemo(() => {
    return components.map(c => ({
      ...c,
      tier: classifyComponentTier(c)
    }));
  }, [components]);

  const counts = useMemo(() => {
    const c = { all: classifiedComponents.length, ingress: 0, services: 0, security: 0, persistence: 0 };
    classifiedComponents.forEach(item => {
      if (c[item.tier.id] !== undefined) c[item.tier.id]++;
    });
    return c;
  }, [classifiedComponents]);

  const filteredComponents = useMemo(() => {
    return classifiedComponents.filter(c => {
      const matchesTier = selectedTier === "all" || c.tier.id === selectedTier;
      const matchesSearch =
        searchQuery === "" ||
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.layer || "").toLowerCase().includes(searchQuery.toLowerCase());
      return matchesTier && matchesSearch;
    });
  }, [classifiedComponents, selectedTier, searchQuery]);

  const tiers = [
    { id: "all", label: "All Tiers", count: counts.all, icon: Layers },
    { id: "ingress", label: "Edge Ingress", count: counts.ingress, icon: Globe },
    { id: "services", label: "Core Services", count: counts.services, icon: Cpu },
    { id: "security", label: "Security & Identity", count: counts.security, icon: Lock },
    { id: "persistence", label: "Persistence & Cache", count: counts.persistence, icon: Database },
  ];

  return (
    <div className="rounded-2xl border border-white/10 bg-[#070b13]/90 backdrop-blur-xl p-5 space-y-4">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Server size={16} className="text-violet-400" />
            <h3 className="text-sm font-bold tracking-widest text-white uppercase" style={{ fontFamily: "Orbitron, sans-serif" }}>
              Architecture Topology & Bounded Contexts
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-400/30 text-violet-300">
              {components.length} Total Components
            </span>
          </div>
          <p className="text-xs text-white/50 mt-0.5">
            Segmented by architectural tier and separation of concerns
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-56">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
          <input
            type="text"
            placeholder="Search component..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder-white/30 focus:outline-none focus:border-cyan-400/60 font-mono"
          />
        </div>
      </div>

      {/* Tier Filter Pills */}
      <div className="flex flex-wrap gap-2">
        {tiers.map((t) => {
          const Icon = t.icon;
          const active = selectedTier === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setSelectedTier(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono transition-all cursor-pointer ${
                active
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/60 shadow-[0_0_12px_rgba(34,211,238,0.2)] font-semibold"
                  : "bg-white/5 text-white/60 hover:text-white border border-white/10 hover:bg-white/10"
              }`}
            >
              <Icon size={12} />
              <span>{t.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${active ? "bg-cyan-400 text-black font-bold" : "bg-white/10 text-white/60"}`}>
                {t.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Components Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto pr-1">
        {filteredComponents.length > 0 ? (
          filteredComponents.map((c, i) => {
            const TierIcon = c.tier.icon;
            const respList = Array.isArray(c.responsibilities)
              ? c.responsibilities
              : typeof c.responsibilities === "string"
              ? [c.responsibilities]
              : [];

            return (
              <div
                key={i}
                className="p-3.5 rounded-xl border border-white/10 bg-black/40 hover:border-white/25 hover:bg-black/60 transition-all space-y-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <div className={`p-1.5 rounded-lg ${c.tier.color}`}>
                        <TierIcon size={13} />
                      </div>
                      <span className="text-xs font-bold text-white tracking-wide font-mono">
                        {c.name}
                      </span>
                    </div>

                    <span className="text-[9.5px] px-2 py-0.5 rounded-full font-mono uppercase bg-white/5 border border-white/10 text-white/60 shrink-0">
                      {c.element_type || c.layer || "Service"}
                    </span>
                  </div>

                  <div className="mt-2 text-[10px] font-mono text-cyan-400/80 flex items-center gap-1">
                    <span className="text-white/40">Tier:</span> {c.tier.label}
                  </div>
                </div>

                {respList.length > 0 && (
                  <div className="pt-2 border-t border-white/5 space-y-1">
                    <span className="text-[9px] uppercase font-mono text-white/40 block">Responsibilities:</span>
                    <ul className="text-[11px] text-white/65 space-y-0.5 list-disc list-inside">
                      {respList.slice(0, 3).map((r, rIdx) => (
                        <li key={rIdx} className="truncate">{r}</li>
                      ))}
                      {respList.length > 3 && (
                        <li className="text-[10px] text-cyan-400/70 list-none pl-3 font-mono">
                          +{respList.length - 3} more duties
                        </li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="col-span-full py-8 text-center text-white/40 text-xs font-mono">
            No components found matching this tier filter.
          </div>
        )}
      </div>

    </div>
  );
}
