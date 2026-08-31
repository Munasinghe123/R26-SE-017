import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ShieldCheck,
  Sparkles,
  Copy,
  Check,
  CheckCircle2,
  Info,
  Pencil,
  Trash2,
  RotateCcw,
  Plus,
  X,
  Save,
  HelpCircle,
  Send,
  CheckCheck,
} from "lucide-react";
import toast from "react-hot-toast";

const AGENT1 = import.meta.env.VITE_AGENT1_URL || "http://127.0.0.1:8001";

// ---------------------------------------------------------------------------
// Parse client_view sections/items into a flat editable list.
// ---------------------------------------------------------------------------
function parseItems(clientView) {
  const out = [];
  if (!clientView) return out;

  if (clientView?.items && Array.isArray(clientView.items)) {
    clientView.items.forEach((item) => {
      const text =
        item.text ||
        item.description ||
        (typeof item === "string" ? item : JSON.stringify(item));
      out.push({
        id: item.requirement_id || item.id || `i-${out.length}`,
        text,
        originalText: text,
        deleted: false,
        isNew: false,
      });
    });
  } else if (clientView?.sections && Array.isArray(clientView.sections)) {
    clientView.sections.forEach((sec) =>
      sec.items?.forEach((item) => {
        const text =
          item.text ||
          item.description ||
          (typeof item === "string" ? item : JSON.stringify(item));
        out.push({
          id: item.requirement_id || item.id || `i-${out.length}`,
          text,
          originalText: text,
          deleted: false,
          isNew: false,
        });
      })
    );
  }

  return out;
}

// ---------------------------------------------------------------------------
// Map local items → backend ClientRequirementReview payload
// ---------------------------------------------------------------------------
function buildPayload(items) {
  return items.map((item) => {
    if (item.deleted) {
      return { id: item.id, action: "delete", text: item.originalText };
    }
    if (item.isNew) {
      return { id: item.id, action: "add", text: item.text };
    }
    if (item.text !== item.originalText) {
      return { id: item.id, action: "edit", text: item.text };
    }
    return { id: item.id, action: "keep", text: item.text };
  });
}

export default function ClientRequirementReview() {
  const { meetingId: paramMeetingId } = useParams();
  const navigate = useNavigate();
  const meetingId = paramMeetingId || localStorage.getItem("lastMeetingId");

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [copied, setCopied] = useState(false);

  // CRUD state
  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState("");
  const [showAddInput, setShowAddInput] = useState(false);
  const [newText, setNewText] = useState("");

  // Targeted Questions HITL state
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({}); // { [question_id]: string }
  const [stage, setStage] = useState("review"); // "review" | "questions" | "completed"

  // ---- Fetch review and existing questions on load ------------------------
  const fetchReview = async () => {
    if (!meetingId) return;
    setFetching(true);
    try {
      const res = await axios.get(`${AGENT1}/meetings/${meetingId}/review`);
      if (res?.data?.client_view) {
        setItems(parseItems(res.data.client_view));
      }

      try {
        const qRes = await axios.get(`${AGENT1}/meetings/${meetingId}/questions`);
        if (qRes?.data?.questions && qRes.data.questions.length > 0) {
          setQuestions(qRes.data.questions);
          setStage("questions");
        }
      } catch {
        // No questions endpoint or not in questions stage yet
      }
    } catch (err) {
      console.error("Failed to load review:", err);
      toast.error("Could not load requirements. Please try again.");
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    if (meetingId) fetchReview();
  }, [meetingId]);

  // ---- CRUD & Keep Actions -------------------------------------------------
  const startEdit = (item) => {
    setEditingId(item.id);
    setEditingText(item.text);
  };
  const cancelEdit = () => {
    setEditingId(null);
    setEditingText("");
  };

  const saveEdit = (id) => {
    if (!editingText.trim()) {
      toast.error("Requirement cannot be empty.");
      return;
    }
    setItems((prev) =>
      prev.map((i) => (i.id === id ? { ...i, text: editingText.trim() } : i))
    );
    cancelEdit();
  };

  const toggleDelete = (id) =>
    setItems((prev) =>
      prev.map((i) => (i.id === id ? { ...i, deleted: !i.deleted } : i))
    );

  // Explicit KEEP action: restores original text and un-deletes
  const handleKeep = (id) => {
    setItems((prev) =>
      prev.map((i) =>
        i.id === id
          ? { ...i, text: i.originalText || i.text, deleted: false }
          : i
      )
    );
    toast.success("Requirement marked as kept.");
  };

  const handleAddNew = () => {
    if (!newText.trim()) {
      toast.error("Please enter a requirement.");
      return;
    }
    setItems((prev) => [
      ...prev,
      {
        id: `new-${Date.now()}`,
        text: newText.trim(),
        originalText: "",
        deleted: false,
        isNew: true,
      },
    ]);
    setNewText("");
    setShowAddInput(false);
    toast.success("Requirement added.");
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(
      `${window.location.origin}/client/requirements/${meetingId}`
    );
    setCopied(true);
    toast.success("Link copied!");
    setTimeout(() => setCopied(false), 2500);
  };

  // ---- Submit Review → Runs graph up to generate_targeted_questions --------
  const handleSubmitReview = async () => {
    const payload = buildPayload(items);
    if (payload.length === 0) {
      toast.error("No requirements to submit.");
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${AGENT1}/meetings/${meetingId}/review`, {
        items: payload,
      });

      const returnedQuestions = res.data?.questions || [];
      if (returnedQuestions.length > 0) {
        setQuestions(returnedQuestions);
        setStage("questions");
        toast.success("Changes analyzed! Please answer a few clarification questions.");
      } else {
        setStage("completed");
        toast.success("Review submitted! All changes reconciled successfully.");
      }
    } catch (err) {
      console.error("Submit failed:", err);
      const msg =
        err?.response?.data?.detail || "Submit failed. Please check connection.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // ---- Submit Answers to Targeted Questions --------------------------------
  const handleAnswerChange = (qId, val) => {
    setAnswers((prev) => ({ ...prev, [qId]: val }));
  };

  const handleSubmitAnswers = async () => {
    const unAnswered = questions.filter(
      (q) => !answers[q.id]?.trim()
    );
    if (unAnswered.length > 0) {
      toast.error("Please provide answers to all clarification questions.");
      return;
    }

    const payload = questions.map((q) => ({
      question_id: q.id,
      requirement_id: q.requirement_id,
      answer: answers[q.id].trim(),
    }));

    try {
      setLoading(true);
      await axios.post(
        `${AGENT1}/meetings/${meetingId}/questions/answers`,
        { answers: payload }
      );
      setStage("completed");
      toast.success("Answers submitted and requirements reconciled!");
    } catch (err) {
      console.error("Failed to submit answers:", err);
      const msg =
        err?.response?.data?.detail || "Failed to submit answers. Please try again.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // ---- Guards --------------------------------------------------------------
  if (!meetingId) {
    return (
      <div className="min-h-screen w-full pt-28 pb-16 px-6 text-white flex flex-col items-center justify-center">
        <div className="max-w-md w-full p-8 rounded-3xl bg-[#0f172a]/90 border border-cyan-500/30 text-center shadow-2xl space-y-4">
          <Info size={40} className="mx-auto text-cyan-400" />
          <h2 className="text-2xl font-bold">No Project ID Specified</h2>
          <p className="text-gray-400 text-sm">Select a project from your dashboard.</p>
          <button
            onClick={() => navigate("/client-dashboard")}
            className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-xl transition cursor-pointer"
          >
            Go to Client Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (fetching) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400 mb-4" />
        <p className="text-cyan-300 font-medium animate-pulse">Loading Requirements...</p>
      </div>
    );
  }

  const keptCount = items.filter((i) => !i.deleted && !i.isNew && i.text === i.originalText).length;
  const editedCount = items.filter((i) => !i.deleted && !i.isNew && i.text !== i.originalText).length;
  const addedCount = items.filter((i) => !i.deleted && i.isNew).length;
  const deletedCount = items.filter((i) => i.deleted).length;

  return (
    <div className="min-h-screen w-full pt-28 pb-16 px-4 md:px-12 text-white">
      <div className="max-w-4xl mx-auto space-y-8">

        {/* HEADER */}
        <div className="relative p-8 rounded-3xl bg-[#0f172a]/90 border border-cyan-500/30 shadow-2xl backdrop-blur-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3">
                <ShieldCheck size={14} />
                Client Review Portal
              </div>
              <h1
                style={{ fontFamily: "Orbitron, sans-serif" }}
                className="text-3xl md:text-4xl font-extrabold text-white"
              >
                {stage === "questions" ? (
                  <>Clarification <span className="text-amber-400">Questions</span></>
                ) : stage === "completed" ? (
                  <>Review <span className="text-emerald-400">Completed</span></>
                ) : (
                  <>Requirements <span className="text-cyan-300">Review</span></>
                )}
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleCopyShareLink}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-950/60 border border-cyan-400/30 hover:border-cyan-400 text-cyan-300 text-xs font-medium transition cursor-pointer"
              >
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? "Copied!" : "Share Link"}
              </button>
            </div>
          </div>
          <p className="text-gray-300 text-sm leading-relaxed max-w-3xl">
            {stage === "questions"
              ? "Our analysis identified a few points that need your clarification. Please answer below to finalize requirements."
              : stage === "completed"
              ? "Thank you! Your requirements and answers have been processed and reconciled."
              : "Review the requirements below. You can keep, edit, delete, or add new requirements before submitting your review."}
          </p>
        </div>

        {/* STAGE 1: REQUIREMENTS REVIEW */}
        {stage === "review" && (
          <>
            <div className="p-8 rounded-3xl bg-[#0f172a]/90 border border-white/10 shadow-2xl backdrop-blur-xl space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">
                    <Sparkles size={20} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">System Requirements</h3>
                    <p className="text-xs text-gray-400">Keep, edit, remove, or add requirements</p>
                  </div>
                </div>

                {/* Status Pills */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-400/20">
                    {keptCount} Kept
                  </span>
                  {editedCount > 0 && (
                    <span className="text-[11px] font-semibold text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-400/20">
                      {editedCount} Edited
                    </span>
                  )}
                  {addedCount > 0 && (
                    <span className="text-[11px] font-semibold text-purple-400 bg-purple-500/10 px-2.5 py-1 rounded-full border border-purple-400/20">
                      {addedCount} Added
                    </span>
                  )}
                  {deletedCount > 0 && (
                    <span className="text-[11px] font-semibold text-red-400 bg-red-500/10 px-2.5 py-1 rounded-full border border-red-400/20">
                      {deletedCount} Deleted
                    </span>
                  )}
                  <button
                    onClick={() => setShowAddInput((v) => !v)}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-500/15 border border-purple-400/30 hover:border-purple-400/60 text-purple-300 text-xs font-semibold transition cursor-pointer ml-1"
                  >
                    <Plus size={14} /> Add
                  </button>
                </div>
              </div>

              {showAddInput && (
                <div className="flex items-start gap-3 p-4 rounded-2xl bg-purple-500/10 border border-purple-400/30">
                  <textarea
                    autoFocus
                    rows={2}
                    value={newText}
                    onChange={(e) => setNewText(e.target.value)}
                    placeholder="Describe the new requirement..."
                    className="flex-1 bg-transparent text-sm text-white placeholder-gray-500 resize-none focus:outline-none leading-relaxed"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleAddNew();
                      }
                      if (e.key === "Escape") {
                        setShowAddInput(false);
                        setNewText("");
                      }
                    }}
                  />
                  <div className="flex gap-2 mt-0.5">
                    <button
                      onClick={handleAddNew}
                      className="p-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white transition cursor-pointer"
                      title="Save"
                    >
                      <Save size={14} />
                    </button>
                    <button
                      onClick={() => {
                        setShowAddInput(false);
                        setNewText("");
                      }}
                      className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 transition cursor-pointer"
                      title="Cancel"
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              )}

              {items.length === 0 ? (
                <div className="py-12 text-center text-gray-400 space-y-3">
                  <Info size={32} className="mx-auto text-gray-500" />
                  <p className="text-sm">No requirements found for this session.</p>
                </div>
              ) : (
                <div className="space-y-3 pt-1">
                  {items.map((item, idx) => {
                    const isEditing = editingId === item.id;
                    const isEdited =
                      !item.isNew && !item.deleted && item.text !== item.originalText;
                    const isKept = !item.deleted && !item.isNew && !isEdited;

                    return (
                      <div
                        key={item.id}
                        className={`p-5 rounded-2xl border transition-all duration-300 flex items-start gap-4 shadow-lg group
                          ${item.deleted
                            ? "bg-red-500/5 border-red-500/20 opacity-50"
                            : isEdited
                            ? "bg-amber-500/5 border-amber-400/30 hover:border-amber-400/50"
                            : item.isNew
                            ? "bg-purple-500/8 border-purple-400/30 hover:border-purple-400/50"
                            : isEditing
                            ? "bg-cyan-500/10 border-cyan-400/40"
                            : "bg-white/5 hover:bg-cyan-500/10 border-white/10 hover:border-cyan-400/40"}`}
                      >
                        {/* Status Icon */}
                        <div
                          className={`mt-0.5 shrink-0 flex items-center justify-center h-6 w-6 rounded-full font-bold text-xs
                          ${item.deleted
                            ? "bg-red-500/20 text-red-400"
                            : item.isNew
                            ? "bg-purple-500/20 text-purple-300"
                            : isEdited
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-emerald-500/20 text-emerald-300"}`}
                        >
                          {item.deleted ? <Trash2 size={11} /> : isKept ? <CheckCheck size={12} /> : idx + 1}
                        </div>

                        <div className="flex-1 min-w-0">
                          {isEditing ? (
                            <textarea
                              autoFocus
                              rows={3}
                              value={editingText}
                              onChange={(e) => setEditingText(e.target.value)}
                              className="w-full bg-transparent text-sm text-white resize-none focus:outline-none leading-relaxed border-b border-cyan-400/40 pb-1"
                              onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                  e.preventDefault();
                                  saveEdit(item.id);
                                }
                                if (e.key === "Escape") cancelEdit();
                              }}
                            />
                          ) : (
                            <p
                              className={`text-sm leading-relaxed ${
                                item.deleted
                                  ? "line-through text-gray-500"
                                  : "text-gray-100"
                              }`}
                            >
                              {item.text}
                            </p>
                          )}

                          {/* Action Badges */}
                          <div className="flex items-center gap-2 mt-2 flex-wrap">
                            {isKept && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/20">
                                KEEP
                              </span>
                            )}
                            {item.isNew && !item.deleted && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-400/20">
                                ADD
                              </span>
                            )}
                            {isEdited && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-400/20">
                                EDITED
                              </span>
                            )}
                            {item.deleted && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-400/20">
                                DELETE
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div
                          className={`flex items-center gap-1.5 shrink-0 transition-opacity duration-200 ${
                            isEditing ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                          }`}
                        >
                          {isEditing ? (
                            <>
                              <button
                                onClick={() => saveEdit(item.id)}
                                className="p-2 rounded-xl bg-cyan-600/80 hover:bg-cyan-500 text-white transition cursor-pointer"
                                title="Save"
                              >
                                <Save size={14} />
                              </button>
                              <button
                                onClick={cancelEdit}
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 transition cursor-pointer"
                                title="Cancel"
                              >
                                <X size={14} />
                              </button>
                            </>
                          ) : (
                            <>
                              {/* Keep / Revert button for edited or deleted items */}
                              {(isEdited || item.deleted) && (
                                <button
                                  onClick={() => handleKeep(item.id)}
                                  className="p-2 rounded-xl bg-white/5 hover:bg-emerald-500/20 hover:text-emerald-300 text-gray-400 transition cursor-pointer"
                                  title="Keep Original (Revert to Keep)"
                                >
                                  <RotateCcw size={14} />
                                </button>
                              )}

                              {!item.deleted && (
                                <button
                                  onClick={() => startEdit(item)}
                                  className="p-2 rounded-xl bg-white/5 hover:bg-cyan-500/20 hover:text-cyan-300 text-gray-400 transition cursor-pointer"
                                  title="Edit Requirement"
                                >
                                  <Pencil size={14} />
                                </button>
                              )}

                              {!item.deleted ? (
                                <button
                                  onClick={() => toggleDelete(item.id)}
                                  className="p-2 rounded-xl bg-white/5 hover:bg-red-500/20 hover:text-red-400 text-gray-400 transition cursor-pointer"
                                  title="Delete Requirement"
                                >
                                  <Trash2 size={14} />
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleKeep(item.id)}
                                  className="p-2 rounded-xl bg-white/5 hover:bg-emerald-500/20 hover:text-emerald-300 text-gray-400 transition cursor-pointer"
                                  title="Restore Requirement"
                                >
                                  <RotateCcw size={14} />
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* ACTION BAR */}
            <div className="p-6 rounded-3xl bg-[#0f172a]/95 border border-cyan-500/40 shadow-2xl backdrop-blur-xl flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="p-3.5 rounded-2xl bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">
                  <ShieldCheck size={26} />
                </div>
                <div>
                  <h4 className="font-bold text-white text-base">Ready to proceed?</h4>
                  <p className="text-xs text-gray-400">
                    Review your changes, then submit to analyze and reconcile.
                  </p>
                </div>
              </div>
              <button
                onClick={handleSubmitReview}
                disabled={loading}
                className="w-full md:w-auto flex items-center justify-center gap-2 px-10 py-3.5 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider shadow-[0_0_25px_rgba(34,211,238,0.4)] transition duration-300 cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Analyzing Changes...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={18} />
                    Submit Review
                  </>
                )}
              </button>
            </div>
          </>
        )}

        {/* STAGE 2: TARGETED CLARIFICATION QUESTIONS */}
        {stage === "questions" && (
          <div className="p-8 rounded-3xl bg-[#0f172a]/90 border border-amber-500/30 shadow-2xl backdrop-blur-xl space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-400/30">
                  <HelpCircle size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Clarification Required</h3>
                  <p className="text-xs text-gray-400">
                    Please answer the questions below to finalize requirement details
                  </p>
                </div>
              </div>
              <span className="text-xs font-semibold text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-400/20">
                {questions.length} Questions
              </span>
            </div>

            <div className="space-y-6 pt-2">
              {questions.map((q, idx) => (
                <div
                  key={q.id || idx}
                  className="p-6 rounded-2xl bg-white/5 border border-white/10 space-y-4 shadow-lg hover:border-amber-400/30 transition-all"
                >
                  <div className="flex items-start gap-3">
                    <div className="shrink-0 h-6 w-6 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center font-bold text-xs">
                      {idx + 1}
                    </div>
                    <div className="space-y-1">
                      <h4 className="text-sm font-semibold text-white leading-relaxed">
                        {q.question}
                      </h4>
                      {q.reason && (
                        <p className="text-xs text-amber-300/80 leading-relaxed">
                          Context: {q.reason}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="pl-9">
                    <textarea
                      rows={3}
                      value={answers[q.id] || ""}
                      onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                      placeholder="Type your answer here..."
                      className="w-full p-4 rounded-xl bg-black/40 border border-white/10 text-white text-sm focus:border-amber-400 focus:outline-none transition resize-none placeholder-gray-500"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/10">
              <button
                onClick={() => setStage("review")}
                className="px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-semibold transition cursor-pointer"
              >
                Back to Review
              </button>
              <button
                onClick={handleSubmitAnswers}
                disabled={loading}
                className="flex items-center gap-2 px-8 py-3.5 rounded-full bg-gradient-to-r from-amber-500 to-emerald-600 hover:from-amber-400 hover:to-emerald-500 text-white font-bold text-xs uppercase tracking-wider shadow-[0_0_25px_rgba(245,158,11,0.4)] transition duration-300 cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Reconciling...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Submit Clarifications
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* STAGE 3: COMPLETED */}
        {stage === "completed" && (
          <div className="p-12 rounded-3xl bg-[#0f172a]/90 border border-emerald-500/40 shadow-2xl backdrop-blur-xl text-center space-y-6">
            <div className="h-16 w-16 mx-auto rounded-full bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center text-emerald-400">
              <CheckCircle2 size={36} />
            </div>
            <div className="space-y-2">
              <h3 className="text-2xl font-bold text-white">Review &amp; Clarification Complete</h3>
              <p className="text-gray-400 text-sm max-w-md mx-auto">
                All client changes have been validated, questions answered, and final requirements reconciled into the project.
              </p>
            </div>
            <button
              onClick={() => navigate("/client-dashboard")}
              className="px-8 py-3.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs uppercase tracking-wider transition cursor-pointer shadow-lg"
            >
              Return to Dashboard
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
