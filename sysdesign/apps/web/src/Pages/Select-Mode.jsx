import meeting from "../Images/Mode/meeting.jpg";
import recording from "../Images/Mode/recording.jpg";
import { useNavigate, useLocation } from "react-router-dom";

export default function SelectMode() {
  const navigate = useNavigate();
  const location = useLocation();
  const projectId = location.state?.projectId || new URLSearchParams(location.search).get("projectId");

  return (
    <div className="relative h-screen w-full overflow-hidden">
      <div className="flex flex-col justify-center h-full w-full ">
        <div className="flex flex-col h-[200px] w-full justify-end ">
          <h1
            className="text-center text-6xl font-bold uppercase text-white"
            style={{ fontFamily: "Orbitron, sans-serif" }}
          >
            Select <span className="text-cyan-300">Mode</span>
          </h1>
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center gap-40 p-8">
          <button 
            onClick={() => navigate("/test-meeting", { state: { projectId } })}
            className="group relative flex h-full aspect-[3/4] items-center justify-center cursor-pointer overflow-hidden"
          >
            <img
              src={meeting}
              alt="Meeting"
              className="h-full w-full object-cover border border-cyan-300 transition-transform duration-300 ease-out group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-black/50 " />
            <h1
              style={{ fontFamily: "Orbitron, sans-serif" }}
              className="absolute inset-0 flex justify-center items-center text-white text-4xl transition-all duration-300 ease-out group-hover:text-cyan-300 group-hover:text-[45px]"
            >
              Start Meeting
            </h1>
          </button>

          <button
            onClick={() => navigate("/upload-audio", { state: { projectId } })}
            className="group relative flex h-full aspect-[3/4] items-center justify-center cursor-pointer overflow-hidden"
          >
            <img
              src={recording}
              alt="Recording"
             className="h-full w-full object-cover border border-cyan-300 transition-transform duration-300 ease-out group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-black/50" />
            <h1
              style={{ fontFamily: "Orbitron, sans-serif" }}
              className="absolute inset-0 flex justify-center items-center text-white text-4xl transition-all duration-300 ease-out group-hover:text-cyan-300 group-hover:text-[45px]"
            >
              Upload Audio <br /> Or <br /> Document
            </h1>
          </button>
        </div>
      </div>
    </div>
  );
}
