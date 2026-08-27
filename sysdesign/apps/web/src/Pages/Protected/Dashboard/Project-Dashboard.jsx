
import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { 
  FolderGit2, 
  Plus, 
  Calendar, 
  User, 
  Users, 
  Play, 
  ArrowRight,
  Boxes,
  FileCheck,
  TrendingUp,
  FolderOpen
} from "lucide-react";

export default function ProjectDashboard() {
  const currentUser = useSelector((state) => state.user.userInfo);
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!currentUser?.id) {
      setLoading(false);
      return;
    }

    const fetchProjects = async () => {
      try {
        const res = await axios.get("/projects", {
          params: { userId: currentUser.id }
        });
        setProjects(res.data || []);
      } catch (err) {
        console.error("Failed to load projects:", err);
        setError("Could not retrieve projects. Please make sure the backend is active.");
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [currentUser]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-white bg-transparent">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400 mb-4"></div>
        <p className="text-cyan-300 font-medium animate-pulse">Initializing project workspace...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full text-white pt-24 pb-12 px-6 lg:px-24">
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-12">
        <div>
          <h1 
            style={{ fontFamily: "Orbitron, sans-serif" }} 
            className="text-4xl md:text-5xl font-extrabold uppercase tracking-wide text-white"
          >
            Project <span className="text-cyan-300">Workspace</span>
          </h1>
          <p className="text-gray-400 mt-2 text-lg">
            Manage your SDLC lifecycle pipelines and launch requirements elicitation.
          </p>
        </div>

        <Link to="/create-project">
          <button className="flex items-center gap-2 px-6 py-3.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-full shadow-[0_0_20px_rgba(34,211,238,0.3)] transition duration-300 cursor-pointer">
            <Plus size={18} />
            New Project
          </button>
        </Link>
      </div>

      {/* STATS OVERVIEW CARD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center gap-5">
          <div className="p-4 rounded-xl bg-cyan-500/10 text-cyan-300">
            <FolderGit2 size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold">{projects.length}</div>
            <div className="text-sm text-gray-400">Total Projects</div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center gap-5">
          <div className="p-4 rounded-xl bg-purple-500/10 text-purple-300">
            <Boxes size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold">Active</div>
            <div className="text-sm text-gray-400">Multi-Agent Pipeline</div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center gap-5">
          <div className="p-4 rounded-xl bg-green-500/10 text-green-300">
            <FileCheck size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold">IEEE 29148</div>
            <div className="text-sm text-gray-400">Verified Schema Compliance</div>
          </div>
        </div>
      </div>

      {/* RECENT ELICITATION RESUME BANNER */}
      {localStorage.getItem("lastMeetingId") && (
        <div className="mb-10 p-6 rounded-3xl bg-gradient-to-r from-cyan-950/60 via-[#0f172a] to-purple-950/50 border border-cyan-400/40 shadow-[0_0_30px_rgba(34,211,238,0.2)] flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="p-4 rounded-2xl bg-cyan-500/20 text-cyan-300">
              <FileCheck size={28} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-2.5 py-0.5 rounded-full border border-cyan-400/30">
                  Active Requirements Elicitation
                </span>
                {localStorage.getItem("lastMeetingTime") && (
                  <span className="text-xs text-gray-400">
                    {new Date(localStorage.getItem("lastMeetingTime")).toLocaleString()}
                  </span>
                )}
              </div>
              <h3 className="text-xl font-bold text-white mt-1">
                Extracted Requirements Package (ID: <span className="font-mono text-cyan-300">{localStorage.getItem("lastMeetingId").slice(0, 8)}</span>)
              </h3>
              <p className="text-gray-400 text-sm">
                Resume review of extracted IEEE 29148 specifications or launch the Multi-Agent Pipeline.
              </p>
            </div>
          </div>

          <Link to={`/requirements-review/${localStorage.getItem("lastMeetingId")}`}>
            <button className="flex items-center gap-2 px-6 py-3.5 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider rounded-full shadow-lg transition duration-300 active:scale-95 cursor-pointer whitespace-nowrap">
              <ArrowRight size={16} />
              Resume Requirements Review
            </button>
          </Link>
        </div>
      )}

      {/* MAIN PROJECT GRID */}
      {projects.length === 0 ? (

        <div className="flex flex-col items-center justify-center p-16 rounded-3xl border border-dashed border-cyan-400/20 bg-white/5 backdrop-blur-sm text-center">
          <div className="p-5 rounded-full bg-cyan-950/40 text-cyan-300 mb-6">
            <FolderOpen size={48} />
          </div>
          <h3 className="text-2xl font-bold mb-2">No Projects Found</h3>
          <p className="text-gray-400 max-w-md mb-8">
            You don't have any projects in your workspace yet. Let's create your first project to start the requirements elicitation process.
          </p>
          <Link to="/create-project">
            <button className="flex items-center gap-2 px-8 py-4 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-full shadow-lg transition-transform active:scale-95 cursor-pointer">
              <Plus size={20} />
              Create Project
            </button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {projects.map((project) => (
            <div 
              key={project.id} 
              className="group relative flex flex-col justify-between p-8 rounded-3xl border border-white/10 bg-[#0f172a]/90 hover:border-cyan-400/50 shadow-xl transition-all duration-300 hover:shadow-[0_0_30px_rgba(34,211,238,0.15)] overflow-hidden"
            >
              {/* Card Accent Glow */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none group-hover:bg-cyan-500/20 transition-all duration-500"></div>

              <div>
                {/* Title */}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-2xl font-bold text-white group-hover:text-cyan-300 transition duration-300">
                    {project.name}
                  </h3>
                  <span className="px-3 py-1 text-xs font-semibold rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                    Analysis Ready
                  </span>
                </div>

                {/* Description */}
                <p className="text-gray-400 text-sm leading-relaxed mb-6 line-clamp-3">
                  {project.description || "No project description provided."}
                </p>

                {/* Meta Details */}
                <div className="space-y-3 mb-8 pt-4 border-t border-white/5">
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <User size={14} className="text-cyan-400" />
                    <span>Owner: <strong>{project.product_owner_name || "You"}</strong></span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <Users size={14} className="text-purple-400" />
                    <span>Client: <strong>{project.client_name || "N/A"}</strong></span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <Calendar size={14} className="text-gray-500" />
                    <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-white/5">
                <button 
                  onClick={() => navigate("/select-mode", { state: { projectId: project.id } })}
                  className="flex-1 flex items-center justify-center gap-2 px-5 py-3.5 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold rounded-2xl transition duration-300 cursor-pointer"
                >
                  <Play size={15} />
                  Start Elicitation
                </button>
                <button 
                  onClick={() => navigate("/upload-audio", { state: { projectId: project.id } })}
                  className="flex-1 flex items-center justify-center gap-2 px-5 py-3.5 bg-white/5 hover:bg-white/10 text-white text-sm font-semibold rounded-2xl border border-white/10 transition duration-300 cursor-pointer"
                >
                  Upload Documents
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}