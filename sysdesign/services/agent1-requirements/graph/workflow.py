from langgraph.graph import StateGraph, END
from graph.state import GraphState, checkpointer as default_checkpointer
from graph.nodes import (
    speech_enhancement_node,
    transcribe_node,
    diarization_node,
    speaker_alignment_node,
    role_identification_node,
    transcript_cleaning_node,
    document_node,
    extraction_node,
    reclassify_requirements_node,
    client_view_node,
    await_client_node,
    process_client_review_node,
    analyze_client_changes_node,
    partition_client_changes_node,
    generate_targeted_questions_node,
    await_client_questions_node,
    apply_client_answers_node,
    collect_new_requirements_node,
    classify_new_requirements_node,
    validate_new_requirement_format_node,
    normalize_new_requirements_node,
    reconcile_requirements_node,
    refine_node,
    generate_srs_pdf_node,
)
from graph.router import route_workflow


def route_after_partition(state: GraphState):
    clarifications = state.get("clarification_changes") or {}
    total = sum(
        len(clarifications.get(k, []))
        for k in ("edited", "deleted", "added")
    )
    if total > 0:
        return "generate_targeted_questions"
    return "collect_new_requirements"


def build_graph(checkpointer=None):
    builder = StateGraph(GraphState)

    # ── nodes ──────────────────────────────────────────────
    builder.add_node("router", lambda state: state)
    builder.add_node("enhance", speech_enhancement_node)
    builder.add_node("transcribe", transcribe_node)
    builder.add_node("diarize", diarization_node)
    builder.add_node("speaker_alignment", speaker_alignment_node)
    builder.add_node("role_identification", role_identification_node)
    builder.add_node("transcript_cleaning", transcript_cleaning_node)
    builder.add_node("document", document_node)
    builder.add_node("extract", extraction_node)
    builder.add_node("reclassify_requirements", reclassify_requirements_node)
    builder.add_node("client_view", client_view_node)
    builder.add_node("await_client", await_client_node)
    builder.add_node("process_client_review", process_client_review_node)
    builder.add_node("analyze_client_changes", analyze_client_changes_node)
    builder.add_node("partition_client_changes", partition_client_changes_node)
    builder.add_node("generate_targeted_questions", generate_targeted_questions_node)
    builder.add_node("await_client_questions", await_client_questions_node)
    builder.add_node("apply_client_answers", apply_client_answers_node)
    builder.add_node("collect_new_requirements", collect_new_requirements_node)
    builder.add_node("classify_new_requirements", classify_new_requirements_node)
    builder.add_node("validate_new_requirement_format", validate_new_requirement_format_node)
    builder.add_node("normalize_new_requirements", normalize_new_requirements_node)
    builder.add_node("reconcile_requirements", reconcile_requirements_node)
    # builder.add_node("build_srs", build_srs_node)
    builder.add_node("generate_pdf", generate_srs_pdf_node)

    # ── entry ──────────────────────────────────────────────
    builder.set_entry_point("router")
    builder.add_conditional_edges("router", route_workflow)

    # ── audio path ─────────────────────────────────────────
    builder.add_edge("enhance", "transcribe")
    builder.add_edge("transcribe", "diarize")
    builder.add_edge("diarize", "speaker_alignment")
    builder.add_edge("speaker_alignment", "role_identification")
    builder.add_edge("role_identification", "transcript_cleaning")
    builder.add_edge("transcript_cleaning", "extract")

    # ── document path ──────────────────────────────────────
    builder.add_edge("document", "extract")

    # ── common: extract → client view ──────────────────────
    builder.add_edge("extract", "reclassify_requirements")
    builder.add_edge("reclassify_requirements", "client_view")
    builder.add_edge("client_view", "await_client")

    # ── HITL: client review ────────────────────────────────
    builder.add_edge("await_client", "process_client_review")
    builder.add_edge("process_client_review", "analyze_client_changes")
    builder.add_edge("analyze_client_changes", "partition_client_changes")
    
    # Conditional branching: only generate questions if clarification is needed
    builder.add_conditional_edges(
        "partition_client_changes",
        route_after_partition,
        {
            "generate_targeted_questions": "generate_targeted_questions",
            "collect_new_requirements": "collect_new_requirements"
        }
    )

    # ── HITL: Q&A (only if questions needed) ────────────────
    builder.add_edge("generate_targeted_questions", "await_client_questions")
    builder.add_edge("await_client_questions", "apply_client_answers")
    builder.add_edge("apply_client_answers", "collect_new_requirements")

    # ── new requirements pipeline ──────────────────────────
    builder.add_edge("collect_new_requirements", "classify_new_requirements")
    builder.add_edge("classify_new_requirements", "validate_new_requirement_format")
    builder.add_edge("validate_new_requirement_format", "normalize_new_requirements")
    builder.add_edge("normalize_new_requirements", "reconcile_requirements")
    builder.add_edge("reconcile_requirements", END)

    # ── srs (optional) ─────────────────────────────────────
    # builder.add_edge("build_srs", "generate_pdf")
    builder.add_edge("generate_pdf", END)

    saver = checkpointer or default_checkpointer
    return builder.compile(checkpointer=saver)
