import React from "react";
import { FileText, Network, Boxes, LayoutTemplate } from "lucide-react";
import roboImage from "../Images/hero.png";
import { useNavigate } from "react-router-dom";
import { FaGithub, FaLinkedin, FaXTwitter } from "react-icons/fa6";

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="hero relative h-screen w-full grid grid-cols-2 bg-transparent z-0  xl:pl-30">
      <div className="relative h-full flex items-start justify-center flex-col space-y-10 ">
        <div className="space-y-10  mt-10">
          <div className="space-y-3">
            <h1
              className="text-white text-7xl uppercase font-bold"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              From <span className="text-cyan-300">Requirements</span> to{" "}
              <span className="text-cyan-300">Design </span>
            </h1>

            <div className="bg-cyan-300/65 w-30 h-0.5 ml-1" />
          </div>

          <div className="space-y-7 mt-14">
            <p className="text-white max-w-md text-base leading-relaxed">
              From conversations to complete software design artifacts. Generate
              SRS, HLD, LLD, and wireframes without weeks of manual analysis
            </p>

            <div className="flex space-x-10 mt-4">
              <button
                onClick={() => navigate("/select-mode")}
                className="relative w-[200px] h-[40px] transition-transform active:scale-95 cursor-pointer"
                style={{
                  animation: "subtlePulse 2s infinite ease-in-out",
                }}
              >
                <style>{`
            @keyframes subtlePulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.03); }
            }
        `}</style>

                <svg
                  className="absolute inset-0 w-full h-full overflow-visible pointer-events-none"
                  viewBox="0 0 275 44"
                  preserveAspectRatio="none"
                >
                  <defs>
                    <linearGradient
                      id="buttonGradient"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="0%"
                    >
                      <stop offset="0%" stopColor="#FFFFFF" />
                      <stop offset="20%" stopColor="#B8F6FF" />
                      <stop offset="50%" stopColor="#2DDCFF" />
                      <stop offset="80%" stopColor="#139DAF" />
                    </linearGradient>
                  </defs>
                  <path
                    d="M273.034 0.5H48.5337C33.2003 14.8333 2.03368 43.5 0.0336752 43.5H231.034L273.034 0.5Z"
                    fill="url(#buttonGradient)"
                    stroke="url(#buttonGradient)"
                  />
                </svg>

                <span className="relative z-10 flex h-full items-center justify-center uppercase font-semibold text-black">
                  Start Designing
                </span>
              </button>

              <div className="flex items-center space-x-3">
                <button className="play-btn">
                  <svg viewBox="0 0 448 512" width="16">
                    <path
                      d="M424.4 214.7L72.4 6.6C43.8-10.3 0 6.1 0 47.9V464c0 37.5 40.7 60.1 72.4 41.3l352-208c31.4-18.5 31.5-64.1 0-82.6z"
                      fill="currentColor"
                    />
                  </svg>
                </button>
                <span className="text-white"> Watch Demo</span>
              </div>
            </div>
          </div>
          <div className="absolute  bottom-4 flex items-center gap-6">
            <FaGithub className="text-2xl text-white/40 hover:text-cyan-400 hover:scale-125 transition-transform duration-300 ease-out  transition-colors cursor-pointer" />
            <FaLinkedin className="text-2xl text-white/40 hover:text-cyan-400 hover:scale-125 transition-transform duration-300 ease-out  transition-colors cursor-pointer" />
            <FaXTwitter className="text-2xl text-white/40 hover:text-cyan-400 hover:scale-125 transition-transform duration-300 ease-out  transition-colors cursor-pointer" />
          </div>
        </div>
      </div>

      <div className=" h-[90%] absolute bottom-0 right-30">
        {/* Cyan glow */}
        <div
          className="absolute bottom-0 -right-10 translate-y-1/2 w-[500px]  h-[1000px]
          rounded-full bg-cyan-300/20 blur-[100px] pointer-events-none"
        />

        <img
          src={roboImage}
          className="relative z-10 w-full h-full object-contain"
          alt="AI robot"
        />
      </div>
    </div>
  );
}

export default LandingPage;
