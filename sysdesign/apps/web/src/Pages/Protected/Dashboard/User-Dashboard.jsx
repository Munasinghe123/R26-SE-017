import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import beehiveBg from "../../../Images/beehive-bg.png";
import createProject from "../../../Images/create-project.png";
import {
  FolderGit2,
  Plus,
  Play,
  ArrowRight,
  FileCheck,
  Rocket,
  Upload,
  LayoutDashboard,
  Boxes,
  Clock
} from "lucide-react";

export default function UserDashboard() {
  const currentUser = useSelector((state) => state.user?.userInfo);
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  const lastMeetingId = localStorage.getItem("lastMeetingId");
  const lastMeetingTime = localStorage.getItem("lastMeetingTime");

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await axios.get("/projects", {
          params: { userId: currentUser?.id }
        });
        setProjects(res.data || []);
      } catch (err) {
        console.error("Failed to load projects:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [currentUser]);

  return (
    <div className="min-h-screen w-full text-white pt-24 pb-16 px-6 lg:px-20 flex flex-col items-center">
      {/* HEADER SECTION */}
      <div className="w-full max-w-6xl mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1
            className="text-4xl md:text-6xl font-extrabold uppercase tracking-wide text-white"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            System <span className="text-cyan-300">Dashboard</span>
          </h1>
          <p className="mt-2 text-gray-400 text-base md:text-lg">
            Multi-Agent Software Engineering Platform — Requirements, HLD, LLD, UI & SRS Assembly.
          </p>
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          <Link to="/upload-audio">
            <button className="flex items-center gap-2 px-5 py-3 bg-white/5 hover:bg-white/10 text-cyan-300 border border-cyan-400/40 rounded-full font-semibold text-xs uppercase tracking-wider transition duration-300 cursor-pointer">
              <Upload size={16} />
              Upload Audio / Doc
            </button>
          </Link>

          <Link to="/project-dashboard">
            <button className="flex items-center gap-2 px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs uppercase tracking-wider rounded-full shadow-[0_0_20px_rgba(34,211,238,0.3)] transition duration-300 cursor-pointer">
              <LayoutDashboard size={16} />
              Project Workspace
            </button>
          </Link>
        </div>
      </div>

      {/* RESUME ACTIVE REQUIREMENTS REVIEW BANNER */}
      {lastMeetingId && (
        <div className="w-full max-w-6xl mb-10 p-6 rounded-3xl bg-gradient-to-r from-cyan-950/70 via-[#0f172a] to-purple-950/60 border border-cyan-400/50 shadow-[0_0_35px_rgba(34,211,238,0.25)] backdrop-blur-xl flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="p-4 rounded-2xl bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">
              <FileCheck size={32} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-extrabold uppercase tracking-widest text-cyan-300 bg-cyan-500/20 px-3 py-1 rounded-full border border-cyan-400/40">
                  Active Requirements Elicitation
                </span>
                {lastMeetingTime && (
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock size={12} />
                    {new Date(lastMeetingTime).toLocaleString()}
                  </span>
                )}
              </div>
              <h3 className="text-xl font-bold text-white mt-1">
                Extracted Requirements Package (ID: <span className="font-mono text-cyan-300">{lastMeetingId.slice(0, 8)}</span>)
              </h3>
              <p className="text-gray-400 text-xs md:text-sm">
                Resume review of extracted IEEE 29148 specifications or confirm to launch the Multi-Agent Pipeline.
              </p>
            </div>
          </div>

          <Link to={`/requirements-review/${lastMeetingId}`}>
            <button className="flex items-center gap-2 px-7 py-3.5 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider rounded-full shadow-[0_0_25px_rgba(34,211,238,0.4)] transition duration-300 active:scale-95 cursor-pointer whitespace-nowrap">
              Resume Review
              <ArrowRight size={16} />
            </button>
          </Link>
        </div>
      )}

      {/* HERO FEATURE CARD */}
      <div className="relative w-full max-w-6xl h-[360px] overflow-hidden rounded-3xl border border-cyan-400/30 bg-gradient-to-br from-cyan-900/60 via-cyan-950/90 to-black shadow-[0_0_50px_rgba(34,211,238,0.25)] mb-12">
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

        <div className="relative h-full grid grid-cols-1 md:grid-cols-2 z-10 items-center justify-center px-8 md:px-14">
          <div className="flex flex-col items-start justify-center h-full w-full">
            <span className="text-2xl md:text-3xl font-bold tracking-[0.2em] text-white">
              START NEW PROJECT
            </span>
            <div className="mt-2 h-1 w-24 bg-cyan-400 rounded-full" />

            <p className="mt-4 max-w-md text-sm md:text-base leading-relaxed text-white/70">
              Initialize a project workspace, upload client audio recordings or raw specification documents, and generate complete software architecture models.
            </p>

            <div className="flex items-center gap-4 mt-6">
              <Link to="/create-project">
                <button className="flex items-center gap-2 px-6 py-3.5 text-xs font-bold uppercase tracking-wider text-white rounded-full border border-cyan-400/60 bg-cyan-600/80 hover:bg-cyan-500 shadow-[0_0_20px_rgba(34,211,238,0.4)] transition duration-300 cursor-pointer">
                  <Rocket size={16} />
                  Create Project
                </button>
              </Link>

              <Link to="/upload-audio">
                <button className="flex items-center gap-2 px-6 py-3.5 text-xs font-bold uppercase tracking-wider text-cyan-300 rounded-full border border-cyan-400/40 bg-black/60 hover:bg-black/90 transition duration-300 cursor-pointer">
                  <Upload size={16} />
                  Upload Audio / Doc
                </button>
              </Link>
            </div>
          </div>

          <div className="relative hidden md:flex flex-col h-full items-center justify-center overflow-hidden">
            <img
              src={createProject}
              alt="Create Project"
              className="w-[110%] max-w-none object-contain opacity-80"
            />
          </div>
        </div>
      </div>

      {/* PROJECTS & SDLC PIPELINE RUNS SECTION */}
      <div className="w-full max-w-6xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <FolderGit2 className="text-cyan-400" />
            Projects & Pipeline Runs ({projects.length})
          </h2>
          <Link to="/project-dashboard" className="text-xs font-semibold text-cyan-300 hover:text-cyan-200 flex items-center gap-1 uppercase tracking-wider">
            View All Projects
            <ArrowRight size={14} />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 rounded-2xl bg-white/5 border border-white/10 text-center text-gray-400">
            Loading project workspace...
          </div>
        ) : projects.length === 0 ? (
          <div className="p-10 rounded-3xl bg-white/5 border border-dashed border-white/10 text-center">
            <Boxes size={40} className="mx-auto text-cyan-400 mb-3 opacity-60" />
            <h3 className="text-lg font-bold text-white">No Projects Found</h3>
            <p className="text-gray-400 text-sm max-w-md mx-auto mt-1 mb-6">
              Create a new project or upload a meeting audio to start the automated multi-agent requirements & design pipeline.
            </p>
            <Link to="/create-project">
              <button className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs uppercase tracking-wider rounded-full shadow-md">
                + Create First Project
              </button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {projects.slice(0, 4).map((p) => (
              <div
                key={p.id}
                className="p-6 rounded-3xl bg-[#0f172a]/90 border border-white/10 hover:border-cyan-400/50 shadow-xl transition duration-300 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold text-white">
                      {p.name}
                    </h3>
                    <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-300 border border-cyan-400/20">
                      {p.is_job ? "Pipeline Run" : "Active Project"}
                    </span>
                  </div>
                  <p className="text-gray-400 text-xs line-clamp-2 mb-4">
                    {p.description || "IEEE 29148 Multi-Agent Pipeline Project"}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                  <span className="text-[11px] text-gray-500">
                    Created: {p.created_at ? new Date(p.created_at).toLocaleDateString() : "Recent"}
                  </span>

                  <button
                    onClick={() => {
                      if (p.is_job) {
                        navigate(`/pipeline/${p.id}`);
                      } else {
                        navigate("/select-mode", { state: { projectId: p.id } });
                      }
                    }}
                    className="flex items-center gap-1.5 px-4 py-2 bg-cyan-600/80 hover:bg-cyan-500 text-white text-xs font-semibold rounded-full transition cursor-pointer"
                  >
                    <Play size={12} />
                    {p.is_job ? "View Pipeline" : "Start Elicitation"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
