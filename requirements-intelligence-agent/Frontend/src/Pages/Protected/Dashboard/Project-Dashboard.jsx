import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate, useParams } from "react-router-dom";
import beehiveBg from "../../../Images/beehive-bg.png";
import { Rocket } from "lucide-react";
import api from "../../../api/api";
import ProjectSidebar from "../../../components/Project-Dashboard/ProjectSidebar";
import requirmentsCard from "../../../Images/requirments-card.png";
import { useDispatch } from "react-redux";
import { updateUser } from "../../../Redux/UserSlice";

// Modals
import SelectModeModal from "../../../components/Project-Dashboard/Modals/SelectModeModal";
import UploadModal from "../../../components/Project-Dashboard/Modals/UploadModal";
import EmptyProjectState from "../../../components/Project-Dashboard/Modals/EmptyProjectState";
import CreateProjectModal from "../../../components/Project-Dashboard/Modals/CreateProjectModal";

export default function ProjectDashboard() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const currentUser = useSelector((state) => state.user.userInfo);

  console.log("current user", currentUser);

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

        setProjects(response.data.projects);

        console.log("PROJECTS:", response.data.projects);
      } catch (error) {
        console.error("Failed to fetch projects:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [currentUser?.id]);

  // --------------------------------------------------
  // Active project
  // --------------------------------------------------

  const activeProject = projects.find((project) => project.id === projectId);

  const threadId = activeProject?.thread_id;

  const analysisStatus = activeProject?.analysis_status ?? "idle";

  // Final requirements belonging ONLY to the selected project
  const projectFinalRequirements = finalRequirements[projectId];

  // --------------------------------------------------
  // Loading
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#080A14] text-gray-400">
        Loading projects...
      </div>
    );
  }

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#080A14] text-white">
      {/* Sidebar */}

      <ProjectSidebar
        projects={projects}
        activeProjectId={projectId}
        userRole={currentUser?.role}
        onCreateProject={() => setShowCreateProject(true)}
      />

      {/* Main Content */}

      <main className="min-w-0 flex-1 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center py-10">
          {currentUser?.role === "USER" && projects.length === 0 ? (
            <EmptyProjectState
              onCreateProject={() => setShowCreateProject(true)}
            />
          ) : !projectId ? (
            <div className="text-center text-gray-500">
              <p className="text-lg">Select a project to continue</p>
            </div>
          ) : !activeProject ? (
            <div className="text-center text-gray-500">
              <p className="text-lg">Project not found</p>
            </div>
          ) : (
            <div className="w-full max-w-4xl px-8 space-y-10">
              {/* Page title */}

              <h1
                className="text-white text-center text-5xl uppercase font-bold"
                style={{
                  fontFamily: "Orbitron, sans-serif",
                }}
              >
                Awaiting <span className="text-cyan-300">Analysis</span>
              </h1>

              {/* Project Card */}

              <div
                className="
                  relative
                  w-full
                  max-w-5xl
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
                    z-0
                    w-[350px]
                    rotate-180
                    opacity-20
                  "
                />

                {/* Main content */}

                <div className="relative z-10 grid h-full grid-cols-2 px-14 py-5">
                  <div className="flex h-full flex-col">
                    {/* Project date */}

                    <span
                      className="
                        inline-flex
                        w-fit
                        items-center
                        rounded-full
                        border border-cyan-400/30
                        bg-white/10
                        px-4
                        py-1.5
                        text-xs
                        font-medium
                        tracking-[0.25em]
                        text-cyan-300
                      "
                    >
                      {new Date(activeProject.created_at).toLocaleDateString(
                        "en-US",
                        {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        },
                      )}
                    </span>

                    {/* Project information */}

                    <div className="flex flex-1 flex-col justify-center py-6">
                      <h1
                        style={{
                          fontFamily: "Orbitron, sans-serif",
                        }}
                        className="
                          text-4xl
                          font-semibold
                          capitalize
                          tracking-wide
                          text-white
                        "
                      >
                        {activeProject.name}
                      </h1>

                      <div className="mt-1 h-0.5 w-28 bg-cyan-400" />

                      <p className="mt-4 max-w-2xl text-base leading-relaxed text-white/70">
                        {activeProject.description}
                      </p>

                      {/* =====================================================
                          PRODUCT OWNER
                         ===================================================== */}

                      {currentUser?.role === "PRODUCT_OWNER" ? (
                        analysisStatus === "waiting" ? (
                          // -----------------------------------------------
                          // Waiting for client
                          // -----------------------------------------------

                          <div
                            className="
                              mt-4
                              flex
                              w-fit
                              items-center
                              gap-3
                              rounded-full
                              border border-cyan-400/30
                              bg-cyan-400/10
                              px-5
                              py-3.5
                              text-sm
                              font-medium
                              uppercase
                              tracking-[2px]
                              text-cyan-300
                            "
                          >
                            <div
                              className="h-4
                                w-4
                                animate-spin
                                rounded-full
                                border-2
                                border-cyan-300/20
                                border-t-cyan-300
                              "
                            />
                            Submitted for Review
                          </div>
                        ) : analysisStatus === "completed" ? (
                          // -----------------------------------------------
                          // Final requirements ready
                          // -----------------------------------------------

                          <button
                            type="button"
                            onClick={async () => {
                              try {
                                setFinalRequirementsLoading(true);

                                const response = await api.get(
                                  `/meetings/${threadId}/final-requirements`,
                                );

                                if (!response.data.ready) {
                                  console.log(
                                    "Final requirements are not ready yet.",
                                  );
                                  return;
                                }

                                setFinalRequirements((prev) => ({
                                  ...prev,
                                  [projectId]: response.data.final_requirements,
                                }));

                                setShowFinalRequirements(true);
                              } catch (error) {
                                console.error(
                                  "Failed to fetch final requirements:",
                                  error,
                                );
                              } finally {
                                setFinalRequirementsLoading(false);
                              }
                            }}
                            className="
                              mt-4
                              flex
                              w-fit
                              items-center
                              gap-3
                              rounded-full
                              border border-cyan-400/60
                              bg-black
                              px-5
                              py-3.5
                              text-sm
                              font-medium
                              uppercase
                              tracking-[2px]
                              text-cyan-300
                              transition-all
                              duration-300
                              hover:border-cyan-200
                              hover:text-white
                              hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]
                            "
                          >
                            View Final Requirements
                          </button>
                        ) : (
                          // -----------------------------------------------
                          // No analysis
                          // -----------------------------------------------

                          <button
                            onClick={() => setShowSelectMode(true)}
                            type="button"
                            className="
                              flex
                              mt-4
                              items-center
                              gap-3
                              cursor-pointer
                              relative
                              px-5
                              py-3.5
                              text-sm
                              font-medium
                              uppercase
                              tracking-[2px]
                              text-white
                              rounded-full
                              border border-cyan-400/60
                              bg-black
                              backdrop-blur-md
                              overflow-hidden
                              transition-all
                              duration-300
                              hover:border-cyan-200
                              w-fit
                              hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]
                            "
                          >
                            <Rocket size={17} />
                            Start Analysis
                          </button>
                        )
                      ) : currentUser?.role === "CLIENT" ? (
                        // =================================================
                        // CLIENT
                        // =================================================

                        activeProject.thread_id ? (
                          <div className="mt-5 space-y-3">
                            {/* Notification */}

                            <div
                              className="
                                flex
                                items-center
                                gap-3
                                rounded-xl
                                border border-cyan-400/30
                                bg-cyan-400/10
                                px-4
                                py-3
                                text-sm
                              "
                            >
                              <div>
                                <p className="font-semibold text-cyan-300">
                                  Requirements Ready for Review
                                </p>

                                <p className="text-white/60">
                                  The requirements are waiting for your review.
                                </p>
                              </div>
                            </div>

                            {/* Review button */}

                            <button
                              type="button"
                              onClick={() => {
                                navigate(
                                  `/client/review/${activeProject.thread_id}`,
                                );
                              }}
                              className="
                                flex
                                w-fit
                                items-center
                                gap-3
                                rounded-full
                                border border-cyan-400/60
                                bg-black
                                px-5
                                py-3.5
                                text-sm
                                font-medium
                                uppercase
                                tracking-[2px]
                                text-cyan-300
                                transition-all
                                duration-300
                                hover:border-cyan-200
                                hover:text-white
                                hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]
                              "
                            >
                              Review Requirements
                            </button>
                          </div>
                        ) : null
                      ) : null}
                    </div>
                  </div>

                  {/* Requirements image */}

                  <div className="absolute inset-y-0 right-0 flex w-[45%] items-end justify-end">
                    <img
                      src={requirmentsCard}
                      alt="Requirements analysis"
                      className="
                        h-full
                        w-full
                        object-contain
                        object-right-bottom
                        opacity-75
                      "
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
              // Later
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
          onSubmit={(data) => {
            console.log("Upload response:", data);

            const newThreadId = data.thread_id;

            setProjects((prev) =>
              prev.map((project) =>
                project.id === projectId
                  ? {
                      ...project,
                      thread_id: newThreadId,
                      analysis_status: "waiting",
                    }
                  : project,
              ),
            );

            setFinalRequirements((prev) => {
              const next = {
                ...prev,
              };

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
            setProjects((prev) => [...prev, data.project]);

            dispatch(updateUser(data.product_owner));

            setShowCreateProject(false);

            navigate(`/project-dashboard/${data.project.id}`);
          }}
        />
      )}

      {/* ============================================================
          FINAL REQUIREMENTS MODAL
         ============================================================ */}

      {showFinalRequirements && (
        <div
          className="
            fixed
            inset-0
            z-50
            flex
            items-center
            justify-center
            bg-black/70
            backdrop-blur-sm
          "
        >
          <div
            className="
              relative
              flex
              max-h-[85vh]
              w-[850px]
              flex-col
              overflow-hidden
              rounded-3xl
              border border-cyan-400/20
              bg-[#080A14]
              shadow-[0_0_60px_rgba(34,211,238,0.15)]
            "
          >
            {/* Modal header */}

            <div
              className="
                flex
                shrink-0
                items-center
                justify-between
                border-b
                border-white/10
                px-8
                py-6
              "
            >
              <div>
                <p
                  className="
                    text-xs
                    uppercase
                    tracking-[3px]
                    text-cyan-300
                  "
                >
                  Analysis Complete
                </p>

                <h2
                  style={{
                    fontFamily: "Orbitron, sans-serif",
                  }}
                  className="
                    mt-2
                    text-3xl
                    font-semibold
                    text-white
                  "
                >
                  Final Requirements
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setShowFinalRequirements(false)}
                className="
                  rounded-full
                  p-2
                  text-gray-500
                  transition
                  hover:bg-white/5
                  hover:text-white
                "
              >
                ✕
              </button>
            </div>

            {/* Modal content */}

            <div
              className="
                flex-1
                overflow-y-auto
                px-8
                py-6
              "
            >
              {projectFinalRequirements?.sections?.map((section) => (
                <div key={section.title} className="mb-8 last:mb-0">
                  <h3
                    style={{
                      fontFamily: "Orbitron, sans-serif",
                    }}
                    className="
                        mb-4
                        text-xl
                        font-semibold
                        text-cyan-300
                      "
                  >
                    {section.title}
                  </h3>

                  <div className="space-y-4">
                    {section.items?.map((item, index) => (
                      <div
                        key={item.id ?? index}
                        className="
                              rounded-2xl
                              border border-white/10
                              bg-white/[0.03]
                              px-5
                              py-4
                            "
                      >
                        <div
                          className="
                                mb-2
                                flex
                                items-center
                                gap-3
                              "
                        >
                          <span
                            className="
                                  rounded-full
                                  border border-cyan-400/30
                                  bg-cyan-400/10
                                  px-3
                                  py-1
                                  text-xs
                                  font-medium
                                  text-cyan-300
                                "
                          >
                            {item.id}
                          </span>
                        </div>

                        <p
                          className="
                                text-sm
                                leading-relaxed
                                text-white/80
                              "
                        >
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
    </div>
  );
}
