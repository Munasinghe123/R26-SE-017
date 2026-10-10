import React from "react";
import { Plus, FolderPlus } from "lucide-react";

export default function EmptyProjectState({ onCreateProject }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center max-w-lg mx-auto">
      <div className="p-5 rounded-3xl bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 mb-6 shadow-[0_0_30px_rgba(34,211,238,0.2)]">
        <FolderPlus size={44} />
      </div>
      <h2
        style={{ fontFamily: "Orbitron, sans-serif" }}
        className="text-3xl font-bold uppercase text-white mb-3"
      >
        No Projects <span className="text-cyan-300">Yet</span>
      </h2>
      <p className="text-gray-400 text-sm leading-relaxed mb-8">
        Create your first project workspace to start automated requirements elicitation, multi-agent software architecture modeling, and design artifacts.
      </p>
      <button
        type="button"
        onClick={onCreateProject}
        className="flex items-center gap-2 rounded-full border border-cyan-400/60 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 px-7 py-3.5 text-xs font-bold uppercase tracking-wider text-white shadow-[0_0_20px_rgba(34,211,238,0.4)] transition duration-300 cursor-pointer"
      >
        <Plus size={16} />
        Create Project
      </button>
    </div>
  );
}
