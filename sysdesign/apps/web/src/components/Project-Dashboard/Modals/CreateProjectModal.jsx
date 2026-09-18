import React, { useState, useEffect } from "react";
import { Rocket, Search, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import beehiveBg from "../../../Images/beehive-bg.png";
import useClientSearch from "../../../hooks/useClientSearch";
import axios from "axios";
import { useSelector, useDispatch } from "react-redux";
import { updateUser } from "../../../Redux/UserSlice";

export default function CreateProjectModal({ isOpen = true, onClose, onCreated }) {
  const currentUser = useSelector((state) => state.user.userInfo);
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [clientSearch, setClientSearch] = useState("");
  const [selectedClient, setSelectedClient] = useState(null);

  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const {
    searchClients,
    results: clientResults,
    loading: searchingClients,
  } = useClientSearch();

  // Close on Escape key press
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === "Escape" && onClose && !submitting) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, submitting]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCreate = async () => {
    if (!projectName.trim()) {
      alert("Please enter a project name.");
      return;
    }

    if (!selectedClient) {
      alert("Please select a client.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await axios.post("/projects", {
        projectName,
        projectDescription,
        clientId: selectedClient.id,
        creatorId: currentUser?.id,
      });

      const newProject = response.data.project || {
        id: response.data.id,
        name: projectName,
        description: projectDescription,
        clientId: selectedClient.id,
      };

      const updatedOwner = {
        role: "PRODUCT_OWNER",
      };

      dispatch(updateUser(updatedOwner));

      if (onCreated) {
        onCreated({
          project: newProject,
          product_owner: updatedOwner,
          message: response.data.message,
        });
      } else {
        alert(response.data.message || "Project created successfully!");
        if (onClose) onClose();
        navigate(`/project-dashboard/${newProject.id}`);
      }
    } catch (error) {
      console.error("Project creation failed:", error);
      alert(error.response?.data?.message || "Project creation failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 md:p-6 overflow-hidden animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose && !submitting) {
          onClose();
        }
      }}
    >
      <div
        className="
          relative
          w-full
          max-w-2xl
          max-h-[90vh]
          flex
          flex-col
          overflow-hidden
          rounded-3xl
          border border-cyan-400/30
          bg-gradient-to-br
          from-cyan-950/95
          via-[#07151B]/95
          to-black
          shadow-[0_0_50px_rgba(34,211,238,0.25)]
          my-auto
          text-white
        "
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative beehive backgrounds */}
        <img
          src={beehiveBg}
          alt=""
          className="pointer-events-none absolute -left-24 -top-24 w-[280px] opacity-20 z-0 select-none"
        />

        <img
          src={beehiveBg}
          alt=""
          className="pointer-events-none absolute -bottom-28 -right-24 w-[300px] rotate-180 opacity-20 z-0 select-none"
        />

        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-cyan-400/20 px-6 md:px-8 py-5 relative z-10 shrink-0 bg-[#07151B]/40 backdrop-blur-sm">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-2">
              <Rocket size={13} />
              Workspace Setup
            </div>
            <h2
              className="text-2xl md:text-3xl font-bold uppercase tracking-wide text-white"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              New <span className="text-cyan-300">Project</span>
            </h2>
            <p className="text-xs md:text-sm text-gray-400 mt-1">
              Initialize a project workspace, link client details, and start requirements engineering.
            </p>
          </div>

          {onClose && (
            <button
              type="button"
              disabled={submitting}
              onClick={onClose}
              className="p-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white transition cursor-pointer disabled:opacity-50"
              aria-label="Close modal"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden px-6 md:px-8 py-6 relative z-10 custom-scrollbar space-y-6">
          {/* Project Name */}
          <div>
            <label className="mb-2.5 block text-sm font-medium text-gray-300">
              Project Name <span className="text-cyan-400">*</span>
            </label>

            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g. Smart Campus Management System"
              className="w-full rounded-xl bg-[#07151B] px-5 py-3.5 text-white outline-none transition placeholder:text-gray-600 border border-cyan-400/20 focus:border-cyan-400/70 focus:ring-1 focus:ring-cyan-400 text-sm md:text-base"
            />
          </div>

          {/* Add Client */}
          <div>
            <label className="mb-2.5 block text-sm font-medium text-gray-300">
              Add Client <span className="text-cyan-400">*</span>
            </label>

            {!selectedClient ? (
              <div className="relative">
                <Search
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
                />

                <div className="absolute left-11 top-1/2 h-7 w-0.5 -translate-y-1/2 bg-cyan-400/30" />

                <input
                  type="text"
                  value={clientSearch}
                  onChange={(e) => {
                    const value = e.target.value;
                    setClientSearch(value);
                    searchClients(value);
                  }}
                  placeholder="Search client by name or email..."
                  className="w-full rounded-xl border border-cyan-400/20 bg-[#07151B] py-3.5 pl-14 pr-5 text-white outline-none transition placeholder:text-gray-500 focus:border-cyan-400/70 focus:ring-1 focus:ring-cyan-400/30 text-sm md:text-base"
                />

                {clientSearch.trim().length >= 2 && (
                  <div className="absolute left-0 right-0 top-full z-50 mt-2 max-h-52 overflow-y-auto overflow-x-hidden rounded-xl border border-cyan-400/30 bg-[#07151B] shadow-2xl custom-scrollbar">
                    {searchingClients && (
                      <div className="px-5 py-3 text-sm text-gray-500">
                        Searching clients...
                      </div>
                    )}

                    {!searchingClients && clientResults.length === 0 && (
                      <div className="px-5 py-3 text-sm text-gray-500">
                        No clients found.
                      </div>
                    )}

                    {!searchingClients &&
                      clientResults.map((client) => (
                        <button
                          key={client.id}
                          type="button"
                          onClick={() => {
                            setSelectedClient(client);
                            setClientSearch("");
                          }}
                          className="flex w-full flex-col items-start px-5 py-3 text-left transition hover:bg-cyan-400/10 border-b border-white/5 last:border-0"
                        >
                          <span className="font-medium text-white text-sm">
                            {client.name}
                          </span>

                          <span className="mt-0.5 text-xs text-gray-400">
                            {client.email}
                          </span>
                        </button>
                      ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-between rounded-xl border border-cyan-400/30 bg-[#07151B] px-5 py-3.5">
                <div>
                  <p className="font-medium text-white text-sm md:text-base">
                    {selectedClient.name}
                  </p>

                  <p className="mt-0.5 text-xs md:text-sm text-cyan-300/80">
                    {selectedClient.email}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedClient(null)}
                  className="rounded-full p-1.5 text-gray-400 transition hover:bg-cyan-400/10 hover:text-cyan-300 cursor-pointer"
                  aria-label="Remove selected client"
                >
                  <X size={18} />
                </button>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="mb-2.5 block text-sm font-medium text-gray-300">
              Project Description
            </label>

            <textarea
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              rows={4}
              placeholder="Briefly describe what you want to build..."
              className="w-full resize-none rounded-xl border border-cyan-400/20 bg-[#07151B] px-5 py-3.5 text-white outline-none transition placeholder:text-gray-600 focus:border-cyan-400/70 focus:ring-1 focus:ring-cyan-400 text-sm md:text-base custom-scrollbar"
            />
          </div>
        </div>

        {/* Actions Footer */}
        <div className="flex items-center justify-end gap-3 px-6 md:px-8 py-4 border-t border-cyan-400/15 relative z-10 shrink-0 bg-[#07151B]/60 backdrop-blur-sm">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-5 py-2.5 rounded-full border border-white/10 text-xs font-semibold uppercase tracking-wider text-gray-300 hover:text-white hover:bg-white/5 transition cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>
          )}

          <button
            type="button"
            onClick={handleCreate}
            disabled={submitting}
            className="flex items-center gap-2 rounded-full border border-cyan-400/60 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 px-6 py-2.5 text-xs font-bold uppercase tracking-wider text-white shadow-[0_0_20px_rgba(34,211,238,0.4)] transition duration-300 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Rocket size={15} />
            )}
            {submitting ? "Creating..." : "Create Project"}
          </button>
        </div>
      </div>
    </div>
  );
}
