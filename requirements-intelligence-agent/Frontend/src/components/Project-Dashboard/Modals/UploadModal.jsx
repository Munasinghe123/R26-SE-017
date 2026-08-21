import React, { useRef, useState } from "react";
import { FileUp, Upload, X } from "lucide-react";
import api from "../../../api/api";
import { useSelector } from "react-redux";

export default function UploadModal({ onClose, onSubmit }) {

  const currentProject = useSelector((state) => state.project.currentProject);

  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;

    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];

    handleFile(droppedFile);
  };

  const handleBrowse = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!file) return;

    console.log("CURRENT PROJECT FROM REDUX:", currentProject);

    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_id", currentProject.id);

    try {
      const res = await api.post("/extract-requirements", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const data = res.data;

      console.log("Upload successful:", data);

      onSubmit(data);
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      {/* Modal */}
      <div
        className="
          relative
          flex
          h-[520px]
          w-[760px]
          flex-col
          overflow-hidden
          rounded-3xl
          border border-cyan-400/20
          bg-[#080A14]
          shadow-[0_0_60px_rgba(34,211,238,0.15)]
        "
      >
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b border-white/10 px-8 py-6">
          <div className="flex items-center justify-center w-full">
            <h2
              style={{ fontFamily: "Orbitron, sans-serif" }}
              className="mt-1 text-4xl font-semibold text-white "
            >
              Add Your <span className="text-cyan-300"> Source</span>
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="
              rounded-full
              p-2
              text-gray-500
              transition
              hover:bg-white/5
              hover:text-white
            "
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex flex-1 flex-col items-center justify-center px-10">
          <p className="mb-6 text-center text-sm text-white/50">
            Upload an audio recording or project document to begin analysis.
          </p>

          {/* Upload area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={handleBrowse}
            className={`
              flex
              h-[220px]
              w-full
              cursor-pointer
              flex-col
              items-center
              justify-center
              rounded-2xl
              border
              border-dashed
              transition-all
              duration-200
              ${
                dragging
                  ? "border-cyan-300 bg-cyan-400/10"
                  : "border-white/15 bg-white/[0.02] hover:border-cyan-400/50 hover:bg-cyan-400/[0.03]"
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".mp3,.wav,.m4a,.mp4,.pdf,.doc,.docx,.txt"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />

            {file ? (
              <>
                <FileUp size={34} className="text-cyan-300" />

                <p className="mt-4 max-w-[500px] truncate text-sm font-medium text-white">
                  {file.name}
                </p>

                <p className="mt-1 text-xs text-white/40">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </>
            ) : (
              <>
                <Upload size={34} className="text-cyan-300" />

                <p className="mt-4 text-base font-medium text-white">
                  Drop your file here
                </p>

                <p className="mt-1 text-sm text-white/40">or click to browse</p>

                <p className="mt-5 text-xs tracking-wide text-white/30">
                  AUDIO · PDF · DOCX · TXT
                </p>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex shrink-0 items-center justify-end border-t border-white/10 px-8 py-5">
          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || loading}
            className="
              rounded-full
              border
              border-cyan-400/60
              bg-black
              px-6
              py-3
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
              disabled:opacity-30
            "
          >
            Start Analysis
          </button>
        </div>
      </div>
    </div>
  );
}
