import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate, useParams } from "react-router-dom";
import beehiveBg from "../../../Images/beehive-bg.png";
import { Link } from "react-router-dom";
import { Rocket } from "lucide-react";
import api from "../../../api/api";
import ProjectSidebar from "../../../components/Project-Dashboard/ProjectSidebar";
import requirmentsCard from "../../../Images/requirments-card.png";
import { useDispatch } from "react-redux";
import { updateUser } from "../../../Redux/UserSlice";

//modals
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

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  //modals
  const [showSelectMode, setShowSelectMode] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showCreateProject, setShowCreateProject] = useState(false);
  // const [showReviewRequirements, setShowReviewRequirements] = useState(false);

  useEffect(() => {
    const fetchProjects = async () => {
      if (!currentUser?.id) {
        setLoading(false);
        return;
      }

      try {
        const response = await api.get(`/projects/user/${currentUser.id}`);

        setProjects(response.data.projects);
        console.log(response.data.projects);
      } catch (error) {
        console.error("Failed to fetch projects:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [currentUser?.id]);

  const activeProject = projects.find((project) => project.id === projectId);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#080A14] text-gray-400">
        Loading projects...
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#080A14] text-white">
      {/* Sidebar */}
      <ProjectSidebar
        projects={projects}
        activeProjectId={projectId}
        userRole={currentUser?.role}
        onCreateProject={() => setShowCreateProject(true)}
      />

      {/* Middle Content */}
      <main className="min-w-0 flex-1 overflow-y-auto">
        {/* Content */}
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
              <h1
                className="text-white text-center text-5xl uppercase font-bold"
                style={{ fontFamily: "Orbitron, sans-serif" }}
              >
                Awaiting <span className="text-cyan-300">Analysis</span>
              </h1>
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
                        z-0
                        absolute
                        -bottom-28
                        -right-24
                        w-[350px]
                        rotate-180
                        opacity-20
                      "
                />

                {/* Main content */}
                <div className="relative z-10 h-full grid grid-cols-2 px-14 py-5 ">
                  <div className="flex h-full flex-col">
                    {/* Project label */}
                    <span
                      className="
                        inline-flex
                        w-fit
                        items-center
                        rounded-full
                        border border-cyan-400/30
                        bg-white/10
                        px-4 py-1.5
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

                    <div className="flex flex-1 flex-col justify-center py-6">
                      <h1
                        style={{ fontFamily: "Orbitron, sans-serif" }}
                        className="text-4xl font-semibold capitalize tracking-wide text-white"
                      >
                        {activeProject.name}
                      </h1>
                      <div className="mt-1 h-0.5 w-28 bg-cyan-400" />

                      <p className="mt-4 max-w-2xl text-base leading-relaxed text-white/70">
                        {activeProject.description}
                      </p>

                      {currentUser?.role === "PRODUCT_OWNER" ? (
                        <button
                          onClick={() => setShowSelectMode(true)}
                          type="button"
                          className="flex mt-4 items-center gap-3 cursor-pointer
    inset-0 bg-gradient-to-r from-cyan-400/0 via-cyan-400/30 to-purple-500/0
    relative px-5 py-3.5 
    text-sm font-medium uppercase tracking-[2px]
    text-white rounded-full
    border border-cyan-400/60
    bg-black backdrop-blur-md
    overflow-hidden
    transition-all duration-300
    hover:border-cyan-200 w-fit
    hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"
                        >
                          <Rocket size={17} />
                          Start Analysis
                        </button>
                      ) : currentUser?.role === "CLIENT" ? (
                        <button
                          type="button"
                          disabled
                          className="
                                    mt-4 flex w-fit items-center gap-3
                                    rounded-full
                                    border border-cyan-400/20
                                    bg-black/40
                                    px-5 py-3.5
                                    text-sm font-medium uppercase tracking-[2px]
                                    text-cyan-300/50
                                    cursor-not-allowed
                                    opacity-70
                                  "
                        >
                          Review Requirements
                        </button>
                      ) : null}
                    </div>
                  </div>

                  <div className="absolute inset-y-0 right-0 w-[45%] flex items-end justify-end">
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
      {/* select mode modal */}
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

      {/* upload modal */}
      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSubmit={(data) => {
            console.log("Upload response:", data);
          }}
        />
      )}

      {/* create project */}
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
    </div>
  );
}
