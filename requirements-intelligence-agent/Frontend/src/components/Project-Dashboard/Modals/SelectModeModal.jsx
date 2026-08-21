import meeting from "../../../Images/Mode/meeting.jpg";
import recording from "../../../Images/Mode/recording.jpg";
import { X } from "lucide-react";

export default function SelectModeModal({ onClose, onSelectMode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-6">
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
        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          className="
            absolute right-5 top-5
            flex h-9 w-9 items-center justify-center
            rounded-full
            border border-white/10
            text-gray-400
            transition
            hover:border-cyan-400/40
            hover:bg-cyan-400/10
            hover:text-white
          "
        >
          <X size={18} />
        </button>

        {/* Heading */}
        <div className="mb-8 mt-4">
          <h1
            className="text-center text-4xl font-bold uppercase text-white"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Select <span className="text-cyan-300">Mode</span>
          </h1>

          <p className="mt-3 text-center text-sm text-white/50">
            Choose how you want to provide the requirements for this project.
          </p>
        </div>

        {/* Cards */}
        <div className="flex items-center justify-center gap-10">
          {/* Meeting */}
          <button
            type="button"
            onClick={() => onSelectMode("meeting")}
            className="
              group relative
              h-[330px]
              aspect-[3/4]
              cursor-pointer
              overflow-hidden
              rounded-xl
              border border-cyan-400/30
              transition-all duration-300
              hover:border-cyan-300
              hover:shadow-[0_0_30px_rgba(34,211,238,0.2)]
            "
          >
            <img
              src={meeting}
              alt="Start Meeting"
              className="
                h-full w-full object-cover
                transition-transform duration-500
                group-hover:scale-105
              "
            />

            <div className="absolute inset-0 bg-black/50 transition-colors duration-300 group-hover:bg-black/40" />

            <div className="absolute inset-0 flex items-center justify-center">
              <span
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="
                  text-4xl font-medium text-white
                  transition-all duration-300
                  group-hover:scale-105
                  group-hover:text-cyan-300
                "
              >
                Start Meeting
              </span>
            </div>
          </button>

          {/* Upload */}
          <button
            type="button"
            onClick={() => onSelectMode("upload")}
            className="
              group relative
              h-[330px]
              aspect-[3/4]
              cursor-pointer
              overflow-hidden
              rounded-xl
              border border-cyan-400/30
              transition-all duration-300
              hover:border-cyan-300
              hover:shadow-[0_0_30px_rgba(34,211,238,0.2)]
            "
          >
            <img
              src={recording}
              alt="Upload Audio or Document"
              className="
                h-full w-full object-cover
                transition-transform duration-500
                group-hover:scale-105
              "
            />

            <div className="absolute inset-0 bg-black/50 transition-colors duration-300 group-hover:bg-black/40" />

            <div
              style={{ fontFamily: "Orbitron, sans-serif" }}
              className="
                absolute inset-0
                flex flex-col
                items-center
                justify-center
                text-center
                text-4xl
                font-medium
                leading-tight
                text-white
                transition-all duration-300
                group-hover:scale-105
                group-hover:text-cyan-300
              "
            >
              <span>Upload Audio</span>
              <span className="my-2 text-2xl text-white/60">or</span>
              <span>Document</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
