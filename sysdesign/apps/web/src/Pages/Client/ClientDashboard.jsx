import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import {
  ShieldCheck,
  FileText,
  ArrowRight,
  User,
  Users,
  Calendar,
  Layers,
  Sparkles,
  Search,
  ExternalLink,
  CheckCircle2,
  FolderOpen,
  ClipboardList
} from "lucide-react";
import toast from "react-hot-toast";

export default function ClientDashboard() {
  const currentUser = useSelector((state) => state.user?.userInfo);
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [meetingSearchId, setMeetingSearchId] = useState("");

  const lastMeetingId = localStorage.getItem("lastMeetingId");
  const lastMeetingTime = localStorage.getItem("lastMeetingTime");

  useEffect(() => {
    const fetchClientProjects = async () => {
      try {
        const res = await axios.get("/projects", {
          params: { userId: currentUser?.id }
        });
        setProjects(res.data || []);
      } catch (err) {
        console.error("Failed to load client projects:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchClientProjects();
  }, [currentUser]);

  const handleDirectLookup = (e) => {
    e.preventDefault();
    const cleanId = meetingSearchId.trim();
    if (!cleanId) {
      toast.error("Please enter a valid Meeting ID or review token");
      return;
    }
    navigate(`/client/requirements/${cleanId}`);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-white bg-transparent">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400 mb-4"></div>
        <p className="text-cyan-300 font-medium animate-pulse">Loading Client Requirements Portal...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full text-white pt-24 pb-16 px-6 lg:px-24">
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-12">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3">
            <ShieldCheck size={14} />
            Client Review & Elicitation Portal
          </div>
          <h1
            style={{ fontFamily: "Orbitron, sans-serif" }}
            className="text-4xl md:text-5xl font-extrabold uppercase tracking-wide text-white"
          >
            Client <span className="text-cyan-300">Dashboard</span>
          </h1>
          <p className="text-gray-400 mt-2 text-lg">
            Review, refine, and approve extracted IEEE 29148 requirements specifications for your software systems.
          </p>
        </div>

        {/* QUICK LOOKUP FORM */}
        <form onSubmit={handleDirectLookup} className="flex items-center gap-2 bg-[#0f172a]/90 p-2 rounded-2xl border border-cyan-500/30 shadow-lg">
          <input
            type="text"
            placeholder="Paste Meeting ID to review..."
            value={meetingSearchId}
            onChange={(e) => setMeetingSearchId(e.target.value)}
            className="bg-transparent text-sm text-white px-4 py-2 focus:outline-none placeholder-gray-500 w-56 md:w-64"
          />
          <button
            type="submit"
            className="flex items-center gap-1.5 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-xl transition cursor-pointer"
          >
            <Search size={14} />
            Open
          </button>
        </form>
      </div>

      {/* STATS OVERVIEW CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center gap-5">
          <div className="p-4 rounded-xl bg-cyan-500/10 text-cyan-300">
            <ClipboardList size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold">{projects.length}</div>
            <div className="text-sm text-gray-400">Assigned Projects</div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center gap-5">
          <div className="p-4 rounded-xl bg-purple-500/10 text-purple-300">
            <ShieldCheck size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold">Client Authority</div>
            <div className="text-sm text-gray-400">Human-In-The-Loop Approval</div>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center gap-5">
          <div className="p-4 rounded-xl bg-emerald-500/10 text-emerald-300">
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold">Interactive</div>
            <div className="text-sm text-gray-400">Live AI Requirement Refinement</div>
          </div>
        </div>
      </div>

      {/* ACTIVE REQUIREMENTS ELICITATION BANNER */}
      {lastMeetingId && (
        <div className="mb-10 p-6 rounded-3xl bg-gradient-to-r from-cyan-950/70 via-[#0f172a] to-purple-950/60 border border-cyan-400/40 shadow-[0_0_30px_rgba(34,211,238,0.2)] flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="p-4 rounded-2xl bg-cyan-500/20 text-cyan-300">
              <FileText size={28} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-2.5 py-0.5 rounded-full border border-cyan-400/30">
                  Ready for Client Review
                </span>
                {lastMeetingTime && (
                  <span className="text-xs text-gray-400">
                    {new Date(lastMeetingTime).toLocaleString()}
                  </span>
                )}
              </div>
              <h3 className="text-xl font-bold text-white mt-1">
                Extracted Requirements Package (ID: <span className="font-mono text-cyan-300">{lastMeetingId.slice(0, 8)}</span>)
              </h3>
              <p className="text-gray-400 text-sm">
                Review functional requirements, quality attributes, and authorize the architecture design pipeline.
              </p>
            </div>
          </div>

          <Link to={`/client/requirements/${lastMeetingId}`}>
            <button className="flex items-center gap-2 px-6 py-3.5 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider rounded-full shadow-lg transition duration-300 active:scale-95 cursor-pointer whitespace-nowrap">
              <ArrowRight size={16} />
              Review & Approve Requirements
            </button>
          </Link>
        </div>
      )}

      {/* CLIENT PROJECTS LIST */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <FolderOpen className="text-cyan-400" size={24} />
          Your Projects
        </h2>

        {projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-16 rounded-3xl border border-dashed border-cyan-400/20 bg-white/5 backdrop-blur-sm text-center">
            <div className="p-5 rounded-full bg-cyan-950/40 text-cyan-300 mb-6">
              <FolderOpen size={48} />
            </div>
            <h3 className="text-2xl font-bold mb-2">No Projects Assigned Yet</h3>
            <p className="text-gray-400 max-w-md mb-4">
              When a Product Owner creates a project and assigns you as the Client, it will appear here for requirements review.
            </p>
            <p className="text-xs text-cyan-400/80">
              You can also open any requirements package directly using the search bar above with a Meeting ID.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {projects.map((project) => (
              <div
                key={project.id}
                className="group relative flex flex-col justify-between p-8 rounded-3xl border border-white/10 bg-[#0f172a]/90 hover:border-cyan-400/50 shadow-xl transition-all duration-300 hover:shadow-[0_0_30px_rgba(34,211,238,0.15)] overflow-hidden"
              >
                {/* Accent Glow */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none group-hover:bg-cyan-500/20 transition-all duration-500"></div>

                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold text-white group-hover:text-cyan-300 transition duration-300">
                      {project.name}
                    </h3>
                    <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                      Client Review Active
                    </span>
                  </div>

                  <p className="text-gray-400 text-sm leading-relaxed mb-6 line-clamp-3">
                    {project.description || "No project description provided."}
                  </p>

                  <div className="space-y-3 mb-8 pt-4 border-t border-white/5">
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <User size={14} className="text-cyan-400" />
                      <span>Product Owner: <strong>{project.product_owner_name || "Lead BA"}</strong></span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <Users size={14} className="text-purple-400" />
                      <span>Client: <strong>{currentUser?.name || project.client_name || "You"}</strong></span>
                    </div>
                    {project.created_at && (
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <Calendar size={14} className="text-gray-500" />
                        <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-white/5">
                  <button
                    onClick={() => {
                      const mId = project.latest_meeting_id || project.id;
                      navigate(`/client/requirements/${mId}`);
                    }}
                    className="flex-1 flex items-center justify-center gap-2 px-5 py-3.5 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold rounded-2xl transition duration-300 cursor-pointer shadow-lg"
                  >
                    <FileText size={16} />
                    Review Requirements
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
