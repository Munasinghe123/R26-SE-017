import React, { useState } from "react";
import {
  Plus,
  User,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  FolderGit2,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { logout } from "../../Redux/UserSlice";
import logo from "../../Images/logo.png";
import { setCurrentProject } from "../../Redux/ProjectSlice";

export default function ProjectSidebar({
  projects = [],
  activeProjectId,
  userRole,
  onCreateProject,
  isCollapsed: controlledCollapsed,
  onToggleCollapse,
}) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);

  const navigate = useNavigate();
  const dispatch = useDispatch();

  const isCollapsed =
    controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  const toggleCollapse = () => {
    if (onToggleCollapse) {
      onToggleCollapse();
    } else {
      setInternalCollapsed((prev) => !prev);
    }
  };

  const handleProjectClick = (project) => {
    dispatch(setCurrentProject(project));
    navigate(`/project-dashboard/${project.id}`);
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate("/get-started");
  };

  const projectList = Array.isArray(projects) ? projects : [];

  console.log("ProjectSidebar - projects:", projectList);

  return (
    <aside
      className={`relative flex h-full shrink-0 flex-col border-r border-white/10 bg-[#0B0D17] transition-all duration-300 ease-in-out ${
        isCollapsed ? "w-20" : "w-80"
      }`}
    >
      {/* Header with Logo and Collapse Toggle */}
      <div className="flex h-20 shrink-0 items-center justify-between border-b border-white/10 px-4">
        {!isCollapsed && (
          <div
            onClick={() => navigate("/project-dashboard")}
            className="flex items-center gap-2 cursor-pointer overflow-hidden"
          >
            <img src={logo} alt="SysDesign" className="h-10 object-contain" />
          </div>
        )}

        <button
          type="button"
          onClick={toggleCollapse}
          className={`rounded-lg p-2 text-gray-400 transition hover:bg-white/5 hover:text-white cursor-pointer ${
            isCollapsed ? "mx-auto" : ""
          }`}
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          aria-label={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? (
            <PanelLeftOpen size={20} />
          ) : (
            <PanelLeftClose size={20} />
          )}
        </button>
      </div>

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto px-3 py-6 custom-scrollbar overflow-x-hidden">
        {!isCollapsed && (
          <div className="flex items-center justify-between px-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Projects
            </p>
          </div>
        )}

        <div className="mt-4 space-y-1.5">
          {projectList.length === 0 ? (
            <p
              className={`text-gray-600 text-sm ${
                isCollapsed
                  ? "text-center text-xs px-1"
                  : "px-3 py-6 text-center"
              }`}
            >
              {isCollapsed ? "Empty" : "No projects available"}
            </p>
          ) : (
            projectList.map((project) => {
              const isActive = project.id === activeProjectId;
              const initials = (project.name || "P")
                .split(" ")
                .map((w) => w[0])
                .slice(0, 2)
                .join("")
                .toUpperCase();

              if (isCollapsed) {
                return (
                  <button
                    key={project.id}
                    type="button"
                    onClick={() => handleProjectClick(project)}
                    title={project.name}
                    className={`
                      group relative mx-auto flex h-11 w-11 items-center justify-center rounded-xl text-xs font-bold transition-all cursor-pointer
                      ${
                        isActive
                          ? "bg-cyan-400/20 text-cyan-300 border border-cyan-400/60 shadow-[0_0_15px_rgba(34,211,238,0.3)]"
                          : "text-gray-400 hover:bg-white/5 hover:text-white border border-transparent"
                      }
                    `}
                  >
                    {initials}
                    {/* Tooltip on hover */}
                    <span className="pointer-events-none absolute left-full ml-3 z-50 hidden rounded-md bg-[#111421] px-2.5 py-1.5 text-xs font-medium text-white shadow-xl border border-white/10 group-hover:block whitespace-nowrap">
                      {project.name}
                    </span>
                  </button>
                );
              }

              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => handleProjectClick(project)}
                  className={`
                    w-full rounded-xl px-3.5 py-3
                    text-left text-sm font-medium
                    transition-all cursor-pointer
                    flex items-center gap-2.5
                    ${
                      isActive
                        ? "bg-cyan-400/10 text-cyan-300 border-l-2 border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.1)]"
                        : "text-gray-400 hover:bg-white/5 hover:text-white"
                    }
                  `}
                >
                  <FolderGit2
                    size={16}
                    className={
                      isActive
                        ? "text-cyan-400 shrink-0"
                        : "text-gray-500 shrink-0"
                    }
                  />
                  <span className="truncate">{project.name}</span>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="shrink-0 border-t border-white/10 p-3 space-y-1">
        <div className="w-fit">
          {userRole === "PRODUCT_OWNER" && (
            <button
              type="button"
              onClick={onCreateProject}
              title="New Project"
              className={`
              mb-2 flex items-center gap-3
              rounded-xl font-medium
              text-black
              bg-gradient-to-r from-cyan-100 via-cyan-300 to-cyan-500
              transition-all
              hover:brightness-110 cursor-pointer shadow-md
              ${isCollapsed ? "mx-auto h-10 w-10 justify-center p-0" : "w-full px-3.5 py-2.5 text-sm"}
            `}
            >
              <Plus size={18} className="shrink-0" />
              {!isCollapsed && <span>New Project</span>}
            </button>
          )}

          {/* Account Menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowAccountMenu((prev) => !prev)}
              title="Account"
              className={`
              flex items-center gap-3
              rounded-xl text-gray-400
              transition
              hover:bg-white/5
              hover:text-white cursor-pointer
              ${isCollapsed ? "mx-auto h-10 w-10 justify-center p-0" : "w-full px-3.5 py-2.5 text-sm"}
            `}
            >
              <User size={18} className="shrink-0" />
              {!isCollapsed && <span>Account</span>}
            </button>

            {showAccountMenu && (
              <div
                className={`
                absolute bottom-full mb-2
                w-44
                rounded-xl
                border border-white/10
                bg-[#111421]
                p-1.5
                shadow-2xl z-50 backdrop-blur-md
                ${isCollapsed ? "left-12" : "left-0"}
              `}
              >
                <button
                  type="button"
                  onClick={handleLogout}
                  className="
                  flex w-full items-center gap-3
                  rounded-lg px-3 py-2.5
                  text-sm text-gray-400
                  transition
                  hover:bg-red-500/10
                  hover:text-red-300 cursor-pointer
                "
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            )}
          </div>

          {/* Settings */}
          <button
            type="button"
            title="Settings"
            className={`
            flex items-center gap-3
            rounded-xl text-gray-400
            transition
            hover:bg-white/5
            hover:text-white cursor-pointer
            ${isCollapsed ? "mx-auto h-10 w-10 justify-center p-0" : "w-full px-3.5 py-2.5 text-sm"}
          `}
          >
            <Settings size={18} className="shrink-0" />
            {!isCollapsed && <span>Settings</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}
