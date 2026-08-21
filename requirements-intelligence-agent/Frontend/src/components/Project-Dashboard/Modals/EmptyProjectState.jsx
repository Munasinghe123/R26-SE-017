import React from "react";
import { Link } from "react-router-dom";
import { Rocket } from "lucide-react";

export default function EmptyProjectState({ onCreateProject }) {
  return (
    <div className="flex w-full max-w-2xl flex-col items-center justify-center px-8 text-center">
      <h1
        className="text-4xl font-bold uppercase tracking-wide text-white"
        style={{ fontFamily: "Orbitron, sans-serif" }}
      >
        Welcome to <span className="text-cyan-300">Sysdesign</span>
      </h1>

      <p className="mt-5 max-w-lg text-base leading-relaxed text-white/60">
        Your workspace for intelligent requirements engineering.
      </p>

      <div
        className="
          mt-10
          w-full
          max-w-md
          rounded-2xl
          border border-cyan-400/20
          bg-gradient-to-br
          from-cyan-900/40
          via-cyan-950/30
          to-black
          p-8
          shadow-[0_0_40px_rgba(34,211,238,0.08)]
        "
      >
        <h2
          className="text-xl font-semibold uppercase tracking-wide text-white"
          style={{ fontFamily: "Orbitron, sans-serif" }}
        >
          Start a Project
        </h2>

        <p className="mt-2 text-sm leading-relaxed text-white/60">
          Create a project and begin transforming your client's ideas into
          structured software requirements.
        </p>

        <button
          type="button"
          onClick={onCreateProject}
          className="
              flex mt-4  mx-auto items-center gap-3 cursor-pointer
                    inset-0 bg-gradient-to-r from-cyan-400/0 via-cyan-400/30 to-purple-500/0
                    relative px-5 py-3.5 
                    text-sm font-medium uppercase tracking-[2px]
                    text-white rounded-full
                    border border-cyan-400/60
                    bg-black backdrop-blur-md
                    overflow-hidden
                    transition-all duration-300
                    hover:border-cyan-200 w-fit
                    hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]
            "
        >
          <Rocket size={17} />
          Create Project
        </button>

        <div className="mx-auto mt-8 h-px w-32 bg-white/20" />

        <div>
          <h2
            className="text-lg mt-4 font-semibold uppercase tracking-wide text-white"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Waiting for a project?
          </h2>
          <p className=" text-sm leading-relaxed text-white/50 mt-2">
            A Product Owner can add you to a project at any time
          </p>
        </div>
      </div>
    </div>
  );
}
