import React, { useEffect } from "react";
import { X, Mic, UploadCloud } from "lucide-react";
import meetingImg from "../../../Images/Mode/meeting.jpg";
import recordingImg from "../../../Images/Mode/recording.jpg";

export default function SelectModeModal({ onClose, onSelectMode }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && onClose) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 md:p-6 overflow-hidden animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose) onClose();
      }}
    >
      <div
        className="relative w-full max-w-4xl rounded-3xl border border-cyan-400/30 bg-gradient-to-br from-cyan-950/95 via-[#07151B]/95 to-black shadow-[0_0_50px_rgba(34,211,238,0.25)] p-6 md:p-10 my-auto text-white overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-cyan-400/20 pb-5 mb-8">
          <div>
            <h2
              className="text-2xl md:text-3xl font-bold uppercase tracking-wide text-white"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              Select <span className="text-cyan-300">Analysis Mode</span>
            </h2>
            <p className="text-xs md:text-sm text-gray-400 mt-1">
              Choose how you want to elicit requirements for this project
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white transition cursor-pointer"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modes Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Mode 1: Meeting */}
          <button
            type="button"
            onClick={() => onSelectMode("meeting")}
            className="group relative flex flex-col items-center justify-center rounded-2xl overflow-hidden border border-cyan-400/30 bg-[#0B0D17] p-6 transition-all duration-300 hover:border-cyan-300 hover:shadow-[0_0_30px_rgba(34,211,238,0.3)] cursor-pointer text-left h-[300px]"
          >
            <img
              src={meetingImg}
              alt="Start Meeting"
              className="absolute inset-0 h-full w-full object-cover opacity-35 transition-transform duration-500 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />

            <div className="relative z-10 mt-auto flex flex-col items-start w-full">
              <div className="p-3 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 mb-3 group-hover:bg-cyan-500/30 transition">
                <Mic size={24} />
              </div>
              <h3
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="text-2xl font-bold text-white group-hover:text-cyan-300 transition"
              >
                Live AI Meeting
              </h3>
              <p className="text-xs md:text-sm text-gray-300 mt-1">
                Conduct real-time interactive voice requirement elicitation with Agent 1.
              </p>
            </div>
          </button>

          {/* Mode 2: Upload Audio or Doc */}
          <button
            type="button"
            onClick={() => onSelectMode("upload")}
            className="group relative flex flex-col items-center justify-center rounded-2xl overflow-hidden border border-cyan-400/30 bg-[#0B0D17] p-6 transition-all duration-300 hover:border-cyan-300 hover:shadow-[0_0_30px_rgba(34,211,238,0.3)] cursor-pointer text-left h-[300px]"
          >
            <img
              src={recordingImg}
              alt="Upload Audio"
              className="absolute inset-0 h-full w-full object-cover opacity-35 transition-transform duration-500 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />

            <div className="relative z-10 mt-auto flex flex-col items-start w-full">
              <div className="p-3 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-400/40 mb-3 group-hover:bg-purple-500/30 transition">
                <UploadCloud size={24} />
              </div>
              <h3
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="text-2xl font-bold text-white group-hover:text-cyan-300 transition"
              >
                Upload Audio / Doc
              </h3>
              <p className="text-xs md:text-sm text-gray-300 mt-1">
                Upload recorded stakeholder interviews or raw specification documents.
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
