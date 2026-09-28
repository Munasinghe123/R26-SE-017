import React, { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate, useParams } from "react-router-dom";
import beehiveBg from "../../../Images/beehive-bg.png";
import requirmentsCard from "../../../Images/requirments-card.png";
import { Rocket, FolderGit2, ShieldCheck } from "lucide-react";
import api from "../../../api/api";
import ProjectSidebar from "../../../components/Project-Dashboard/ProjectSidebar";
import { updateUser } from "../../../Redux/UserSlice";
import { setCurrentProject } from "../../../Redux/ProjectSlice";

// Modals
import SelectModeModal from "../../../components/Project-Dashboard/Modals/SelectModeModal";
import UploadModal from "../../../components/Project-Dashboard/Modals/UploadModal";
import EmptyProjectState from "../../../components/Project-Dashboard/Modals/EmptyProjectState";
import CreateProjectModal from "../../../components/Project-Dashboard/Modals/CreateProjectModal";
import QualityEvaluationModal from "../../../components/Project-Dashboard/Modals/QualityEvaluationModal";
import ClientRequirementReview from "../../../components/Project-Dashboard/Modals/ClientRequirementReview";
import { devForceStartHLD } from "../../../utils/devBypass";

export default function ProjectDashboard() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const currentUser = useSelector((state) => state.user.userInfo);

  // --------------------------------------------------
  // Projects
  // --------------------------------------------------

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // Final requirements stored per project
  const [finalRequirements, setFinalRequirements] = useState({});

  // Final requirements modal
  const [showFinalRequirements, setShowFinalRequirements] = useState(false);
  const [finalRequirementsLoading, setFinalRequirementsLoading] =
    useState(false);

  // --------------------------------------------------
  // Modals
  // --------------------------------------------------

  const [showSelectMode, setShowSelectMode] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showQualityModal, setShowQualityModal] = useState(false);
  const [qualityEvaluationData, setQualityEvaluationData] = useState(null);
  const [qualityLoading, setQualityLoading] = useState(false);
  const [approvingHLD, setApprovingHLD] = useState(false);
  const [showClientReviewModal, setShowClientReviewModal] = useState(false);

  // --------------------------------------------------
  // Fetch projects
  // --------------------------------------------------

  useEffect(() => {
    const fetchProjects = async () => {
      if (!currentUser?.id) {
        setLoading(false);
        return;
      }

      try {
        const response = await api.get(`/projects/user/${currentUser.id}`);

        console.log("Fetched projects:", response.data);

        setProjects(response.data?.projects ?? []);
      } catch (error) {
        console.error("Failed to fetch projects:", error);
        setProjects([]);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [currentUser?.id]);

  // --------------------------------------------------
  // Active project
  // --------------------------------------------------

  const safeProjects = Array.isArray(projects) ? projects : [];
  const activeProject = safeProjects.find(
    (project) => project?.id === projectId,
  );

  console.log("Active project:", activeProject);

  useEffect(() => {
    if (activeProject) {
      dispatch(setCurrentProject(activeProject));
    }
  }, [activeProject, dispatch]);

  const id = activeProject?.id;
  const analysisStatus =
    activeProject?.analysis_status ?? (activeProject?.status || "idle");

  // Final requirements belonging ONLY to the selected project
  const projectFinalRequirements = id ? finalRequirements[id] : null;

  // --------------------------------------------------
  // Quality Evaluation & HLD Handlers
  // --------------------------------------------------

  const handleOpenQualityEvaluation = async () => {
    setShowQualityModal(true);
    if (qualityEvaluationData) return;

    setQualityLoading(true);
    const targetMeetingId =
      activeProject?.latest_meeting_id ||
      activeProject?.meeting_id ||
      activeProject?.thread_id ||
      id ||
      projectId;

    try {
      let res;
      try {
        res = await api.get(`/requirements/${targetMeetingId}/evaluation`);
      } catch (err) {
        console.warn(
          "Direct evaluation get failed, trying fallback POST:",
          err,
        );
        const reqRes = await api.get(`/requirements/${targetMeetingId}`);
        const reqs =
          reqRes.data?.final_requirements || reqRes.data?.requirements || {};
        res = await api.post("/evaluate-requirements", {
          requirements: reqs,
          meetingId: targetMeetingId,
        });
      }

      setQualityEvaluationData(res.data);
    } catch (error) {
      console.error("Failed to load quality evaluation:", error);
      alert(
        "Could not load quality evaluation. Please check server connection.",
      );
    } finally {
      setQualityLoading(false);
    }
  };

  const handleContinueHLD = async () => {
    const targetMeetingId =
      activeProject?.latest_meeting_id ||
      activeProject?.meeting_id ||
      activeProject?.thread_id ||
      id ||
      projectId;

    setApprovingHLD(true);
    try {
      const res = await api.post("/approve-reqs", {
        meeting_id: targetMeetingId,
      });

      const jobId = res.data?.job_id;
      if (jobId) {
        navigate(`/project/${projectId}/pipeline/${jobId}`);
      } else {
        navigate(`/project-dashboard/${projectId}`);
      }
    } catch (error) {
      console.error("Failed to approve requirements and trigger HLD:", error);
      alert("Could not start HLD pipeline. Please try again.");
    } finally {
      setApprovingHLD(false);
    }
  };

  const handleDevContinueHLD = async () => {
    const targetMeetingId =
      activeProject?.latest_meeting_id ||
      activeProject?.meeting_id ||
      activeProject?.thread_id ||
      id ||
      projectId;

    setApprovingHLD(true);
    try {
      const jobId = await devForceStartHLD(targetMeetingId, activeProject?.name);
      navigate(`/project/${projectId}/pipeline/${jobId}`);
    } catch (error) {
      console.error("Failed to start HLD pipeline via dev bypass:", error);
      alert("Could not start HLD pipeline: " + (error?.response?.data?.detail || error.message));
    } finally {
      setApprovingHLD(false);
    }
  };

  // --------------------------------------------------
  // Loading
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#080A14] text-cyan-300">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
          <p className="text-sm font-medium tracking-wider uppercase text-gray-400">
            Loading projects...
          </p>
        </div>
      </div>
    );
  }

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#080A14] text-white">
      {/* Collapsible Sidebar */}
      <ProjectSidebar
        projects={safeProjects}
        activeProjectId={projectId}
        userRole={currentUser?.role}
        onCreateProject={() => setShowCreateProject(true)}
      />

      {/* Main Content */}
      <main className="min-w-0 flex-1 overflow-y-auto custom-scrollbar">
        <div className="flex min-h-full items-center justify-center py-10 px-4 md:px-8">
          {(currentUser?.role === "USER" || !currentUser?.role) &&
          safeProjects.length === 0 ? (
            <EmptyProjectState
              onCreateProject={() => setShowCreateProject(true)}
            />
          ) : !projectId && currentUser?.role === "PRODUCT_OWNER" ? (
            <div className="flex flex-col items-center justify-center text-center p-8 space-y-4">
              <div className="p-5 rounded-3xl bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 shadow-[0_0_30px_rgba(34,211,238,0.2)]">
                <FolderGit2 size={44} />
              </div>
              <h2
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="text-3xl font-bold uppercase text-white"
              >
                Project <span className="text-cyan-300">Workspace</span>
              </h2>
              <p className="text-gray-400 max-w-md text-sm">
                Select a project from the sidebar to manage analysis status,
                review elicitation, or start a new multi-agent pipeline.
              </p>
            </div>
          ) : !projectId && currentUser?.role === "CLIENT" ? (
            <div className="flex flex-col items-center justify-center text-center p-8 space-y-4">
              <div className="p-5 rounded-3xl bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 shadow-[0_0_30px_rgba(34,211,238,0.2)]">
                <FolderGit2 size={44} />
              </div>
              <h2
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="text-3xl font-bold uppercase text-white"
              >
                Project <span className="text-cyan-300">Review</span>
              </h2>
              <p className="text-gray-400 max-w-md text-sm">
                You will be notified for the projects that are ready for your
                review. Please select a project from the sidebar to view the
                requirements and provide your feedback.
              </p>
            </div>
          ) : !activeProject && currentUser?.role === "PRODUCT_OWNER" ? (
            <div className="text-center text-gray-500 space-y-3">
              <p className="text-xl font-medium text-gray-400">
                Project not found
              </p>
              <p className="text-sm text-gray-500">
                The requested project could not be found or has been moved.
              </p>
              <button
                type="button"
                onClick={() => navigate("/project-dashboard")}
                className="px-5 py-2.5 rounded-full border border-cyan-400/40 bg-cyan-500/10 text-cyan-300 text-xs font-semibold uppercase tracking-wider hover:bg-cyan-500/20 transition cursor-pointer"
              >
                Back to Workspace
              </button>
            </div>
          ) : (
            <div className="w-full max-w-4xl px-4 md:px-8 space-y-10">
              {/* Page title */}
              <h1
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="text-white text-center text-4xl md:text-5xl uppercase font-bold"
              >
                Awaiting <span className="text-cyan-300">Analysis</span>
              </h1>

              {/* Project Card */}
              <div className="relative w-full max-w-5xl overflow-hidden rounded-3xl border border-cyan-400/20 bg-gradient-to-br from-cyan-800/80 via-cyan-950/80 to-black shadow-[0_0_50px_rgba(34,211,238,0.25)]">
                {/* Top-left beehive */}
                <img
                  src={beehiveBg}
                  alt=""
                  className="pointer-events-none absolute -left-24 -top-24 w-[330px] opacity-20"
                />

                {/* Bottom-right beehive */}
                <img
                  src={beehiveBg}
                  alt=""
                  className="pointer-events-none absolute -bottom-28 -right-24 z-0 w-[350px] rotate-180 opacity-20"
                />

                {/* Main content */}
                <div className="relative z-10 grid h-full grid-cols-1 md:grid-cols-2 px-8 md:px-14 py-8">
                  <div className="flex h-full flex-col justify-between">
                    <div>
                      {/* Project date */}
                      {activeProject?.created_at && (
                        <span className="inline-flex w-fit items-center rounded-full border border-cyan-400/30 bg-white/10 px-4 py-1.5 text-xs font-medium tracking-[0.25em] text-cyan-300">
                          {new Date(
                            activeProject.created_at,
                          ).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </span>
                      )}

                      {/* Project information */}
                      <div className="flex flex-1 flex-col justify-center py-6">
                        <h1
                          style={{ fontFamily: "Orbitron, sans-serif" }}
                          className="text-3xl md:text-4xl font-semibold capitalize tracking-wide text-white"
                        >
                          {activeProject?.name}
                        </h1>

                        <div className="mt-2 h-0.5 w-28 bg-cyan-400" />

                        <p className="mt-4 max-w-2xl text-sm md:text-base leading-relaxed text-white/70">
                          {activeProject?.description ||
                            "No description provided for this project."}
                        </p>

                        {/* PRODUCT OWNER / USER */}
                        {currentUser?.role === "PRODUCT_OWNER" ||
                        currentUser?.role === "USER" ||
                        !currentUser?.role ? (
                          analysisStatus === "waiting" ? (
                            <>
                              <div className="mt-6 flex w-fit items-center gap-3 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-5 py-3.5 text-sm font-medium uppercase tracking-[2px] text-cyan-300">
                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-300/20 border-t-cyan-300" />
                                Submitted for Review
                              </div>
                              {/* this button was added temporarily */}
                              <button
                                type="button"
                                disabled={approvingHLD}
                                onClick={handleDevContinueHLD}
                                className="group mt-5 relative flex w-[270px] justify-center items-center gap-3 cursor-pointer py-3.5 text-sm font-medium uppercase tracking-[2px] text-white rounded-full border border-cyan-400/60 bg-black backdrop-blur-md overflow-hidden transition-all duration-300 hover:border-cyan-200 hover:shadow-[0_0_25px_rgba(34,211,238,0.5)] active:scale-95"
                              >
                                <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent" />
                                {approvingHLD ? (
                                  <>
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                    <span>Starting Pipeline...</span>
                                  </>
                                ) : (
                                  <>
                                    <Rocket
                                      size={18}
                                      className="relative z-10 text-cyan-300 group-hover:text-white transition-colors"
                                    />
                                    <span className="tracking-[2px]">
                                      Continue for HLD (temp)
                                    </span>
                                  </>
                                )}
                              </button>
                            </>
                          ) : analysisStatus === "completed" ? (
                            <div className="mt-6 flex flex-wrap items-center gap-4">
                              {/* 1. Quality Evaluation Button */}
                              <button
                                type="button"
                                onClick={handleOpenQualityEvaluation}
                                className="group relative flex w-[270px] justify-center items-center gap-3 cursor-pointer py-3.5 text-sm font-semibold uppercase tracking-[2px] text-cyan-300 rounded-full border border-cyan-400/60 bg-cyan-950/40 backdrop-blur-md overflow-hidden transition-all duration-300 hover:border-cyan-300 hover:text-white hover:shadow-[0_0_25px_rgba(34,211,238,0.4)] active:scale-95"
                              >
                                <ShieldCheck
                                  size={18}
                                  className="text-cyan-400 group-hover:scale-110 transition-transform duration-300"
                                />
                                <span>Quality Evaluation</span>
                              </button>

                              {/* 2. Continue for HLD Button */}
                              <button
                                type="button"
                                disabled={approvingHLD}
                                onClick={handleContinueHLD}
                                className="group relative flex w-[270px] justify-center items-center gap-3 cursor-pointer py-3.5 text-sm font-medium uppercase tracking-[2px] text-white rounded-full border border-cyan-400/60 bg-black backdrop-blur-md overflow-hidden transition-all duration-300 hover:border-cyan-200 hover:shadow-[0_0_25px_rgba(34,211,238,0.5)] active:scale-95"
                              >
                                <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent" />
                                {approvingHLD ? (
                                  <>
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                    <span>Starting Pipeline...</span>
                                  </>
                                ) : (
                                  <>
                                    <Rocket
                                      size={18}
                                      className="relative z-10 text-cyan-300 group-hover:text-white transition-colors"
                                    />
                                    <span className="tracking-[2px]">
                                      Continue for HLD
                                    </span>
                                  </>
                                )}
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setShowSelectMode(true)}
                              type="button"
                              className="group relative mt-6 flex w-fit items-center gap-3 cursor-pointer px-6 py-3.5 text-sm font-medium uppercase tracking-[2px] text-white rounded-full border border-cyan-400/60 bg-black backdrop-blur-md overflow-hidden transition-all duration-300 hover:border-cyan-200 hover:shadow-[0_0_25px_rgba(34,211,238,0.5)] active:scale-95"
                            >
                              {/* Glowing center layers */}
                              <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent" />

                              <Rocket
                                size={17}
                                className="relative z-10 text-cyan-300 group-hover:text-white transition-colors"
                              />
                              <span className="relative z-10 font-semibold tracking-[2px]">
                                Start Analysis
                              </span>
                            </button>
                          )
                        ) : currentUser?.role === "CLIENT" ? (
                          analysisStatus === "waiting" ||
                          activeProject?.latest_meeting_id ? (
                            <div className="mt-5 space-y-3">
                              <div className="flex items-center gap-3 rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-4 py-3 text-sm">
                                <div>
                                  <p className="font-semibold text-cyan-300">
                                    Requirements Ready for Review
                                  </p>
                                  <p className="text-white/60 text-xs mt-0.5">
                                    The requirements are waiting for your
                                    review.
                                  </p>
                                </div>
                              </div>

                              <button
                                type="button"
                                onClick={() => {
                                  setShowClientReviewModal(true);
                                }}
                                className="flex w-fit items-center gap-3 rounded-full border border-cyan-400/60 bg-black px-5 py-3.5 text-sm font-medium uppercase tracking-[2px] text-cyan-300 transition-all duration-300 hover:border-cyan-200 hover:text-white hover:shadow-[0_0_20px_rgba(34,211,238,0.4)] cursor-pointer"
                              >
                                Review Requirements
                              </button>
                            </div>
                          ) : analysisStatus === "completed" ? (
                            <div className="mt-5 flex items-center gap-3 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-sm">
                              <div>
                                <p className="font-semibold text-emerald-300">
                                  Requirements Approved
                                </p>
                                <p className="text-white/60 text-xs mt-0.5">
                                  Your review is complete.
                                </p>
                              </div>
                            </div>
                          ) : (
                            <div className="mt-5 flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-gray-400">
                              <p>
                                Waiting for Product Owner to start requirements
                                analysis.
                              </p>
                            </div>
                          )
                        ) : null}
                      </div>
                    </div>
                  </div>

                  {/* Requirements image */}
                  <div className="absolute inset-y-0 right-0 flex w-[45%] items-end justify-end pointer-events-none">
                    <img
                      src={requirmentsCard}
                      alt="Requirements analysis"
                      className="h-full w-full object-contain object-right-bottom opacity-75"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ============================================================
          SELECT MODE MODAL
         ============================================================ */}

      {showClientReviewModal && (
        <ClientRequirementReview
          onClose={() => setShowClientReviewModal(false)}
          projectId={projectId}
        />
      )}

      {showSelectMode && (
        <SelectModeModal
          onClose={() => setShowSelectMode(false)}
          onSelectMode={(mode) => {
            console.log("Selected mode:", mode);
            if (mode === "upload") {
              setShowUpload(true);
              setShowSelectMode(false);
            }
            if (mode === "meeting") {
              navigate("/test-meeting", { state: { projectId } });
            }
          }}
        />
      )}

      {/* ============================================================
          UPLOAD MODAL
         ============================================================ */}

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          projectId={projectId}
          onSubmit={(data) => {
            console.log("Upload response:", data);
            const threadId = data.thread_id || data.meeting_id;
            setProjects((prev) => {
              const prevList = Array.isArray(prev) ? prev : [];
              return prevList.map((project) =>
                project.id === projectId
                  ? {
                      ...project,
                      thread_id: threadId,
                      latest_meeting_id: threadId,
                      meeting_id: threadId,
                      analysis_status: "waiting",
                    }
                  : project,
              );
            });

            setFinalRequirements((prev) => {
              const next = { ...prev };
              delete next[projectId];
              return next;
            });

            setShowUpload(false);
          }}
        />
      )}

      {/* ============================================================
          CREATE PROJECT MODAL
         ============================================================ */}

      {showCreateProject && (
        <CreateProjectModal
          onClose={() => setShowCreateProject(false)}
          onCreated={(data) => {
            setProjects((prev) => [
              ...(Array.isArray(prev) ? prev : []),
              data.project,
            ]);
            if (data.product_owner) {
              dispatch(updateUser(data.product_owner));
            }
            setShowCreateProject(false);
            navigate(`/project-dashboard/${data.project.id}`);
          }}
        />
      )}

      {/* ============================================================
          FINAL REQUIREMENTS MODAL
         ============================================================ */}

      {showFinalRequirements && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="relative flex max-h-[85vh] w-[850px] flex-col overflow-hidden rounded-3xl border border-cyan-400/20 bg-[#080A14] shadow-[0_0_60px_rgba(34,211,238,0.15)]">
            {/* Modal header */}
            <div className="flex shrink-0 items-center justify-between border-b border-white/10 px-8 py-6">
              <div>
                <p className="text-xs uppercase tracking-[3px] text-cyan-300">
                  Analysis Complete
                </p>
                <h2
                  style={{ fontFamily: "Orbitron, sans-serif" }}
                  className="mt-2 text-3xl font-semibold text-white"
                >
                  Final Requirements
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setShowFinalRequirements(false)}
                className="rounded-full p-2 text-gray-500 transition hover:bg-white/5 hover:text-white cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Modal content */}
            <div className="flex-1 overflow-y-auto px-8 py-6 custom-scrollbar">
              {projectFinalRequirements?.sections?.map((section) => (
                <div key={section.title} className="mb-8 last:mb-0">
                  <h3
                    style={{ fontFamily: "Orbitron, sans-serif" }}
                    className="mb-4 text-xl font-semibold text-cyan-300"
                  >
                    {section.title}
                  </h3>

                  <div className="space-y-4">
                    {section.items?.map((item, index) => (
                      <div
                        key={item.id ?? index}
                        className="rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-4"
                      >
                        <div className="mb-2 flex items-center gap-3">
                          <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-300">
                            {item.id}
                          </span>
                        </div>

                        <p className="text-sm leading-relaxed text-white/80">
                          {item.text}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          QUALITY EVALUATION MODAL
         ============================================================ */}
      <QualityEvaluationModal
        isOpen={showQualityModal}
        onClose={() => setShowQualityModal(false)}
        evaluationData={qualityEvaluationData}
        loading={qualityLoading}
      />
    </div>
  );
}
