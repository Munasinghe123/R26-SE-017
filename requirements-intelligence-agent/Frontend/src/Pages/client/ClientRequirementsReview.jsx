import React, { useEffect, useState } from "react";
import { ArrowLeft, Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api/api";

export default function ClientRequirementsReview() {
  const { threadId } = useParams();
  const navigate = useNavigate();

  // ---------------------------------------------------------
  // STATE
  // ---------------------------------------------------------

  const [requirements, setRequirements] = useState([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState("");

  const [newRequirement, setNewRequirement] = useState("");

  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});

  const [showQuestions, setShowQuestions] = useState(false);

  // ---------------------------------------------------------
  // API ERROR HANDLER
  // ---------------------------------------------------------

  const getApiErrorMessage = (error, fallback) => {
    const detail = error?.response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") {
            return item;
          }

          return item?.msg || "Validation error";
        })
        .join(", ");
    }

    if (typeof detail === "string") {
      return detail;
    }

    return fallback;
  };

  // ---------------------------------------------------------
  // LOAD REQUIREMENTS
  // ---------------------------------------------------------

  useEffect(() => {
    const fetchReview = async () => {
      if (!threadId) {
        setError("No review thread was provided.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // IMPORTANT:
        // Loading an existing review is GET, not POST.
        const response = await api.get(`/meetings/${threadId}/review`);

        const sections = response.data?.client_view?.sections || [];

        const items = sections.flatMap((section) => section.items || []);

        setRequirements(items);
      } catch (err) {
        console.error("Failed to load requirements:", err);

        setError(getApiErrorMessage(err, "Failed to load requirements."));
      } finally {
        setLoading(false);
      }
    };

    fetchReview();
  }, [threadId]);

  // ---------------------------------------------------------
  // KEEP
  // ---------------------------------------------------------

  const handleKeep = (id) => {
    setRequirements((prev) =>
      prev.map((requirement) =>
        requirement.id === id
          ? {
              ...requirement,
              reviewAction: "keep",
            }
          : requirement,
      ),
    );
  };

  // ---------------------------------------------------------
  // EDIT
  // ---------------------------------------------------------

  const startEdit = (requirement) => {
    setEditingId(requirement.id);
    setEditingText(requirement.text);
    setError(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingText("");
  };

  const saveEdit = (id) => {
    const text = editingText.trim();

    if (!text) {
      setError("Requirement text cannot be empty.");
      return;
    }

    setRequirements((prev) =>
      prev.map((requirement) =>
        requirement.id === id
          ? {
              ...requirement,
              text,
              reviewAction: "edit",
            }
          : requirement,
      ),
    );

    cancelEdit();
    setError(null);
  };

  // ---------------------------------------------------------
  // DELETE
  // ---------------------------------------------------------

  const handleDelete = (id) => {
    setRequirements((prev) =>
      prev.map((requirement) =>
        requirement.id === id
          ? {
              ...requirement,
              reviewAction: "delete",
            }
          : requirement,
      ),
    );

    setError(null);
  };

  // ---------------------------------------------------------
  // RESTORE
  // ---------------------------------------------------------

  const handleRestore = (id) => {
    setRequirements((prev) =>
      prev.map((requirement) =>
        requirement.id === id
          ? {
              ...requirement,
              reviewAction: "keep",
            }
          : requirement,
      ),
    );

    setError(null);
  };

  // ---------------------------------------------------------
  // ADD REQUIREMENT
  // ---------------------------------------------------------

  const handleAdd = () => {
    const text = newRequirement.trim();

    if (!text) {
      return;
    }

    const newItem = {
      id: `new-${Date.now()}`,
      text,
      reviewAction: "add",
    };

    setRequirements((prev) => [...prev, newItem]);

    setNewRequirement("");
    setError(null);
  };

  // ---------------------------------------------------------
  // SUBMIT REVIEW
  // ---------------------------------------------------------

  const handleSubmitReview = async () => {
    if (submitting) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const changes = requirements
        .filter((requirement) => requirement.reviewAction)
        .map((requirement) => ({
          id: requirement.id,
          action: requirement.reviewAction,
          text: requirement.reviewAction === "delete" ? "" : requirement.text,
        }));

      console.log("========== CLIENT REVIEW SUBMISSION ==========");

      console.log("THREAD ID:", threadId);
      console.log("ITEMS:", changes);

      // 1. Submit requirement review
      await api.post(`/meetings/${threadId}/review`, {
        items: changes,
      });

      console.log("Client review submitted successfully.");

      // 2. Fetch clarification questions
      const questionResponse = await api.get(`/meetings/${threadId}/questions`);

      const targetedQuestions = questionResponse.data?.questions || [];

      console.log("========== TARGETED QUESTIONS ==========");

      console.log(targetedQuestions);

      // 3. Show questions
      if (targetedQuestions.length > 0) {
        setQuestions(targetedQuestions);
        setShowQuestions(true);
      } else {
        console.log("No clarification questions generated.");

        navigate(-1);
      }
    } catch (err) {
      console.error("Failed to submit review:", err);

      setError(
        getApiErrorMessage(err, "Failed to submit requirements review."),
      );
    } finally {
      setSubmitting(false);
    }
  };

  // ---------------------------------------------------------
  // ANSWER QUESTION
  // ---------------------------------------------------------

  const handleAnswerChange = (questionId, answer) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  };

  // ---------------------------------------------------------
  // SUBMIT ANSWERS
  // ---------------------------------------------------------

  const handleSubmitAnswers = async () => {
    if (submitting) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        answers: questions.map((question) => ({
          question_id: question.id,
          requirement_id: question.requirement_id,
          answer: answers[question.id] || "",
        })),
      };

      console.log("========== CLIENT ANSWERS ==========");

      console.log("THREAD ID:", threadId);
      console.log("PAYLOAD:", payload);

      console.log("====================================");

      await api.post(`/meetings/${threadId}/questions/answers`, payload);

      console.log("Client answers submitted successfully.");

      navigate(-1);
    } catch (err) {
      console.error("Failed to submit answers:", err);

      setError(getApiErrorMessage(err, "Failed to submit client answers."));
    } finally {
      setSubmitting(false);
    }
  };

  // ---------------------------------------------------------
  // LOADING
  // ---------------------------------------------------------

  if (loading) {
    return (
      <div
        className="
          flex
          h-screen
          w-full
          items-center
          justify-center
          bg-[#080A14]
          text-cyan-300
        "
      >
        <div className="flex flex-col items-center gap-4">
          <div
            className="
              h-8
              w-8
              animate-spin
              rounded-full
              border-2
              border-cyan-400/20
              border-t-cyan-300
            "
          />

          <p className="text-sm tracking-wide">Loading requirements...</p>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------
  // ERROR WITH NO REQUIREMENTS
  // ---------------------------------------------------------

  if (error && requirements.length === 0) {
    return (
      <div
        className="
          flex
          h-screen
          w-full
          items-center
          justify-center
          bg-[#080A14]
          text-white
        "
      >
        <div className="text-center">
          <p className="mb-5 text-red-400">{error}</p>

          <button
            onClick={() => navigate(-1)}
            className="
              rounded-full
              border
              border-white/20
              px-5
              py-3
              text-sm
              text-white/70
              transition
              hover:border-cyan-400
              hover:text-cyan-300
            "
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------
  // QUESTIONS SCREEN
  // ---------------------------------------------------------

  if (showQuestions) {
    return (
      <div
        className="
          min-h-screen
          w-full
          overflow-y-auto
          bg-[#080A14]
          px-6
          py-10
          text-white
        "
      >
        <div className="mx-auto max-w-4xl">
          {/* BACK */}

          <button
            onClick={() => setShowQuestions(false)}
            className="
              mb-8
              flex
              items-center
              gap-2
              text-sm
              text-white/50
              transition
              hover:text-cyan-300
            "
          >
            <ArrowLeft size={17} />
            Back to requirements
          </button>

          {/* HEADER */}

          <div className="mb-10">
            <p
              className="
                mb-2
                text-sm
                uppercase
                tracking-[3px]
                text-cyan-300
              "
            >
              Clarification
            </p>

            <h1
              className="
                text-4xl
                font-bold
              "
            >
              We need your input
            </h1>

            <p
              className="
                mt-3
                text-white/50
              "
            >
              Please answer the following questions so we can finalize the
              requirements.
            </p>
          </div>

          {/* QUESTIONS */}

          <div className="space-y-6">
            {questions.map((question, index) => (
              <div
                key={question.id}
                className="
                    rounded-2xl
                    border
                    border-white/10
                    bg-white/[0.03]
                    p-6
                  "
              >
                <div
                  className="
                      mb-4
                      flex
                      items-center
                      justify-between
                    "
                >
                  <span
                    className="
                        text-xs
                        uppercase
                        tracking-[2px]
                        text-cyan-300
                      "
                  >
                    Question {index + 1}
                  </span>

                  <span
                    className="
                        text-xs
                        text-white/30
                      "
                  >
                    {question.requirement_id}
                  </span>
                </div>

                <p
                  className="
                      mb-5
                      text-lg
                      leading-relaxed
                      text-white
                    "
                >
                  {question.question}
                </p>

                <textarea
                  value={answers[question.id] || ""}
                  onChange={(e) =>
                    handleAnswerChange(question.id, e.target.value)
                  }
                  placeholder="Enter your answer..."
                  rows={4}
                  className="
                      w-full
                      resize-none
                      rounded-xl
                      border
                      border-white/10
                      bg-black/30
                      p-4
                      text-white
                      outline-none
                      placeholder:text-white/25
                      focus:border-cyan-400/50
                    "
                />
              </div>
            ))}
          </div>

          {/* ERROR */}

          {error && (
            <p
              className="
                mt-6
                text-sm
                text-red-400
              "
            >
              {error}
            </p>
          )}

          {/* SUBMIT ANSWERS */}

          <div
            className="
              mt-8
              flex
              justify-end
            "
          >
            <button
              onClick={handleSubmitAnswers}
              disabled={submitting}
              className="
                rounded-full
                border
                border-cyan-400/60
                bg-black
                px-7
                py-3.5
                text-sm
                font-medium
                uppercase
                tracking-[2px]
                text-cyan-300
                transition
                hover:border-cyan-200
                hover:text-white
                disabled:cursor-not-allowed
                disabled:opacity-40
              "
            >
              {submitting ? "Submitting..." : "Submit Answers"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------
  // REQUIREMENTS SCREEN
  // ---------------------------------------------------------

  return (
    <div
      className="
        min-h-screen
        w-full
        overflow-y-auto
        bg-[#080A14]
        px-6
        py-10
        text-white
      "
    >
      <div className="mx-auto max-w-5xl">
        {/* =====================================================
            HEADER
        ===================================================== */}

        <div
          className="
            mb-10
            flex
            items-start
            justify-between
          "
        >
          <div>
            <button
              onClick={() => navigate(-1)}
              className="
                mb-5
                flex
                items-center
                gap-2
                text-sm
                text-white/50
                transition
                hover:text-cyan-300
              "
            >
              <ArrowLeft size={17} />
              Back to dashboard
            </button>

            <p
              className="
                mb-2
                text-sm
                uppercase
                tracking-[3px]
                text-cyan-300
              "
            >
              Client Review
            </p>

            <h1
              className="
                text-4xl
                font-bold
              "
            >
              Review Requirements
            </h1>

            <p
              className="
                mt-3
                max-w-2xl
                text-white/50
              "
            >
              Review the generated requirements. Keep, edit, delete, or add
              requirements before submitting your review.
            </p>
          </div>
        </div>

        {/* =====================================================
            REQUIREMENTS
        ===================================================== */}

        <div className="space-y-4">
          {requirements.map((requirement, index) => {
            const deleted = requirement.reviewAction === "delete";

            const action = requirement.reviewAction;

            const kept = action === "keep";

            const edited = action === "edit";

            const added = action === "add";

            return (
              <div
                key={requirement.id}
                className={`
                    rounded-2xl
                    border
                    p-5
                    transition-all
                    duration-200

                    ${
                      deleted
                        ? `
                          border-red-400/20
                          bg-red-400/[0.04]
                          opacity-60
                        `
                        : kept
                          ? `
                          border-green-400/30
                          bg-green-400/[0.04]
                        `
                          : edited
                            ? `
                          border-yellow-400/30
                          bg-yellow-400/[0.04]
                        `
                            : added
                              ? `
                          border-cyan-400/30
                          bg-cyan-400/[0.04]
                        `
                              : `
                          border-white/10
                          bg-white/[0.03]
                        `
                    }
                  `}
              >
                <div
                  className="
                      flex
                      gap-5
                    "
                >
                  {/* =================================================
                        NUMBER
                    ================================================= */}

                  <div
                    className="
                        flex
                        h-9
                        w-9
                        shrink-0
                        items-center
                        justify-center
                        rounded-full
                        bg-white/5
                        text-xs
                        text-white/40
                      "
                  >
                    {index + 1}
                  </div>

                  {/* =================================================
                        CONTENT
                    ================================================= */}

                  <div
                    className="
                        min-w-0
                        flex-1
                      "
                  >
                    {/* ID + STATUS */}

                    <div
                      className="
                          mb-3
                          flex
                          flex-wrap
                          items-center
                          gap-3
                        "
                    >
                      <span
                        className="
                            rounded-full
                            border
                            border-cyan-400/20
                            bg-cyan-400/5
                            px-3
                            py-1
                            text-xs
                            text-cyan-300
                          "
                      >
                        {requirement.id}
                      </span>

                      {/* KEPT */}

                      {kept && (
                        <span
                          className="
                              flex
                              items-center
                              gap-1.5
                              text-xs
                              font-medium
                              text-green-300
                            "
                        >
                          <Check size={13} />
                          Kept
                        </span>
                      )}

                      {/* EDITED */}

                      {edited && (
                        <span
                          className="
                              flex
                              items-center
                              gap-1.5
                              text-xs
                              font-medium
                              text-yellow-300
                            "
                        >
                          <Pencil size={13} />
                          Edited
                        </span>
                      )}

                      {/* DELETED */}

                      {deleted && (
                        <span
                          className="
                              flex
                              items-center
                              gap-1.5
                              text-xs
                              font-medium
                              text-red-400
                            "
                        >
                          <Trash2 size={13} />
                          Marked for deletion
                        </span>
                      )}

                      {/* ADDED */}

                      {added && (
                        <span
                          className="
                              flex
                              items-center
                              gap-1.5
                              text-xs
                              font-medium
                              text-cyan-300
                            "
                        >
                          <Plus size={13} />
                          New
                        </span>
                      )}
                    </div>

                    {/* =================================================
                          EDIT MODE
                      ================================================= */}

                    {editingId === requirement.id ? (
                      <div>
                        <textarea
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                          rows={3}
                          className="
                              w-full
                              resize-none
                              rounded-xl
                              border
                              border-cyan-400/30
                              bg-black/30
                              p-4
                              text-white
                              outline-none
                              focus:border-cyan-400/60
                            "
                        />

                        <div
                          className="
                              mt-3
                              flex
                              gap-3
                            "
                        >
                          <button
                            onClick={() => saveEdit(requirement.id)}
                            className="
                                flex
                                items-center
                                gap-2
                                rounded-full
                                border
                                border-green-400/30
                                px-4
                                py-2
                                text-xs
                                text-green-300
                                transition
                                hover:border-green-400
                                hover:bg-green-400/5
                              "
                          >
                            <Check size={14} />
                            Save
                          </button>

                          <button
                            onClick={cancelEdit}
                            className="
                                flex
                                items-center
                                gap-2
                                rounded-full
                                border
                                border-white/10
                                px-4
                                py-2
                                text-xs
                                text-white/50
                                transition
                                hover:border-white/30
                                hover:text-white
                              "
                          >
                            <X size={14} />
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p
                        className={`
                            text-base
                            leading-relaxed

                            ${
                              deleted
                                ? `
                                  text-white/30
                                  line-through
                                `
                                : `
                                  text-white/80
                                `
                            }
                          `}
                      >
                        {requirement.text}
                      </p>
                    )}
                  </div>

                  {/* =================================================
                        ACTIONS
                    ================================================= */}

                  {editingId !== requirement.id && !deleted && (
                    <div
                      className="
                            flex
                            shrink-0
                            items-start
                            gap-2
                          "
                    >
                      {/* KEEP */}

                      <button
                        onClick={() => handleKeep(requirement.id)}
                        title="Keep"
                        className={`
                              rounded-lg
                              border
                              p-2
                              transition

                              ${
                                kept
                                  ? `
                                    border-green-400
                                    bg-green-400/10
                                    text-green-300
                                  `
                                  : `
                                    border-green-400/20
                                    text-green-300/70
                                    hover:border-green-400
                                    hover:bg-green-400/5
                                    hover:text-green-300
                                  `
                              }
                            `}
                      >
                        <Check size={16} />
                      </button>

                      {/* EDIT */}

                      <button
                        onClick={() => startEdit(requirement)}
                        title="Edit"
                        className={`
                              rounded-lg
                              border
                              p-2
                              transition

                              ${
                                edited
                                  ? `
                                    border-yellow-400
                                    bg-yellow-400/10
                                    text-yellow-300
                                  `
                                  : `
                                    border-yellow-400/20
                                    text-yellow-300/70
                                    hover:border-yellow-400
                                    hover:bg-yellow-400/5
                                    hover:text-yellow-300
                                  `
                              }
                            `}
                      >
                        <Pencil size={16} />
                      </button>

                      {/* DELETE */}

                      <button
                        onClick={() => handleDelete(requirement.id)}
                        title="Delete"
                        className="
                              rounded-lg
                              border
                              border-red-400/20
                              p-2
                              text-red-300/70
                              transition
                              hover:border-red-400
                              hover:bg-red-400/5
                              hover:text-red-300
                            "
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}

                  {/* =================================================
                        RESTORE
                    ================================================= */}

                  {deleted && (
                    <button
                      onClick={() => handleRestore(requirement.id)}
                      className="
                          shrink-0
                          rounded-full
                          border
                          border-white/10
                          px-4
                          py-2
                          text-xs
                          text-white/50
                          transition
                          hover:border-green-400/40
                          hover:text-green-300
                        "
                    >
                      Restore
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* =====================================================
            ADD REQUIREMENT
        ===================================================== */}

        <div
          className="
            mt-8
            rounded-2xl
            border
            border-dashed
            border-white/10
            bg-white/[0.02]
            p-5
          "
        >
          <div
            className="
              mb-4
              flex
              items-center
              gap-2
            "
          >
            <Plus size={18} className="text-cyan-300" />

            <span
              className="
                text-sm
                font-medium
                text-white/70
              "
            >
              Add Requirement
            </span>
          </div>

          <div
            className="
              flex
              gap-3
            "
          >
            <input
              value={newRequirement}
              onChange={(e) => setNewRequirement(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleAdd();
                }
              }}
              placeholder="Enter a new requirement..."
              className="
                flex-1
                rounded-xl
                border
                border-white/10
                bg-black/30
                px-4
                py-3
                text-sm
                text-white
                outline-none
                placeholder:text-white/25
                focus:border-cyan-400/40
              "
            />

            <button
              onClick={handleAdd}
              disabled={!newRequirement.trim()}
              className="
                rounded-xl
                border
                border-cyan-400/40
                px-5
                text-cyan-300
                transition
                hover:bg-cyan-400/10
                disabled:cursor-not-allowed
                disabled:opacity-30
              "
            >
              <Plus size={18} />
            </button>
          </div>
        </div>

        {/* =====================================================
            ERROR
        ===================================================== */}

        {error && (
          <div
            className="
              mt-5
              rounded-xl
              border
              border-red-400/20
              bg-red-400/[0.04]
              px-4
              py-3
            "
          >
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* =====================================================
            SUBMIT
        ===================================================== */}

        <div
          className="
            mt-8
            flex
            justify-end
          "
        >
          <button
            onClick={handleSubmitReview}
            disabled={submitting}
            className="
              flex
              items-center
              gap-3
              rounded-full
              border
              border-cyan-400/60
              bg-black
              px-8
              py-3.5
              text-sm
              font-medium
              uppercase
              tracking-[2px]
              text-cyan-300
              transition-all
              hover:border-cyan-200
              hover:text-white
              hover:shadow-[0_0_20px_rgba(34,211,238,0.3)]
              disabled:cursor-not-allowed
              disabled:opacity-40
            "
          >
            {submitting && (
              <span
                className="
                  h-4
                  w-4
                  animate-spin
                  rounded-full
                  border-2
                  border-cyan-300/30
                  border-t-cyan-300
                "
              />
            )}

            {submitting ? "Submitting Review..." : "Submit Review"}
          </button>
        </div>
      </div>
    </div>
  );
}
