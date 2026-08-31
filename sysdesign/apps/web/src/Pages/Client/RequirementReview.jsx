import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { 
  FileText, 
  CheckCircle2, 
  XCircle, 
  Layers, 
  ShieldCheck, 
  Cpu, 
  Share2, 
  Sparkles,
  Info,
  HelpCircle,
  Clock
} from "lucide-react";

const AGENT1 = import.meta.env.VITE_AGENT1_URL || "http://127.0.0.1:8001";

export default function RequirementReview() {
  const { meetingId } = useParams();
  const navigate = useNavigate();
  const [requirements, setRequirements] = useState(null);
  const [version, setVersion] = useState(1);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedBackModal, setFeedBackModal] = useState(false);

  console.log("meeting id", meetingId)

  const fetchRequirements = async () => {
    try {
      let res;
      try {
        res = await axios.get(`${AGENT1}/requirements/${meetingId}`);
      } catch (e1) {
        res = await axios.get(`/requirements/${meetingId}`);
      }
      if (res?.data) {
        setRequirements(res.data.requirements || { functional: [], non_functional: [] });
        if (res.data.version) setVersion(res.data.version);
      }
    } catch (err) {
      console.error(err);
      setRequirements({ functional: [], non_functional: [] });
    }
  };

  useEffect(() => {
    if (meetingId) {
      fetchRequirements();
    }
  }, [meetingId]);

  if (!requirements) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-white bg-transparent">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400 mb-4"></div>
        <p className="text-cyan-300 font-medium animate-pulse">Loading requirements package...</p>
      </div>
    );
  }

  const handleRefine = async () => {
    if (!feedback.trim()) return;
    setLoading(true);
    try {
      await axios.post(`${AGENT1}/refine-reqs`, {
        feedback: feedback,
        requirements: requirements,
        meetingId: meetingId,
      });
      await fetchRequirements();
      setFeedback("");
      setFeedBackModal(false);
    } catch (err) {
      console.error("Refine failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      setLoading(true);
      const res = await axios.post(`${AGENT1}/approve-reqs`, {
        meeting_id: meetingId,
      });
      const jobId = res.data?.job_id;
      if (jobId) {
        navigate(`/pipeline/${jobId}`);
      } else {
        navigate("/project-dashboard");
      }

    } catch (err) {
      console.error("Approve failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full pt-28 pb-16 px-4 md:px-12 text-white">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* HEADER BADGE & TITLE */}
        <div className="relative p-8 rounded-3xl bg-[#0f172a]/90 border border-white/10 shadow-2xl backdrop-blur-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3">
                <ShieldCheck size={14} />
                IEEE 29148 Specification Review
              </div>
              <h1 
                style={{ fontFamily: "Orbitron, sans-serif" }} 
                className="text-3xl md:text-4xl font-extrabold text-white"
              >
                Requirements <span className="text-cyan-300">Package</span>
              </h1>
            </div>

            <div className="flex items-center gap-3">
              <span className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-gray-300">
                Version <strong>v{version}.0</strong>
              </span>
              <span className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-gray-300">
                ID: <strong className="font-mono text-cyan-300">{meetingId.slice(0, 8)}</strong>
              </span>
            </div>
          </div>

          <p className="text-gray-300 text-sm leading-relaxed max-w-3xl">
            This is the full software requirements specification package extracted by <strong>Agent 1 (Requirements Intelligence)</strong>. Please review all executive summaries, functional scope, quality constraints, and system interface details before approving for architecture design generation.
          </p>
        </div>

        {/* SECTION 1: PURPOSE & SCOPE */}
        {(requirements.purpose || requirements.scope) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {requirements.purpose && (
              <div className="p-6 rounded-3xl bg-gradient-to-br from-cyan-950/40 via-[#0f172a] to-black border border-cyan-500/20 shadow-lg">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-300">
                    <Sparkles size={18} />
                  </div>
                  <h3 className="text-lg font-bold text-cyan-300">System Purpose</h3>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {requirements.purpose}
                </p>
              </div>
            )}

            {requirements.scope && (
              <div className="p-6 rounded-3xl bg-gradient-to-br from-purple-950/40 via-[#0f172a] to-black border border-purple-500/20 shadow-lg">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-300">
                    <Layers size={18} />
                  </div>
                  <h3 className="text-lg font-bold text-purple-300">Product Scope</h3>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {requirements.scope}
                </p>
              </div>
            )}
          </div>
        )}

        {/* SECTION 2: FUNCTIONAL REQUIREMENTS */}
        <div className="p-8 rounded-3xl bg-[#0f172a]/90 border border-white/10 shadow-2xl backdrop-blur-xl space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <h2 className="text-xl font-bold text-cyan-300 tracking-wide flex items-center gap-2">
              <FileText size={20} />
              1. Functional Requirements ({requirements.functional?.length || 0})
            </h2>
            <span className="text-xs text-gray-400">Behavioral Specifications</span>
          </div>

          {!requirements.functional || requirements.functional.length === 0 ? (
            <p className="text-gray-400 italic text-sm">No functional requirements extracted yet.</p>
          ) : (
            <div className="space-y-4">
              {requirements.functional.map((r, index) => (
                <div
                  key={r.id || index}
                  className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-cyan-400/40 hover:bg-cyan-400/5 transition-all duration-300 space-y-2"
                >
                  <div className="flex items-start justify-between gap-4">
                    <p className="text-gray-100 font-medium leading-relaxed">
                      <span className="text-cyan-300 font-bold mr-2.5">
                        {r.id || `FR-${index + 1}`}:
                      </span>
                      {r.description}
                    </p>
                  </div>

                  {/* Evidence Quotes */}
                  {r.source_evidence && r.source_evidence.length > 0 && (
                    <div className="pt-2 border-t border-white/5 space-y-1">
                      {r.source_evidence.map((ev, i) => (
                        <p key={i} className="text-xs text-gray-400 italic flex items-center gap-2">
                          <span className="text-cyan-400 font-semibold uppercase font-sans text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800">
                            {ev.speaker || "Evidence"}
                          </span>
                          "{ev.statement}"
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SECTION 3: NON-FUNCTIONAL REQUIREMENTS */}
        <div className="p-8 rounded-3xl bg-[#0f172a]/90 border border-white/10 shadow-2xl backdrop-blur-xl space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <h2 className="text-xl font-bold text-purple-300 tracking-wide flex items-center gap-2">
              <Cpu size={20} />
              2. Non-Functional Requirements ({requirements.non_functional?.length || 0})
            </h2>
            <span className="text-xs text-gray-400">ISO/IEC 25010 Quality Attributes</span>
          </div>

          {!requirements.non_functional || requirements.non_functional.length === 0 ? (
            <p className="text-gray-400 italic text-sm">No non-functional requirements specified.</p>
          ) : (
            <div className="space-y-4">
              {requirements.non_functional.map((r, index) => (
                <div
                  key={r.id || index}
                  className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-400/40 hover:bg-purple-400/5 transition-all duration-300 space-y-2"
                >
                  <p className="text-gray-100 font-medium leading-relaxed">
                    <span className="text-purple-300 font-bold mr-2.5">
                      {r.id || `NFR-${index + 1}`}:
                    </span>
                    {r.description}
                  </p>

                  {r.source_evidence && r.source_evidence.length > 0 && (
                    <div className="pt-2 border-t border-white/5 space-y-1">
                      {r.source_evidence.map((ev, i) => (
                        <p key={i} className="text-xs text-gray-400 italic flex items-center gap-2">
                          <span className="text-purple-400 font-semibold uppercase font-sans text-[10px] px-1.5 py-0.5 rounded bg-purple-950 border border-purple-800">
                            {ev.speaker || "Evidence"}
                          </span>
                          "{ev.statement}"
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SECTION 4: EXTERNAL INTERFACES & DESIGN CONSTRAINTS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* External Interfaces */}
          <div className="p-6 rounded-3xl bg-[#0f172a]/90 border border-white/10 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-cyan-300 flex items-center gap-2">
              <Share2 size={18} />
              External Interfaces & Services
            </h3>

            {!requirements.external_interfaces || requirements.external_interfaces.length === 0 ? (
              <p className="text-gray-400 italic text-sm">No external system interfaces identified.</p>
            ) : (
              <div className="space-y-3">
                {requirements.external_interfaces.map((ext, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-xs space-y-1">
                    <div className="font-semibold text-cyan-300">
                      {ext.interacting_external_entity || ext.interacting_entity || `Interface #${idx+1}`}
                    </div>
                    {ext.purpose && <div className="text-gray-300">Purpose: {ext.purpose}</div>}
                    {ext.information_exchanged && <div className="text-gray-400 italic">Data: {ext.information_exchanged}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Constraints & Supporting Info */}
          <div className="p-6 rounded-3xl bg-[#0f172a]/90 border border-white/10 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-purple-300 flex items-center gap-2">
              <Info size={18} />
              Design Constraints & Assumptions
            </h3>

            {!requirements.design_constraints || requirements.design_constraints.length === 0 ? (
              <p className="text-gray-400 italic text-sm">No specific design constraints noted.</p>
            ) : (
              <div className="space-y-2">
                {requirements.design_constraints.map((c, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-white/5 border border-white/5 text-xs text-gray-300 flex items-start gap-2">
                    <span className="text-purple-400 font-bold">•</span>
                    <span>{typeof c === 'string' ? c : c.description || JSON.stringify(c)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* BOTTOM ACTION BAR */}
        <div className="sticky bottom-6 p-6 rounded-3xl bg-[#0f172a]/95 border border-cyan-400/30 shadow-[0_0_40px_rgba(0,0,0,0.8)] backdrop-blur-2xl flex flex-col sm:flex-row items-center justify-between gap-4 z-30">
          <div>
            <div className="text-sm font-bold text-white">Requirements Verification & Pipeline Launch</div>
            <div className="text-xs text-gray-400">Confirm specifications above to generate High-Level Design (HLD), Low-Level Design (LLD), UI Wireframes, and SRS Document.</div>
          </div>

          <div className="flex items-center gap-4 w-full sm:w-auto">
            {/* <button
              onClick={() => setFeedBackModal(true)}
              className="flex-1 sm:flex-none px-6 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/30 rounded-full font-semibold text-xs uppercase tracking-wider transition duration-300 cursor-pointer"
            >
              Refine Requirements
            </button> */}

            <button
              onClick={handleApprove}
              disabled={loading}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-8 py-3.5 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white border border-cyan-300/40 rounded-full font-bold text-xs uppercase tracking-wider shadow-[0_0_25px_rgba(34,211,238,0.4)] transition duration-300 active:scale-95 cursor-pointer disabled:opacity-50"
            >
              {loading ? "Launching Pipeline..." : "Confirm & Launch Pipeline 🚀"}
            </button>
          </div>
        </div>

      </div>

      {/* REFINEMENT FEEDBACK MODAL */}
      {feedBackModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center z-50 px-4">
          <div className="relative w-full max-w-2xl bg-[#0f172a] border border-white/10 rounded-3xl shadow-2xl overflow-hidden p-8 space-y-6">
            <div className="absolute top-0 left-0 w-72 h-72 bg-cyan-500/10 blur-3xl rounded-full pointer-events-none" />

            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Sparkles size={20} className="text-cyan-400" />
                Refine Software Requirements
              </h2>
              <p className="mt-2 text-gray-400 text-sm leading-relaxed">
                Enter your requested additions, corrections, or constraints. Agent 1 will re-evaluate the specs and update all requirements.
              </p>
            </div>

            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Example: Add functional requirements for staff updating prices, include mobile push notifications, enforce 2-second response latency constraint..."
              className="w-full h-44 p-4 rounded-2xl bg-white/5 border border-white/10 text-white placeholder:text-gray-500 outline-none resize-none focus:border-cyan-400/50 text-sm"
            />

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setFeedBackModal(false)}
                className="px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-gray-400 border border-white/10 rounded-full hover:bg-white/5 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleRefine}
                disabled={loading}
                className="px-6 py-2.5 text-xs font-semibold uppercase tracking-wider text-white bg-cyan-600 hover:bg-cyan-500 rounded-full shadow-lg transition disabled:opacity-50"
              >
                {loading ? "Refining..." : "Submit Refinements"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}