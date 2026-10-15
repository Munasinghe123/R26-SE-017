import React, { useEffect, useState, useRef, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  LiveKitRoom,
  VideoConference,
  RoomAudioRenderer,
  useRoomContext,
  useLocalParticipant,
} from "@livekit/components-react";
import { RoomEvent } from "livekit-client";
import "@livekit/components-styles";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import {
  Sparkles,
  Zap,
  Radio,
  Share2,
  Copy,
  Check,
  LogOut,
  ArrowRight,
  Shield,
  Layers,
  Cpu,
  Mic,
  MicOff,
  Trash2,
  AlertCircle,
  FileCheck2,
  User,
  Users,
  Video,
  CheckCircle2,
  Smile,
} from "lucide-react";

const AGENT1_BASE = import.meta.env.VITE_AGENT1_URL || "http://127.0.0.1:8001";

// ── Inner Meeting Room with Live AI Extraction & Data Sync ───────────────────
function MeetingRoomInner({
  connection,
  projectId,
  roomName,
  userRole,
  username,
  onFinishMeeting,
}) {
  const navigate = useNavigate();
  const room = useRoomContext();
  const { isMicrophoneEnabled } = useLocalParticipant();
  const [requirements, setRequirements] = useState([]);
  const [filter, setFilter] = useState("all");
  const [isListening, setIsListening] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [manualInput, setManualInput] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [clientConfirmed, setClientConfirmed] = useState(false);

  const recognitionRef = useRef(null);
  const lastAnalyzedText = useRef("");

  // 1. Send data packet over LiveKit Data Channel
  const broadcastMessage = useCallback(
    (type, data) => {
      if (!room || !room.localParticipant) return;
      try {
        const payload = new TextEncoder().encode(
          JSON.stringify({ type, data, sender: username, role: userRole })
        );
        room.localParticipant.publishData(payload, { reliable: true });
      } catch (err) {
        console.warn("[LiveKit DataChannel] Broadcast error:", err);
      }
    },
    [room, username, userRole]
  );

  // 2. Listen to LiveKit Data Channel
  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (payload) => {
      try {
        const decoded = new TextDecoder().decode(payload);
        const msg = JSON.parse(decoded);

        if (msg.type === "NEW_REQUIREMENT" && msg.data) {
          setRequirements((prev) => {
            if (prev.some((r) => r.id === msg.data.id)) return prev;
            toast.custom(
              (t) => (
                <div
                  className={`${
                    t.visible ? "animate-enter" : "animate-leave"
                  } bg-slate-900/90 border border-cyan-500/50 text-white p-3 rounded-lg shadow-xl flex items-center gap-3 backdrop-blur-md`}
                >
                  <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
                  <div>
                    <p className="text-xs font-semibold text-cyan-300">
                      Requirement Captured
                    </p>
                    <p className="text-xs text-slate-200 line-clamp-1">
                      {msg.data.title}
                    </p>
                  </div>
                </div>
              ),
              { duration: 3000 }
            );
            return [msg.data, ...prev];
          });
        } else if (msg.type === "CLIENT_CONFIRMED_SCOPE") {
          setClientConfirmed(true);
          toast.success(`${msg.sender || "Client"} has confirmed the agreed requirements!`, {
            icon: "🎉",
            duration: 5000,
          });
        } else if (msg.type === "MEETING_CONCLUDED") {
          toast.success("Business Analyst has concluded the session! Redirecting to dashboard...", {
            icon: "📋",
            duration: 3500,
          });
          setTimeout(() => {
            if (projectId) {
              navigate(`/project-dashboard/${projectId}`);
            } else {
              navigate("/project-dashboard");
            }
          }, 2000);
        }
      } catch (err) {
        console.warn("[LiveKit DataChannel] Parse error:", err);
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room]);

  // 3. Analyze spoken sentence through Agent 1 Real-Time Elicitation Endpoint
  const analyzeUtterance = useCallback(
    async (textToAnalyze, speakerName) => {
      const clean = (textToAnalyze || "").trim();
      if (!clean || clean.length < 10) return;
      if (clean === lastAnalyzedText.current) return;
      lastAnalyzedText.current = clean;

      setIsAnalyzing(true);
      try {
        const resp = await axios.post(
          `${AGENT1_BASE}/live-meeting/detect-requirement`,
          {
            text: clean,
            speaker: speakerName || username,
            role: userRole,
            project_id: projectId || null,
            room_name: roomName,
          }
        );

        if (resp.data && resp.data.is_requirement === true) {
          const newCard = resp.data;
          setRequirements((prev) => {
            if (prev.some((r) => r.id === newCard.id)) return prev;
            return [newCard, ...prev];
          });
          broadcastMessage("NEW_REQUIREMENT", newCard);

          toast.success(`[${newCard.category}] ${newCard.title}`, {
            icon: "✨",
            style: {
              background: "#0f172a",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.4)",
            },
          });
        }
      } catch (err) {
        console.warn("[Live Elicitation] Analysis error:", err);
      } finally {
        setIsAnalyzing(false);
      }
    },
    [AGENT1_BASE, broadcastMessage, projectId, roomName, userRole, username]
  );

  // 4. Web Speech API (Real-Time In-Browser Voice Recognition)
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("Web Speech API not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          setLiveTranscript("");
          analyzeUtterance(transcript, username);
        } else {
          interim += transcript;
        }
      }
      if (interim) {
        setLiveTranscript(interim);
      }
    };

    recognition.onerror = (e) => {
      if (e.error !== "no-speech") {
        console.warn("Speech recognition error:", e.error);
      }
    };

    recognition.onend = () => {
      if (isListening) {
        try {
          recognition.start();
        } catch (_) {}
      }
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch (_) {}
    };
  }, [isListening, analyzeUtterance, username]);

  // Sync AI Speech Listener with the actual microphone toggle
  useEffect(() => {
    if (isMicrophoneEnabled) {
      setIsListening(true);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (_) {}
      }
    } else {
      setIsListening(false);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (_) {}
      }
    }
  }, [isMicrophoneEnabled]);

  // Toggle listening
  const toggleListening = async () => {
    if (room && room.localParticipant) {
      const willEnable = !isMicrophoneEnabled;
      try {
        await room.localParticipant.setMicrophoneEnabled(willEnable);
        setIsListening(willEnable);
        toast(willEnable ? "Microphone Unmuted" : "Microphone Muted", {
          icon: willEnable ? "🎙️" : "🔇",
        });
      } catch (err) {
        console.warn("Could not toggle microphone:", err);
        toast.error("Please grant microphone permissions in your browser.");
      }
    } else {
      setIsListening((prev) => !prev);
    }
  };

  // 5. Manual Note / Utterance submission
  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (!manualInput.trim()) return;
    analyzeUtterance(manualInput, username);
    setManualInput("");
  };

  // 6. Copy Client Invite Link
  const copyInviteLink = () => {
    const origin = window.location.origin;
    const clientLink = `${origin}/test-meeting?room=${roomName}&role=client${
      projectId ? `&projectId=${projectId}` : ""
    }`;
    navigator.clipboard.writeText(clientLink);
    setCopiedLink(true);
    toast.success("Client invite link copied to clipboard!");
    setTimeout(() => setCopiedLink(false), 2500);
  };

  // 7. Client Confirm Scope
  const handleClientConfirm = () => {
    setClientConfirmed(true);
    broadcastMessage("CLIENT_CONFIRMED_SCOPE", { count: requirements.length });
    toast.success("You confirmed the agreed project requirements!", { icon: "✅" });
  };

  // 8. BA Finish Meeting & Save Requirements
  const handleFinish = async () => {
    if (finishing) return;
    setFinishing(true);
    try {
      const meetingId = projectId ? projectId : `meeting-${Date.now()}`;
      toast.loading("Saving requirements & returning to dashboard...", {
        id: "finish-toast",
      });

      broadcastMessage("MEETING_CONCLUDED", { meetingId });

      await axios.post(
        `${AGENT1_BASE}/live-meeting/save-requirements`,
        {
          meeting_id: meetingId,
          project_id: projectId || null,
          requirements: requirements,
        }
      );

      toast.success("Requirements saved! Opening dashboard...", {
        id: "finish-toast",
      });

      if (room) {
        await room.disconnect();
      }

      onFinishMeeting(meetingId, projectId, requirements);
    } catch (err) {
      console.error("Error finalizing meeting:", err);
      toast.error("Failed to save requirements: " + err.message, {
        id: "finish-toast",
      });
      setFinishing(false);
    }
  };

  // Filtered requirements
  const filteredReqs = requirements.filter((r) => {
    if (filter === "all") return true;
    if (filter === "fr") return r.category === "FR";
    if (filter === "nfr") return r.category === "NFR";
    return true;
  });

  const frCount = requirements.filter((r) => r.category === "FR").length;
  const nfrCount = requirements.filter((r) => r.category === "NFR").length;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#060a12] text-slate-100 font-sans">
      <Toaster position="top-right" />

      {/* ── LEFT COLUMN: VIDEO CONFERENCE AREA (65-70%) ───────────────────── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden border-r border-cyan-500/20">
        {/* Top Header Bar */}
        <div className="h-16 px-6 bg-[#090e1a]/90 backdrop-blur-md border-b border-cyan-500/20 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 absolute" />
              <h1
                className="text-lg font-bold tracking-wider text-white uppercase"
                style={{ fontFamily: "Orbitron, sans-serif" }}
              >
                SYS<span className="text-cyan-400">DESIGN</span> // LIVE MEETING
              </h1>
            </div>

            <div className="h-4 w-[1px] bg-slate-700" />

            <div className="flex items-center gap-2 px-3 py-1 bg-slate-800/60 rounded-full border border-slate-700/60 text-xs">
              <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span className="text-slate-400">Room:</span>
              <span className="font-mono text-cyan-300 font-medium">
                {roomName}
              </span>
            </div>

            <span
              className={`text-xs px-2.5 py-0.5 rounded font-semibold uppercase tracking-wider flex items-center gap-1.5 ${
                userRole === "ba"
                  ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                  : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
              }`}
            >
              <User className="w-3 h-3" />
              {userRole === "ba" ? `BA (Host): ${username}` : `Client: ${username}`}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {userRole === "ba" && (
              <button
                onClick={copyInviteLink}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 hover:border-cyan-400/50 transition cursor-pointer"
              >
                {copiedLink ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Share2 className="w-3.5 h-3.5 text-cyan-400" />
                )}
                <span>{copiedLink ? "Link Copied!" : "Invite Client Link"}</span>
              </button>
            )}

            <button
              onClick={toggleListening}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs border transition cursor-pointer ${
                isListening
                  ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/40 hover:bg-cyan-500/20"
                  : "bg-rose-500/10 text-rose-300 border-rose-500/40 hover:bg-rose-500/20"
              }`}
              title="Toggle AI Speech Listener"
            >
              {isListening ? (
                <>
                  <Mic className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                  <span>AI Listener Active</span>
                </>
              ) : (
                <>
                  <MicOff className="w-3.5 h-3.5 text-rose-400" />
                  <span>AI Listener Muted</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* LiveKit Video Grid */}
        <div className="flex-1 relative bg-black/40 overflow-hidden" data-lk-theme="default">
          <VideoConference />
          <RoomAudioRenderer />
        </div>

        {/* Live Subtitle / Spoken Utterance Ticker */}
        {liveTranscript && (
          <div className="h-12 px-6 bg-slate-900/95 border-t border-cyan-500/30 flex items-center gap-3 text-xs text-cyan-200 shrink-0 backdrop-blur-md">
            <Radio className="w-4 h-4 text-cyan-400 animate-pulse shrink-0" />
            <span className="font-semibold text-cyan-400 shrink-0">Hearing:</span>
            <span className="italic truncate text-slate-200">
              "{liveTranscript}"
            </span>
          </div>
        )}
      </div>

      {/* ── RIGHT COLUMN: REAL-TIME AI REQUIREMENTS STREAM (30-35%) ──────── */}
      <div className="w-[430px] flex flex-col h-full bg-[#080d19] border-l border-cyan-500/20 shadow-2xl shrink-0">
        {/* Stream Header */}
        <div className="p-4 border-b border-cyan-500/20 bg-[#0c1322]">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-cyan-500/10 border border-cyan-500/30">
                <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                  {userRole === "ba" ? "AI Requirements Stream" : "Live Agreed Scope"}
                  {isAnalyzing && (
                    <span className="text-[10px] text-cyan-400 animate-pulse font-normal">
                      (Analyzing...)
                    </span>
                  )}
                </h2>
                <p className="text-[11px] text-slate-400">
                  {userRole === "ba"
                    ? "Real-time semantic extraction"
                    : "Real-time client scope preview"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5 text-xs font-mono">
              <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                {requirements.length} Captured
              </span>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 mt-3">
            <button
              onClick={() => setFilter("all")}
              className={`flex-1 py-1 text-xs rounded transition font-medium cursor-pointer ${
                filter === "all"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-transparent"
              }`}
            >
              All ({requirements.length})
            </button>
            <button
              onClick={() => setFilter("fr")}
              className={`flex-1 py-1 text-xs rounded transition font-medium cursor-pointer ${
                filter === "fr"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  : "bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-transparent"
              }`}
            >
              FR ({frCount})
            </button>
            <button
              onClick={() => setFilter("nfr")}
              className={`flex-1 py-1 text-xs rounded transition font-medium cursor-pointer ${
                filter === "nfr"
                  ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                  : "bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-transparent"
              }`}
            >
              NFR ({nfrCount})
            </button>
          </div>
        </div>

        {/* Requirements Card Feed */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
          {filteredReqs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-800/60 border border-slate-700/60 flex items-center justify-center">
                <Radio className="w-6 h-6 text-slate-400 animate-pulse" />
              </div>
              <p className="text-xs font-medium text-slate-400">
                Listening to dialogue...
              </p>
              <p className="text-[11px] text-slate-500 max-w-[260px]">
                {userRole === "ba"
                  ? "As you and the client discuss, requirements will automatically appear here."
                  : "As you explain your requirements to the Business Analyst, the agreed features will appear here."}
              </p>
            </div>
          ) : (
            filteredReqs.map((req) => (
              <div
                key={req.id}
                className="group relative bg-[#0d1527]/90 border border-slate-700/70 hover:border-cyan-400/50 rounded-xl p-3.5 shadow-lg transition-all duration-200 backdrop-blur-sm"
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded tracking-wide uppercase ${
                        req.category === "FR"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                      }`}
                    >
                      {req.category}
                    </span>
                    {req.sub_type && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {req.sub_type}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-1">
                    <span className="text-[10px] text-slate-500 font-mono">
                      {req.timestamp}
                    </span>
                    {userRole === "ba" && (
                      <button
                        onClick={() =>
                          setRequirements((prev) =>
                            prev.filter((x) => x.id !== req.id)
                          )
                        }
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 text-slate-500 transition cursor-pointer"
                        title="Dismiss requirement"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>

                <h3 className="text-xs font-semibold text-slate-100 mb-1 group-hover:text-cyan-300 transition">
                  {req.title}
                </h3>

                <p className="text-[11px] text-slate-300 leading-relaxed">
                  {req.description}
                </p>

                {req.source_text && (
                  <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500">
                    <span className="italic truncate max-w-[260px]">
                      "{req.source_text}"
                    </span>
                    <span className="text-cyan-400 font-mono shrink-0">
                      {Math.round(req.confidence * 100)}% conf
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Manual Dictate / Type Box */}
        <form
          onSubmit={handleManualSubmit}
          className="p-3 border-t border-cyan-500/20 bg-[#0a101f]"
        >
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value)}
              placeholder="Dictate or type statement..."
              className="flex-1 bg-slate-900/90 border border-slate-700/80 focus:border-cyan-400 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none transition"
            />
            <button
              type="submit"
              disabled={!manualInput.trim() || isAnalyzing}
              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-xs font-semibold text-white transition flex items-center gap-1 cursor-pointer shrink-0"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </div>
        </form>

        {/* Role-Specific Action Footer */}
        <div className="p-4 border-t border-cyan-500/20 bg-[#080d19]">
          {userRole === "ba" ? (
            <button
              onClick={handleFinish}
              disabled={finishing}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs tracking-wider uppercase flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 transition cursor-pointer disabled:opacity-50"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              {finishing ? (
                <>
                  <Cpu className="w-4 h-4 animate-spin text-white" />
                  <span>Saving Requirements...</span>
                </>
              ) : (
                <>
                  <FileCheck2 className="w-4 h-4" />
                  <span>Finish Meeting & Review Requirements ({requirements.length})</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={handleClientConfirm}
                disabled={clientConfirmed || requirements.length === 0}
                className={`flex-1 py-2.5 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition cursor-pointer ${
                  clientConfirmed
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20"
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{clientConfirmed ? "Agreed Scope Confirmed" : "Confirm Scope"}</span>
              </button>

              <button
                onClick={() => {
                  if (projectId) {
                    navigate(`/project-dashboard/${projectId}`);
                  } else {
                    navigate("/project-dashboard");
                  }
                }}
                className="py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs border border-slate-700 transition cursor-pointer flex items-center gap-1.5"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Leave</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Root TestMeeting Component (Pre-Join Lobby & LiveKit Room) ─────────────────
export default function TestMeeting() {
  const location = useLocation();
  const navigate = useNavigate();

  const queryParams = new URLSearchParams(location.search);
  const projectId = location.state?.projectId || queryParams.get("projectId") || "";
  const roomParam = queryParams.get("room") || (projectId ? `proj-${projectId.slice(0, 8)}` : "sysdesign-room");
  const roleParam = queryParams.get("role") || location.state?.role || "ba";
  const defaultUser =
    queryParams.get("username") ||
    location.state?.username ||
    (roleParam === "ba" ? "Business Analyst" : "Client Partner");

  // State
  const [joined, setJoined] = useState(false);
  const [nameInput, setNameInput] = useState(defaultUser);
  const [connection, setConnection] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Connect to room when user enters lobby
  const handleJoinLobby = async (e) => {
    e?.preventDefault();
    if (!nameInput.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const resp = await axios.get(
        `${AGENT1_BASE}/test/livekit-token?room=${encodeURIComponent(
          roomParam
        )}&username=${encodeURIComponent(nameInput.trim())}&role=${encodeURIComponent(
          roleParam
        )}${projectId ? `&project_id=${projectId}` : ""}`
      );

      setConnection(resp.data);
      setJoined(true);
    } catch (err) {
      console.error("LiveKit token error:", err);
      setError(err.response?.data?.detail || err.message || "Failed to join room.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinishMeeting = (meetingId, projId, savedReqs) => {
    const targetProject = projId || projectId;
    if (targetProject) {
      navigate(`/project-dashboard/${targetProject}`, {
        state: {
          meetingId: meetingId,
        },
      });
    } else {
      navigate(`/project-dashboard`);
    }
  };

  // ── Pre-Join Lobby View ────────────────────────────────────────────────────
  if (!joined) {
    return (
      <div className="min-h-screen w-screen bg-[#060a12] flex items-center justify-center p-6 text-slate-100">
        <Toaster position="top-right" />
        <div className="w-full max-w-md bg-[#0b1222]/90 border border-cyan-500/30 rounded-2xl p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600" />

          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Users className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1
                className="text-lg font-bold text-white tracking-wider uppercase"
                style={{ fontFamily: "Orbitron, sans-serif" }}
              >
                SYS<span className="text-cyan-400">DESIGN</span> // MEETING
              </h1>
              <p className="text-xs text-slate-400">
                AI-Powered Requirements Elicitation
              </p>
            </div>
          </div>

          <form onSubmit={handleJoinLobby} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                Your Display Name
              </label>
              <input
                type="text"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                placeholder="e.g. Mr. Pereira, John Doe"
                className="w-full bg-slate-900 border border-slate-700 focus:border-cyan-400 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none transition"
                required
              />
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
              <div className="flex justify-between items-center text-slate-400">
                <span>Room Name:</span>
                <span className="font-mono text-cyan-300 font-semibold">{roomParam}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Assigned Role:</span>
                <span
                  className={`font-semibold uppercase px-2 py-0.5 rounded text-[10px] ${
                    roleParam === "ba"
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  }`}
                >
                  {roleParam === "ba" ? "Business Analyst (Host)" : "Client Partner"}
                </span>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !nameInput.trim()}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs tracking-wider uppercase flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/25 transition cursor-pointer disabled:opacity-50 mt-4"
              style={{ fontFamily: "Orbitron, sans-serif" }}
            >
              {loading ? (
                <>
                  <Cpu className="w-4 h-4 animate-spin text-white" />
                  <span>Entering Session...</span>
                </>
              ) : (
                <>
                  <Video className="w-4 h-4" />
                  <span>Enter Live Meeting</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ── Connected LiveKit Room View ────────────────────────────────────────────
  return (
    <LiveKitRoom
      token={connection.token}
      serverUrl={connection.server_url}
      connect={true}
      audio={false}
      video={false}
      data-lk-theme="default"
      style={{ height: "100vh", width: "100vw" }}
    >
      <MeetingRoomInner
        connection={connection}
        projectId={projectId}
        roomName={roomParam}
        userRole={roleParam}
        username={nameInput}
        onFinishMeeting={handleFinishMeeting}
      />
    </LiveKitRoom>
  );
}