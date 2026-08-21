import React, { useState } from "react";
import { Rocket, Search, X } from "lucide-react";
import beehiveBg from "../../../Images/beehive-bg.png";
import useClientSearch from "../../../hooks/useClientSearch";
import { useSelector } from "react-redux";
import api from "../../../api/api";
import { useDispatch } from "react-redux";
import { setCurrentProject } from "../../../Redux/ProjectSlice";

export default function CreateProjectModal({ onClose, onCreated }) {
  const currentUser = useSelector((state) => state.user.userInfo);

  const dispatch = useDispatch();

  const [clientSearch, setClientSearch] = useState("");
  const [selectedClient, setSelectedClient] = useState(null);

  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const {
    searchClients,
    results: clientResults,
    loading: searchingClients,
  } = useClientSearch();

  const createProject = async () => {
    if (!projectName.trim()) {
      alert("Please enter a project name.");
      return;
    }

    if (!selectedClient) {
      alert("Please select a client.");
      return;
    }

    try {
      setCreating(true);

      const response = await api.post("/projects", {
        projectName,
        projectDescription,
        clientId: selectedClient.id,
        creatorId: currentUser.id,
      });

      const createdProject = response.data;

      console.log("Created project:", createdProject);

      console.log("Dispatched current project:", createdProject.project);

      dispatch(setCurrentProject(createdProject.project));
      onCreated(createdProject);
    } catch (error) {
      console.error("Project creation failed:", error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-6 backdrop-blur-sm">
      {/* Modal */}
      <div
        className="
          relative
      w-[760px]
      h-[680px]
      overflow-hidden
      rounded-3xl
      border border-cyan-400/20
      bg-gradient-to-br
      from-cyan-800/80
      via-cyan-950/90
      to-black
      p-8
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
            w-[350px]
            rotate-180
            opacity-20
          "
        />

        {/* Header */}
        <div className="relative z-10 mb-8 flex items-center justify-between">
          <div>
            <h2
              className="text-4xl font-bold text-white"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              New <span className="text-cyan-300">Project</span>
            </h2>

            <p className="mt-2 text-sm text-white/50">
              Set up a new requirements engineering project.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="
              rounded-full
              p-2
              text-gray-400
              transition
              hover:bg-white/10
              hover:text-white
            "
          >
            <X size={22} />
          </button>
        </div>

        {/* Form */}
        <div className="relative z-10">
          {/* Project Name */}
          <div className="mb-7">
            <label className="mb-3 block text-md font-medium text-gray-300">
              Project Name
            </label>

            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g. Smart Campus Management System"
              className="
                w-full
                rounded-xl
                border border-cyan-400/20
                bg-[#07151B]
                px-5
                py-4
                text-white
                outline-none
                transition
                placeholder:text-gray-600
                focus:border-cyan-400/70
                focus:ring-1
                focus:ring-cyan-400/30
              "
            />
          </div>

          {/* Client */}
          <div className="mb-7">
            <label className="mb-3 block text-md font-medium text-gray-300">
              Add Client
            </label>

            {!selectedClient ? (
              <div className="relative">
                <Search
                  size={19}
                  className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-500"
                />

                <div className="absolute left-12 top-1/2 h-9 w-0.5 -translate-y-1/2 bg-cyan-400/30" />

                <input
                  type="text"
                  value={clientSearch}
                  onChange={(e) => {
                    const value = e.target.value;

                    setClientSearch(value);
                    searchClients(value);
                  }}
                  placeholder="Search client by name or email..."
                  className="
                    w-full
                    rounded-xl
                    border border-cyan-400/20
                    bg-[#07151B]
                    py-4
                    pl-14
                    pr-5
                    text-white
                    outline-none
                    transition
                    placeholder:text-gray-500
                    focus:border-cyan-400/70
                    focus:ring-1
                    focus:ring-cyan-400/30
                  "
                />

                {clientSearch.trim().length >= 2 && (
                  <div
                    className="
                      absolute
                      left-0
                      right-0
                      top-full
                      z-50
                      mt-2
                      overflow-hidden
                      rounded-xl
                      border border-cyan-400/20
                      bg-[#07151B]
                      shadow-2xl
                    "
                  >
                    {searchingClients && (
                      <div className="px-5 py-4 text-sm text-gray-500">
                        Searching...
                      </div>
                    )}

                    {!searchingClients && clientResults.length === 0 && (
                      <div className="px-5 py-4 text-sm text-gray-500">
                        No users found.
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
                          className="
                            flex
                            w-full
                            flex-col
                            items-start
                            px-5
                            py-4
                            text-left
                            transition
                            hover:bg-cyan-400/10
                          "
                        >
                          <span className="font-medium text-white">
                            {client.name}
                          </span>

                          <span className="mt-1 text-sm text-gray-500">
                            {client.email}
                          </span>
                        </button>
                      ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-between rounded-xl border border-cyan-400/20 bg-[#07151B] px-5 py-4">
                <div>
                  <p className="font-medium text-white">
                    {selectedClient.name}
                  </p>

                  <p className="mt-1 text-sm text-gray-500">
                    {selectedClient.email}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedClient(null)}
                  className="
                    rounded-full
                    p-1
                    text-gray-400
                    transition
                    hover:bg-cyan-400/10
                    hover:text-cyan-300
                  "
                >
                  <X size={20} />
                </button>
              </div>
            )}
          </div>

          {/* Description */}
          <div className="mb-8">
            <label className="mb-3 block text-md font-medium text-gray-300">
              Project Description
            </label>

            <textarea
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              rows={5}
              placeholder="Briefly describe what you want to build..."
              className="
                w-full
                resize-none
                rounded-xl
                border border-cyan-400/20
                bg-[#07151B]
                px-5
                py-4
                text-white
                outline-none
                transition
                placeholder:text-gray-600
                focus:border-cyan-400/70
                focus:ring-1
                focus:ring-cyan-400/30
              "
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="
                rounded-full
                border border-white/10
                px-5
                py-3.5
                text-sm
                font-medium
                uppercase
                tracking-[2px]
                text-white/60
                transition
                hover:border-white/20
                hover:text-white
              "
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={createProject}
              disabled={creating}
              className="
                flex
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
                text-white
                transition-all
                duration-300
                hover:border-cyan-200
                hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              <Rocket size={17} />

              {creating ? "Creating..." : "Create Project"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
