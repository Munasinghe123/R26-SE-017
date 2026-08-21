import React from "react";
import { Plus, User, Settings,LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { logout } from "../../Redux/UserSlice";
import logo from "../../Images/logo.png";
import CreateProjectModal from "./Modals/CreateProjectModal";
import { useState } from "react";

export default function ProjectSidebar({
  projects,
  activeProjectId,
  userRole,
  onCreateProject,
}) {
  const [showAccountMenu, setShowAccountMenu] = useState(false);

  const navigate = useNavigate();

  const handleProjectClick = (projectId) => {
    navigate(`/project-dashboard/${projectId}`);
  };

  const dispatch = useDispatch();

  const handleLogout = () => {
    dispatch(logout());
    navigate("/get-started");
  };

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-r border-white/10 bg-[#0B0D17]">
      {/* Logo */}
      <div className="flex h-20 shrink-0 items-center border-b border-white/10 px-6">
        <img src={logo} alt="SysDesign" className="h-12 object-contain" />
      </div>

      {/* Projects */}
      <div className="flex-1 overflow-y-auto px-3 py-7">
        <p className="px-3 text-xs font-medium uppercase tracking-wider text-gray-500">
          Projects
        </p>

        <div className="mt-4 space-y-1">
          {projects.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-gray-600">
              No projects available
            </p>
          ) : (
            projects.map((project) => {
              const isActive = project.id === activeProjectId;

              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => handleProjectClick(project.id)}
                  className={`
                    w-full rounded-lg px-3 py-3
                    text-left text-sm
                    transition-colors
                    ${
                      isActive
                        ? "bg-cyan-400/10 text-cyan-300"
                        : "text-gray-400 hover:bg-white/5 hover:text-white"
                    }
                  `}
                >
                  {project.name}
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="shrink-0 border-t border-white/10 p-3">
        {userRole === "PRODUCT_OWNER" && (
          <button
            type="button"
            onClick={onCreateProject}
            className="
            mb-2 flex w-fit items-center gap-3
            rounded-lg px-3 py-3
            text-sm font-medium
            text-black
            bg-gradient-to-r from-cyan-100 via-cyan-300 to-cyan-500
            transition
            hover:brightness-110
          "
          >
            <Plus size={18} />
            New Project
          </button>
        )}

        <div className="relative">
          <button
            type="button"
            onClick={() => setShowAccountMenu((prev) => !prev)}
            className="
      flex w-fit items-center gap-3
      rounded-lg px-3 py-3
      text-sm text-gray-400
      transition
      hover:bg-white/5
      hover:text-white
    "
          >
            <User size={18} />
            Account
          </button>

          {showAccountMenu && (
            <div
              className="
        absolute bottom-full left-0 mb-2
        w-40
        rounded-xl
        border border-white/10
        bg-[#111421]
        p-1
        shadow-xl
      "
            >
              <button
                type="button"
                onClick={handleLogout}
                className="
          flex w-full items-center gap-3
          rounded-lg px-3 py-2.5
          text-sm text-gray-400
          transition
          hover:bg-white/5
          hover:text-white
        "
              >
                <LogOut size={17} />
                Logout
              </button>
            </div>
          )}
        </div>

        <button
          type="button"
          className="
            flex w-fit items-center gap-3
            rounded-lg px-3 py-3
            text-sm text-gray-400
            transition
            hover:bg-white/5
            hover:text-white
          "
        >
          <Settings size={18} />
          Settings
        </button>
      </div>
    </aside>
  );
}
