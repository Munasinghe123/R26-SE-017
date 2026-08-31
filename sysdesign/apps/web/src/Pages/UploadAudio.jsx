import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import audio from "../Images/audio.png";

function UploadAudio() {
  const navigate = useNavigate();
  const location = useLocation();
  const projectId = location.state?.projectId || new URLSearchParams(location.search).get("projectId");

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [dragging, setDragging] = useState(false);

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setStatusText("Analyzing file and extracting IEEE 29148 Software Requirements...");

    const formData = new FormData();
    formData.append("file", file);
    if (projectId) {
      formData.append("projectId", projectId);
    }

    try {
      const res = await axios.post(
        "/extract-requirements",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );

      const data = res.data;
      if (data?.meeting_id) {
        localStorage.setItem("lastMeetingId", data.meeting_id);
        localStorage.setItem("lastMeetingTime", new Date().toISOString());
        if (projectId) {
          localStorage.setItem(`project_${projectId}_meetingId`, data.meeting_id);
        }
        setStatusText("Extraction Complete! Redirecting to Requirements Review...");
        setTimeout(() => {
          navigate(`/requirements-review/${data.meeting_id}`);
        }, 500);
      }
    } catch (err) {
      console.error(err);
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || "Extraction failed. Please check backend connection.";
      setStatusText(errorMsg);
    } finally {
      setLoading(false);
    }
  };


  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);

    if (e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="relative h-screen w-full ">
      <div className="relative min-h-full w-full grid lg:grid-cols-2 grid-cols-1 xl:px-30 pb-5 pt-20">
        <div className="flex items-start justify-center w-full h-full flex-col space-y-10">
          <h1
            className="text-white text-6xl uppercase font-bold"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Turn <span className="text-cyan-300">Audio</span> And{" "}
            <span className="text-cyan-300">Documents</span> into intelligent{" "}
            <span className="text-cyan-300"> results</span>
          </h1>
          <div className="w-full max-w-md bg-gray-800/60 backdrop-blur-md border border-cyan-900 rounded-2xl p-8 shadow-xl">
            <label
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center
        w-full h-40
        border-2 border-dashed rounded-xl cursor-pointer
        transition

        ${
          dragging
            ? "border-cyan-400 bg-cyan-500/10"
            : "border-gray-600 hover:border-cyan-700"
        }
    `}
            >
              <input
                type="file"
                className="hidden"
                onChange={(e) => setFile(e.target.files[0])}
              />

              <p className="text-gray-400">
                {file ? file.name : "Click or drag audio and document files here"}
              </p>
            </label>

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className={`w-full mt-6 py-3.5 rounded-xl font-bold uppercase tracking-wider text-xs transition flex items-center justify-center gap-2
                        ${
                          !file || loading
                            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                            : "bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_20px_rgba(34,211,238,0.4)] cursor-pointer"
                        }`}
            >
              {loading ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  Extracting Requirements...
                </>
              ) : (
                "Upload & Extract Requirements"
              )}
            </button>

            {statusText && (
              <div className={`mt-5 p-4 rounded-xl text-xs font-semibold text-center border ${
                statusText.toLowerCase().includes("rejected") || statusText.toLowerCase().includes("failed") || statusText.toLowerCase().includes("non-technical")
                  ? "bg-red-950/40 border-red-500/40 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.2)]"
                  : "bg-cyan-950/40 border-cyan-400/30 text-cyan-300 animate-pulse"
              }`}>
                {statusText}
              </div>
            )}

          </div>
        </div>

        <div className="overflow-hidden h-[85%] opacity-90 absolute bottom-0 right-20">
          <img src={audio} className="w-full h-full object-contain" />
        </div>
      </div>
    </div>
  );
}

export default UploadAudio;
