import React, { useState, useEffect } from "react";
import { X, UploadCloud, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import axios from "axios";

export default function UploadModal({ onClose, projectId, onSubmit }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && onClose && !loading) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, loading]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setStatusText("Analyzing file and extracting IEEE 29148 Software Requirements...");

    const formData = new FormData();
    formData.append("file", file);
    if (projectId) {
      formData.append("projectId", projectId);
    }

    try {
      const res = await axios.post("/extract-requirements", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const data = res.data;
      const threadId = data.thread_id || data.meeting_id;
      if (threadId) {
        localStorage.setItem("lastMeetingId", threadId);
        localStorage.setItem("lastMeetingTime", new Date().toISOString());
        if (projectId) {
          localStorage.setItem(`project_${projectId}_meetingId`, threadId);
        }
      }

      setStatusText("Extraction Complete!");
      if (onSubmit) {
        onSubmit({ ...data, thread_id: threadId });
      }
    } catch (err) {
      console.error("Extraction failed:", err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Extraction failed. Please check your file and backend connection.";
      setError(msg);
      setStatusText("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 md:p-6 overflow-hidden animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose && !loading) onClose();
      }}
    >
      <div
        className="relative w-full max-w-xl rounded-3xl border border-cyan-400/30 bg-gradient-to-br from-cyan-950/95 via-[#07151B]/95 to-black shadow-[0_0_50px_rgba(34,211,238,0.25)] p-6 md:p-8 my-auto text-white overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-cyan-400/20 pb-4 mb-6">
          <div>
            <h2
              className="text-2xl font-bold uppercase tracking-wide text-white"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              Upload <span className="text-cyan-300">File</span>
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Upload audio recordings or specifications for automated elicitation
            </p>
          </div>

          {onClose && (
            <button
              type="button"
              disabled={loading}
              onClick={onClose}
              className="p-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white transition cursor-pointer disabled:opacity-50"
              aria-label="Close modal"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`
            relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all
            ${
              dragging
                ? "border-cyan-400 bg-cyan-500/10"
                : file
                ? "border-cyan-400/60 bg-[#07151B]"
                : "border-white/15 bg-white/[0.02] hover:border-cyan-400/40 hover:bg-white/[0.04]"
            }
          `}
        >
          <input
            type="file"
            id="modal-file-upload"
            accept="audio/*,.pdf,.txt,.docx,.md"
            onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
            className="hidden"
          />

          <label
            htmlFor="modal-file-upload"
            className="flex flex-col items-center justify-center cursor-pointer w-full"
          >
            <div className="p-4 rounded-2xl bg-cyan-500/10 text-cyan-300 border border-cyan-400/30 mb-3">
              <UploadCloud size={32} />
            </div>

            {file ? (
              <div className="flex items-center gap-2 text-cyan-300 font-medium">
                <FileText size={18} />
                <span className="text-sm truncate max-w-xs">{file.name}</span>
                <span className="text-xs text-gray-400">
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
            ) : (
              <>
                <p className="text-sm font-semibold text-white">
                  Click to browse or drag and drop
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Audio (.mp3, .wav, .m4a) or Docs (.pdf, .txt, .docx)
                </p>
              </>
            )}
          </label>
        </div>

        {/* Status / Error Messages */}
        {statusText && (
          <div className="mt-4 flex items-center gap-2.5 text-xs text-cyan-300 bg-cyan-500/10 border border-cyan-400/20 px-3.5 py-2.5 rounded-xl">
            <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-cyan-300 border-t-transparent" />
            <span>{statusText}</span>
          </div>
        )}

        {error && (
          <div className="mt-4 flex items-center gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 px-3.5 py-2.5 rounded-xl">
            <AlertCircle size={15} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-cyan-400/15">
          {onClose && (
            <button
              type="button"
              disabled={loading}
              onClick={onClose}
              className="px-5 py-2.5 rounded-full border border-white/10 text-xs font-semibold uppercase tracking-wider text-gray-300 hover:text-white hover:bg-white/5 transition cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>
          )}

          <button
            type="button"
            disabled={!file || loading}
            onClick={handleUpload}
            className="flex items-center gap-2 rounded-full border border-cyan-400/60 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 px-6 py-2.5 text-xs font-bold uppercase tracking-wider text-white shadow-[0_0_20px_rgba(34,211,238,0.4)] transition duration-300 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <CheckCircle2 size={16} />
            )}
            {loading ? "Extracting..." : "Start Extraction"}
          </button>
        </div>
      </div>
    </div>
  );
}
