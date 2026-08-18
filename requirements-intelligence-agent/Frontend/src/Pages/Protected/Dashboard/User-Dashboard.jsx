import beehiveBg from "../../../Images/beehive-bg.png";
import createProject from "../../../Images/create-project.png";
import {
  ClipboardList,
  FileText,
  Network,
  Code2,
  PanelsTopLeft,
  Rocket,
} from "lucide-react";
import { Link } from "react-router-dom";

export default function UserDashboard() {
  return (
    <div className=" min-h-screen w-full items-center justify-center px-10 flex flex-col">
      <h2
        className="mt-4 text-7xl font-bold text-white mb-10"
        style={{ fontFamily: "Orbitron, sans-serif" }}
      >
        Create <span className="text-cyan-300">Project </span>
      </h2>
      {/* Main card */}
      <div
        className="
          relative
          w-full
          max-w-5xl
          h-[390px]
          overflow-hidden
          rounded-3xl
          border border-cyan-400/20
          bg-gradient-to-br
          from-cyan-800/80
          via-cyan-950/80
          to-black
          shadow-[0_0_50px_rgba(34,211,238,0.25)]
        "
      >
        {/* Top-left beehive */}
        <img
          src={beehiveBg}
          alt=""
          className="
            pointer-events-none
            absolute
            -left-24
            -top-24
            w-[330px]
            opacity-20
          "
        />

        {/* Bottom-right beehive */}
        <img
          src={beehiveBg}
          alt=""
          className="
            pointer-events-none
            absolute
            -bottom-28
            -right-24
            w-[350px]
            rotate-180
            opacity-20
          "
        />

        {/* Main content */}
        <div className="relative h-full grid grid-cols-2 z-10 items-center justify-center px-14">
          {/* LEFT SIDE */}
          <div className="flex flex-col items-start justify-center h-full w-full p-4">
            <span className="text-4xl font-semibold tracking-[0.3em] text-white">
              NEW PROJECT
            </span>
            <div className="mt-1 h-0.5 w-28 bg-cyan-400" />

            <p className="mt-6 max-w-md text-base leading-relaxed text-white/70">
              Start a new requirements analysis and transform your ideas into
              complete software design artifacts.
            </p>

            <Link to="/create-project">
              <button
                className="flex mt-4 items-center gap-3 cursor-pointer
                    inset-0 bg-gradient-to-r from-cyan-400/0 via-cyan-400/30 to-purple-500/0
                    relative px-5 py-3.5 
                    text-sm font-medium uppercase tracking-[2px]
                    text-white rounded-full
                    border border-cyan-400/60
                    bg-black backdrop-blur-md
                    overflow-hidden
                    transition-all duration-300
                    hover:border-cyan-200
                    hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"
              >
                <Rocket size={17} />
                Create Project
              </button>
            </Link>
          </div>

          {/* RIGHT SIDE */}
          <div className="relative mr-8 flex flex-col h-full min-h-0 min-w-0 items-center justify-center overflow-hidden">
            <img
              src={createProject}
              alt="Create Project"
              className="w-[120%] h-[120%] max-w-none object-contain opacity-75 mt-16"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
