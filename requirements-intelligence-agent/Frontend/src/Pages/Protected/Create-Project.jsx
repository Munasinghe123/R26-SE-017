import React from "react";
import { ArrowLeft, Rocket, Search, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import beehiveBg from "../../Images/beehive-bg.png";
import { useState } from "react";
import useClientSearch from "../../hooks/useClientSearch";
import axios from "axios";
import { useSelector } from "react-redux";

export default function CreateProject() {
  const currentUser = useSelector((state) => state.user.userInfo);
  console.log("user from the slice", currentUser);

  const navigate = useNavigate();

  const [clientSearch, setClientSearch] = useState("");
  const [selectedClient, setSelectedClient] = useState(null);

  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");

  const {
    searchClients,
    results: clientResults,
    loading: searchingClients,
  } = useClientSearch();

  const createProject = async () => {
    if (!selectedClient) {
      alert("Please select a client.");
      return;
    }
    console.log("user from the slice", currentUser);
    try {
      const response = await axios.post("http://127.0.0.1:8000/projects", {
        projectName,
        projectDescription,
        clientId: selectedClient.id,
        creatorId: currentUser.id,
      });

      alert(response.data.message);
      navigate("/project-dashboard");
    } catch (error) {
      console.error("Project creation failed:", error);
    }
  };

  return (
    <div className="min-h-screen w-full px-6 pb-20 pt-24 text-white">
      <div className="mx-auto w-full max-w-4xl">
        {/* Heading */}
        <div className="mb-10">
          <h2
            className="mt-4 text-7xl font-bold text-center text-white mb-10"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            New <span className="text-cyan-300">Project </span>
          </h2>
        </div>

        {/* Form Card */}
        <div
          className="
          relative
          w-full
          max-w-5xl
          h-full
          overflow-hidden
          rounded-3xl
          border border-cyan-400/20
          bg-gradient-to-br
          from-cyan-800/80
          via-cyan-950/80
          to-black
          shadow-[0_0_50px_rgba(34,211,238,0.25)]
          p-8
        "
        >
          <img
            src={beehiveBg}
            alt=""
            className="z-0
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
            className="z-0
                        pointer-events-none
                        absolute
                        -bottom-28
                        -right-24
                        w-[350px]
                        rotate-180
                        opacity-20
                      "
          />
          {/* Project Name */}
          <div className="relative z-10">
            <div className="mb-7">
              <label className="mb-3 block text-md font-medium text-gray-300">
                Project Name
              </label>

              <input
                type="text"
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. Smart Campus Management System"
                className="w-full  rounded-xl bg-[#07151B] px-5 py-4 text-white outline-none transition placeholder:text-gray-600 border border-cyan-400/20  focus:ring-1 focus:ring-cyan-400"
              />
            </div>

            <div className="mb-7">
              <label className="mb-3 block text-md font-medium text-gray-300">
                Add Client
              </label>

              {!selectedClient ? (
                // SEARCH INPUT
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
          w-full rounded-xl border border-cyan-400/20
          bg-[#07151B] py-4 pl-14 pr-5 text-white outline-none
          transition placeholder:text-gray-500
          focus:border-cyan-400/70 focus:ring-1 focus:ring-cyan-400/30
        "
                  />

                  {clientSearch.trim().length >= 2 && (
                    <div className="absolute left-0 right-0 top-full z-50 mt-2 overflow-hidden rounded-xl border border-cyan-400/20 bg-[#07151B] shadow-2xl">
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
                            className="flex w-full flex-col items-start px-5 py-4 text-left transition hover:bg-cyan-400/10"
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
                // SELECTED CLIENT
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
                    className="rounded-full p-1 text-gray-400 transition hover:bg-cyan-400/10 hover:text-cyan-300"
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
                onChange={(e) => setProjectDescription(e.target.value)}
                rows={6}
                placeholder="Briefly describe what you want to build..."
                className="w-full resize-none rounded-xl border border-cyan-400/20 bg-[#07151B] px-5 py-4 text-white outline-none transition placeholder:text-gray-600 focus:ring-1 focus:ring-cyan-400"
              />
            </div>

            {/* CTA */}
            <div className="flex justify-start">
              <button
                onClick={() => createProject()}
                className="flex items-center gap-3 cursor-pointer
                    inset-0 bg-gradient-to-r from-cyan-400/0 via-cyan-400/30 to-purple-500/0
                    relative px-5 py-3.5 
                    text-sm font-medium uppercase tracking-[2px]
                    text-white rounded-full
                    border border-cyan-400/60
                    bg-black backdrop-blur-md
                    overflow-hidden
                    transition-all duration-300
                    hover:border-cyan-200
                    hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"
              >
                <Rocket size={17} />
                Create Project
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
