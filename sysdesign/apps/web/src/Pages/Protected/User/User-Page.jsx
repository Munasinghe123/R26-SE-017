import React, { useState } from "react";
import beehiveBg from "../../../Images/beehive-bg.png";
import createProject from "../../../Images/create-project.png";
import { Rocket } from "lucide-react";
import CreateProject from "../../../components/Project-Dashboard/Modals/CreateProjectModal";

export default function UserPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  return (
    <div className="min-h-screen w-full flex items-center justify-center px-6 flex-col gap-8">
      <h1
        className="text-white text-7xl uppercase font-bold"
        style={{ fontFamily: "Orbitron, sans-serif" }}
      >
        Create <span className="text-cyan-300">Project</span>
      </h1>

      {/* CREATE PROJECT CARD */}
      <div className="relative w-full max-w-6xl h-[360px] overflow-hidden rounded-3xl border border-cyan-400/30 bg-gradient-to-br from-cyan-900/60 via-cyan-950/90 to-black shadow-[0_0_50px_rgba(34,211,238,0.25)]">
        <img
          src={beehiveBg}
          alt=""
          className="pointer-events-none absolute -left-24 -top-24 w-[330px] opacity-20"
        />

        <img
          src={beehiveBg}
          alt=""
          className="pointer-events-none absolute -bottom-28 -right-24 w-[350px] rotate-180 opacity-20"
        />

        <div className="relative z-10 grid h-full grid-cols-1 items-center px-8 md:grid-cols-2 md:px-14">
          {/* CONTENT */}
          <div className="flex h-full w-full flex-col items-start justify-center">
            <span className="text-2xl font-bold tracking-[0.2em] text-white md:text-3xl">
              START NEW PROJECT
            </span>

            <div className="mt-2 h-1 w-24 rounded-full bg-cyan-400" />

            <p className="mt-4 max-w-md text-sm leading-relaxed text-white/70 md:text-base">
              Initialize a project workspace, upload client audio recordings or
              raw specification documents, and generate complete software
              architecture models.
            </p>

            <div className="mt-6 flex items-center gap-4">
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-2 rounded-full border border-cyan-400/60 bg-cyan-600/80 px-6 py-3.5 text-xs font-bold uppercase tracking-wider text-white shadow-[0_0_20px_rgba(34,211,238,0.4)] transition duration-300 hover:bg-cyan-500 cursor-pointer"
              >
                <Rocket size={16} />
                Create Project
              </button>
            </div>
          </div>

          {/* IMAGE */}
          <div className="relative hidden h-full items-center justify-center overflow-hidden md:flex">
            <img
              src={createProject}
              alt="Create Project"
              className="w-[70%] max-w-none object-contain opacity-80"
            />
          </div>
        </div>
      </div>

      {/* CREATE PROJECT MODAL */}
      <CreateProject
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  );
}
