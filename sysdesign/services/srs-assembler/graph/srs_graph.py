from __future__ import annotations

import json
from typing import Literal

from langgraph.graph import END, START, StateGraph

from services.artifact_repair import ArtifactRepairConfig, ArtifactRepairService
from graph.prompts import (
    build_overview_prompt,
    build_functional_prompt,
    build_non_functional_prompt,
    build_traceability_prompt,
)
from graph.srs_state import (
    SRSConfig,
    SRSState,
    SRSGraphState,
    StageName,
    MAX_REPAIR_ATTEMPTS,
    record_stage_metrics,
    record_repair_metrics,
    all_stage_validations_passed,
)
from llm.provider import LLMProvider, LLMResponse
from utils.json_cleaner import clean_json_response
from utils.markdown_renderer import render_ieee_29148_markdown
from validators.stage_validators import (
    validate_overview_section,
    validate_functional_requirements,
    validate_non_functional_requirements,
    validate_traceability_matrix,
)
from utils.logger import (
    log_stage_start,
    log_stage_llm_done,
    log_stage_validation,
    log_repair_start,
    log_repair_result,
    log_stage_error,
    log_compiling_markdown,
)

RouteName = Literal[
    "mark_failed",
    "validate_overview",
    "validate_functional",
    "validate_nfr",
    "validate_traceability",
    "repair_overview",
    "repair_functional",
    "repair_nfr",
    "repair_traceability",
    "generate_functional",
    "generate_nfr",
    "generate_traceability",
    "assemble_final_srs",
]


def build_srs_graph():
    graph = StateGraph(SRSGraphState)

    # 1. Overview Stage Nodes
    graph.add_node("generate_overview", _generate_overview)
    graph.add_node("parse_overview", _parse_overview)
    graph.add_node("validate_overview", _validate_overview)
    graph.add_node("repair_overview", _repair_overview)

    # 2. Functional Stage Nodes
    graph.add_node("generate_functional", _generate_functional)
    graph.add_node("parse_functional", _parse_functional)
    graph.add_node("validate_functional", _validate_functional)
    graph.add_node("repair_functional", _repair_functional)

    # 3. Non-Functional Stage Nodes
    graph.add_node("generate_nfr", _generate_nfr)
    graph.add_node("parse_nfr", _parse_nfr)
    graph.add_node("validate_nfr", _validate_nfr)
    graph.add_node("repair_nfr", _repair_nfr)

    # 4. Traceability Stage Nodes
    graph.add_node("generate_traceability", _generate_traceability)
    graph.add_node("parse_traceability", _parse_traceability)
    graph.add_node("validate_traceability", _validate_traceability)
    graph.add_node("repair_traceability", _repair_traceability)

    # 5. Terminal Nodes
    graph.add_node("assemble_final_srs", _assemble_final_srs)
    graph.add_node("mark_failed", _mark_failed)

    # --- Edges: Overview ---
    graph.add_edge(START, "generate_overview")
    graph.add_conditional_edges(
        "generate_overview",
        _route_after_generation("overview", "parse_overview"),
        {"mark_failed": "mark_failed", "parse_overview": "parse_overview"},
    )
    graph.add_conditional_edges(
        "parse_overview",
        _route_after_parse("overview", "validate_overview"),
        {"mark_failed": "mark_failed", "validate_overview": "validate_overview"},
    )
    graph.add_conditional_edges(
        "validate_overview",
        _route_after_validation("overview", "repair_overview", "generate_functional"),
        {"repair_overview": "repair_overview", "generate_functional": "generate_functional"},
    )
    graph.add_conditional_edges(
        "repair_overview",
        _route_after_repair("overview", "validate_overview", "generate_functional"),
        {"validate_overview": "validate_overview", "generate_functional": "generate_functional"},
    )

    # --- Edges: Functional ---
    graph.add_conditional_edges(
        "generate_functional",
        _route_after_generation("functional", "parse_functional"),
        {"mark_failed": "mark_failed", "parse_functional": "parse_functional"},
    )
    graph.add_conditional_edges(
        "parse_functional",
        _route_after_parse("functional", "validate_functional"),
        {"mark_failed": "mark_failed", "validate_functional": "validate_functional"},
    )
    graph.add_conditional_edges(
        "validate_functional",
        _route_after_validation("functional", "repair_functional", "generate_nfr"),
        {"repair_functional": "repair_functional", "generate_nfr": "generate_nfr"},
    )
    graph.add_conditional_edges(
        "repair_functional",
        _route_after_repair("functional", "validate_functional", "generate_nfr"),
        {"validate_functional": "validate_functional", "generate_nfr": "generate_nfr"},
    )

    # --- Edges: Non-Functional ---
    graph.add_conditional_edges(
        "generate_nfr",
        _route_after_generation("non_functional", "parse_nfr"),
        {"mark_failed": "mark_failed", "parse_nfr": "parse_nfr"},
    )
    graph.add_conditional_edges(
        "parse_nfr",
        _route_after_parse("non_functional", "validate_nfr"),
        {"mark_failed": "mark_failed", "validate_nfr": "validate_nfr"},
    )
    graph.add_conditional_edges(
        "validate_nfr",
        _route_after_validation("non_functional", "repair_nfr", "generate_traceability"),
        {"repair_nfr": "repair_nfr", "generate_traceability": "generate_traceability"},
    )
    graph.add_conditional_edges(
        "repair_nfr",
        _route_after_repair("non_functional", "validate_nfr", "generate_traceability"),
        {"validate_nfr": "validate_nfr", "generate_traceability": "generate_traceability"},
    )

    # --- Edges: Traceability ---
    graph.add_conditional_edges(
        "generate_traceability",
        _route_after_generation("traceability", "parse_traceability"),
        {"mark_failed": "mark_failed", "parse_traceability": "parse_traceability"},
    )
    graph.add_conditional_edges(
        "parse_traceability",
        _route_after_parse("traceability", "validate_traceability"),
        {"mark_failed": "mark_failed", "validate_traceability": "validate_traceability"},
    )
    graph.add_conditional_edges(
        "validate_traceability",
        _route_after_validation("traceability", "repair_traceability", "assemble_final_srs"),
        {"repair_traceability": "repair_traceability", "assemble_final_srs": "assemble_final_srs"},
    )
    graph.add_conditional_edges(
        "repair_traceability",
        _route_after_repair("traceability", "validate_traceability", "assemble_final_srs"),
        {"validate_traceability": "validate_traceability", "assemble_final_srs": "assemble_final_srs"},
    )

    graph.add_edge("assemble_final_srs", END)
    graph.add_edge("mark_failed", END)
    return graph.compile()


def build_async_srs_graph():
    graph = StateGraph(SRSGraphState)

    # 1. Overview Stage Nodes
    graph.add_node("generate_overview", _agenerate_overview)
    graph.add_node("parse_overview", _parse_overview)
    graph.add_node("validate_overview", _validate_overview)
    graph.add_node("repair_overview", _arepair_overview)

    # 2. Functional Stage Nodes
    graph.add_node("generate_functional", _agenerate_functional)
    graph.add_node("parse_functional", _parse_functional)
    graph.add_node("validate_functional", _validate_functional)
    graph.add_node("repair_functional", _arepair_functional)

    # 3. Non-Functional Stage Nodes
    graph.add_node("generate_nfr", _agenerate_nfr)
    graph.add_node("parse_nfr", _parse_nfr)
    graph.add_node("validate_nfr", _validate_nfr)
    graph.add_node("repair_nfr", _arepair_nfr)

    # 4. Traceability Stage Nodes
    graph.add_node("generate_traceability", _agenerate_traceability)
    graph.add_node("parse_traceability", _parse_traceability)
    graph.add_node("validate_traceability", _validate_traceability)
    graph.add_node("repair_traceability", _arepair_traceability)

    # 5. Terminal Nodes
    graph.add_node("assemble_final_srs", _assemble_final_srs)
    graph.add_node("mark_failed", _mark_failed)

    # --- Edges: Overview ---
    graph.add_edge(START, "generate_overview")
    graph.add_conditional_edges(
        "generate_overview",
        _route_after_generation("overview", "parse_overview"),
        {"mark_failed": "mark_failed", "parse_overview": "parse_overview"},
    )
    graph.add_conditional_edges(
        "parse_overview",
        _route_after_parse("overview", "validate_overview"),
        {"mark_failed": "mark_failed", "validate_overview": "validate_overview"},
    )
    graph.add_conditional_edges(
        "validate_overview",
        _route_after_validation("overview", "repair_overview", "generate_functional"),
        {"repair_overview": "repair_overview", "generate_functional": "generate_functional"},
    )
    graph.add_conditional_edges(
        "repair_overview",
        _route_after_repair("overview", "validate_overview", "generate_functional"),
        {"validate_overview": "validate_overview", "generate_functional": "generate_functional"},
    )

    # --- Edges: Functional ---
    graph.add_conditional_edges(
        "generate_functional",
        _route_after_generation("functional", "parse_functional"),
        {"mark_failed": "mark_failed", "parse_functional": "parse_functional"},
    )
    graph.add_conditional_edges(
        "parse_functional",
        _route_after_parse("functional", "validate_functional"),
        {"mark_failed": "mark_failed", "validate_functional": "validate_functional"},
    )
    graph.add_conditional_edges(
        "validate_functional",
        _route_after_validation("functional", "repair_functional", "generate_nfr"),
        {"repair_functional": "repair_functional", "generate_nfr": "generate_nfr"},
    )
    graph.add_conditional_edges(
        "repair_functional",
        _route_after_repair("functional", "validate_functional", "generate_nfr"),
        {"validate_functional": "validate_functional", "generate_nfr": "generate_nfr"},
    )

    # --- Edges: Non-Functional ---
    graph.add_conditional_edges(
        "generate_nfr",
        _route_after_generation("non_functional", "parse_nfr"),
        {"mark_failed": "mark_failed", "parse_nfr": "parse_nfr"},
    )
    graph.add_conditional_edges(
        "parse_nfr",
        _route_after_parse("non_functional", "validate_nfr"),
        {"mark_failed": "mark_failed", "validate_nfr": "validate_nfr"},
    )
    graph.add_conditional_edges(
        "validate_nfr",
        _route_after_validation("non_functional", "repair_nfr", "generate_traceability"),
        {"repair_nfr": "repair_nfr", "generate_traceability": "generate_traceability"},
    )
    graph.add_conditional_edges(
        "repair_nfr",
        _route_after_repair("non_functional", "validate_nfr", "generate_traceability"),
        {"validate_nfr": "validate_nfr", "generate_traceability": "generate_traceability"},
    )

    # --- Edges: Traceability ---
    graph.add_conditional_edges(
        "generate_traceability",
        _route_after_generation("traceability", "parse_traceability"),
        {"mark_failed": "mark_failed", "parse_traceability": "parse_traceability"},
    )
    graph.add_conditional_edges(
        "parse_traceability",
        _route_after_parse("traceability", "validate_traceability"),
        {"mark_failed": "mark_failed", "validate_traceability": "validate_traceability"},
    )
    graph.add_conditional_edges(
        "validate_traceability",
        _route_after_validation("traceability", "repair_traceability", "assemble_final_srs"),
        {"repair_traceability": "repair_traceability", "assemble_final_srs": "assemble_final_srs"},
    )
    graph.add_conditional_edges(
        "repair_traceability",
        _route_after_repair("traceability", "validate_traceability", "assemble_final_srs"),
        {"validate_traceability": "validate_traceability", "assemble_final_srs": "assemble_final_srs"},
    )

    graph.add_edge("assemble_final_srs", END)
    graph.add_edge("mark_failed", END)
    return graph.compile()


# ==============================================================================
# Node Handlers: Stage 1 - Overview
# ==============================================================================

def _generate_overview(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    log_stage_start(1, 4, "Overview", "Synthesizing Purpose, Scope, Context & Personas")
    prompt = build_overview_prompt(graph_state["config"].project_name, graph_state["requirements"])
    response = _complete_stage(srs, graph_state["config"], graph_state["provider"], "overview", [
        {"role": "system", "content": "You generate IEEE 29148 system overview JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.overview_response = response.content
        log_stage_llm_done("Overview", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


async def _agenerate_overview(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    log_stage_start(1, 4, "Overview", "Synthesizing Purpose, Scope, Context & Personas")
    prompt = build_overview_prompt(graph_state["config"].project_name, graph_state["requirements"])
    response = await _acomplete_stage(srs, graph_state["config"], graph_state["provider"], "overview", [
        {"role": "system", "content": "You generate IEEE 29148 system overview JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.overview_response = response.content
        log_stage_llm_done("Overview", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


def _parse_overview(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    srs.overview_section = _parse_stage_object(srs, "overview", srs.overview_response, "overview_section")
    return {"srs": srs}


def _validate_overview(graph_state: SRSGraphState) -> SRSGraphState:
    return _validate_stage(graph_state, "overview", validate_overview_section)


def _repair_overview(graph_state: SRSGraphState) -> SRSGraphState:
    return _repair_stage(graph_state, "overview", graph_state["srs"].overview_section, {})


async def _arepair_overview(graph_state: SRSGraphState) -> SRSGraphState:
    return await _arepair_stage(graph_state, "overview", graph_state["srs"].overview_section, {})


# ==============================================================================
# Node Handlers: Stage 2 - Functional Requirements
# ==============================================================================

def _generate_functional(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    num = len(graph_state["requirement_ids"])
    log_stage_start(2, 4, "Functional Requirements", f"Formalizing {num} FRs into IEEE 29148 normative specifications")
    prompt = build_functional_prompt(graph_state["requirements"], srs.overview_section or {})
    response = _complete_stage(srs, graph_state["config"], graph_state["provider"], "functional", [
        {"role": "system", "content": "You formalize IEEE 29148 functional requirements JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.functional_response = response.content
        log_stage_llm_done("Functional", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


async def _agenerate_functional(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    num = len(graph_state["requirement_ids"])
    log_stage_start(2, 4, "Functional Requirements", f"Formalizing {num} FRs into IEEE 29148 normative specifications")
    prompt = build_functional_prompt(graph_state["requirements"], srs.overview_section or {})
    response = await _acomplete_stage(srs, graph_state["config"], graph_state["provider"], "functional", [
        {"role": "system", "content": "You formalize IEEE 29148 functional requirements JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.functional_response = response.content
        log_stage_llm_done("Functional", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


def _parse_functional(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    srs.functional_section = _parse_stage_object(srs, "functional", srs.functional_response, "functional_requirements")
    return {"srs": srs}


def _validate_functional(graph_state: SRSGraphState) -> SRSGraphState:
    return _validate_stage(
        graph_state,
        "functional",
        lambda artifact: validate_functional_requirements(artifact, graph_state["requirement_ids"]),
    )


def _repair_functional(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    return _repair_stage(
        graph_state,
        "functional",
        srs.functional_section,
        {"overview": srs.overview_section},
    )


async def _arepair_functional(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    return await _arepair_stage(
        graph_state,
        "functional",
        srs.functional_section,
        {"overview": srs.overview_section},
    )


# ==============================================================================
# Node Handlers: Stage 3 - Non-Functional Requirements
# ==============================================================================

def _generate_nfr(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    num = len(graph_state["nfr_ids"])
    log_stage_start(3, 4, "Non-Functional Requirements", f"Allocating {num} NFRs across ISO/IEC 25010 characteristics")
    prompt = build_non_functional_prompt(
        graph_state["requirements"],
        srs.overview_section or {},
        srs.functional_section or [],
    )
    response = _complete_stage(srs, graph_state["config"], graph_state["provider"], "non_functional", [
        {"role": "system", "content": "You formalize ISO/IEC 25010 non-functional requirements JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.non_functional_response = response.content
        log_stage_llm_done("Non-Functional", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


async def _agenerate_nfr(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    num = len(graph_state["nfr_ids"])
    log_stage_start(3, 4, "Non-Functional Requirements", f"Allocating {num} NFRs across ISO/IEC 25010 characteristics")
    prompt = build_non_functional_prompt(
        graph_state["requirements"],
        srs.overview_section or {},
        srs.functional_section or [],
    )
    response = await _acomplete_stage(srs, graph_state["config"], graph_state["provider"], "non_functional", [
        {"role": "system", "content": "You formalize ISO/IEC 25010 non-functional requirements JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.non_functional_response = response.content
        log_stage_llm_done("Non-Functional", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


def _parse_nfr(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    srs.non_functional_section = _parse_stage_object(srs, "non_functional", srs.non_functional_response, "non_functional_requirements")
    return {"srs": srs}


def _validate_nfr(graph_state: SRSGraphState) -> SRSGraphState:
    return _validate_stage(
        graph_state,
        "non_functional",
        lambda artifact: validate_non_functional_requirements(artifact, graph_state["nfr_ids"]),
    )


def _repair_nfr(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    return _repair_stage(
        graph_state,
        "non_functional",
        srs.non_functional_section,
        {"overview": srs.overview_section, "functional": srs.functional_section},
    )


async def _arepair_nfr(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    return await _arepair_stage(
        graph_state,
        "non_functional",
        srs.non_functional_section,
        {"overview": srs.overview_section, "functional": srs.functional_section},
    )


# ==============================================================================
# Node Handlers: Stage 4 - Traceability Matrix
# ==============================================================================

def _generate_traceability(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    log_stage_start(4, 4, "Traceability Matrix", "Mapping Requirements Traceability Matrix (RTM)")
    prompt = build_traceability_prompt(
        srs.functional_section or [],
        srs.non_functional_section or [],
        graph_state["annexes"],
    )
    response = _complete_stage(srs, graph_state["config"], graph_state["provider"], "traceability", [
        {"role": "system", "content": "You generate IEEE 29148 Requirements Traceability Matrix JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.traceability_response = response.content
        log_stage_llm_done("Traceability", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


async def _agenerate_traceability(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    log_stage_start(4, 4, "Traceability Matrix", "Mapping Requirements Traceability Matrix (RTM)")
    prompt = build_traceability_prompt(
        srs.functional_section or [],
        srs.non_functional_section or [],
        graph_state["annexes"],
    )
    response = await _acomplete_stage(srs, graph_state["config"], graph_state["provider"], "traceability", [
        {"role": "system", "content": "You generate IEEE 29148 Requirements Traceability Matrix JSON."},
        {"role": "user", "content": prompt},
    ])
    if response is not None:
        srs.traceability_response = response.content
        log_stage_llm_done("Traceability", response.latency_ms, response.input_tokens, response.output_tokens)
    return {"srs": srs}


def _parse_traceability(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    srs.traceability_matrix = _parse_stage_object(srs, "traceability", srs.traceability_response, "traceability_matrix")
    return {"srs": srs}


def _validate_traceability(graph_state: SRSGraphState) -> SRSGraphState:
    functional_ids = [str(f.get("id")) for f in (graph_state["srs"].functional_section or [])]
    return _validate_stage(
        graph_state,
        "traceability",
        lambda artifact: validate_traceability_matrix(artifact, functional_ids),
    )


def _repair_traceability(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    return _repair_stage(
        graph_state,
        "traceability",
        srs.traceability_matrix,
        {"functional": srs.functional_section, "annexes": graph_state["annexes"]},
    )


async def _arepair_traceability(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    return await _arepair_stage(
        graph_state,
        "traceability",
        srs.traceability_matrix,
        {"functional": srs.functional_section, "annexes": graph_state["annexes"]},
    )


# ==============================================================================
# Node Handlers: Assembly & Terminal
# ==============================================================================

def _assemble_final_srs(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    log_compiling_markdown(
        project_name=graph_state["config"].project_name,
        has_hld=bool(srs.hld_annex),
        has_lld=bool(srs.lld_annex),
        has_ui=bool(srs.ui_annex),
    )
    srs.final_ir = {
        "overview": srs.overview_section,
        "functional": srs.functional_section,
        "non_functional": srs.non_functional_section,
        "traceability": srs.traceability_matrix,
    }
    srs.final_srs_markdown = render_ieee_29148_markdown(
        project_name=graph_state["config"].project_name,
        job_id=graph_state["config"].job_id,
        overview=srs.overview_section,
        functional=srs.functional_section,
        non_functional=srs.non_functional_section,
        traceability=srs.traceability_matrix,
        hld_annex=srs.hld_annex,
        lld_annex=srs.lld_annex,
        ui_annex=srs.ui_annex,
    )
    srs.status = "valid" if all_stage_validations_passed(srs) else "invalid"
    return {"srs": srs}


def _mark_failed(graph_state: SRSGraphState) -> SRSGraphState:
    srs = graph_state["srs"]
    srs.status = "failed"
    return {"srs": srs}


# ==============================================================================
# Routing & Helpers
# ==============================================================================

def _route_after_generation(stage: StageName, next_node: RouteName):
    def route(graph_state: SRSGraphState) -> RouteName:
        provider_errors = graph_state["srs"].provider_errors or []
        if provider_errors and provider_errors[-1].get("stage") == stage:
            return "mark_failed"
        return next_node
    return route


def _route_after_parse(stage: StageName, next_node: RouteName):
    def route(graph_state: SRSGraphState) -> RouteName:
        return "mark_failed" if _artifact_for(graph_state["srs"], stage) is None else next_node
    return route


def _route_after_validation(stage: StageName, repair_node: RouteName, next_node: RouteName):
    def route(graph_state: SRSGraphState) -> RouteName:
        validation = _validation_for(graph_state["srs"], stage) or {}
        if validation.get("passed"):
            return next_node
        if graph_state["repair_blocked"].get(stage):
            return next_node
        if graph_state["repair_attempts"].get(stage, 0) < graph_state["repair_service"].config.max_attempts:
            return repair_node
        return next_node
    return route


def _route_after_repair(stage: StageName, validate_node: RouteName, next_node: RouteName):
    def route(graph_state: SRSGraphState) -> RouteName:
        return next_node if graph_state["repair_blocked"].get(stage) else validate_node
    return route


def _artifact_for(srs: SRSState, stage: StageName):
    if stage == "overview": return srs.overview_section
    if stage == "functional": return srs.functional_section
    if stage == "non_functional": return srs.non_functional_section
    return srs.traceability_matrix


def _set_artifact(srs: SRSState, stage: StageName, artifact) -> None:
    if stage == "overview": srs.overview_section = artifact
    elif stage == "functional": srs.functional_section = artifact
    elif stage == "non_functional": srs.non_functional_section = artifact
    else: srs.traceability_matrix = artifact


def _validation_for(srs: SRSState, stage: StageName):
    if stage == "overview": return srs.overview_validation
    if stage == "functional": return srs.functional_validation
    if stage == "non_functional": return srs.non_functional_validation
    return srs.traceability_validation


def _set_validation(srs: SRSState, stage: StageName, validation: dict) -> None:
    if stage == "overview": srs.overview_validation = validation
    elif stage == "functional": srs.functional_validation = validation
    elif stage == "non_functional": srs.non_functional_validation = validation
    else: srs.traceability_validation = validation


def _validate_stage(graph_state: SRSGraphState, stage: StageName, validator):
    srs = graph_state["srs"]
    artifact = _artifact_for(srs, stage)
    validation = validator(artifact)
    _set_validation(srs, stage, validation)
    graph_state["initial_validations"].setdefault(stage, validation)
    _write_repair_metadata(graph_state, stage, validation)
    log_stage_validation(
        stage_name=stage,
        passed=bool(validation.get("passed", False)),
        passed_checks=int(validation.get("passed_checks", 0)),
        total_checks=int(validation.get("total_checks", 0)),
        errors=validation.get("errors", []),
        warnings=validation.get("warnings", []),
    )
    return {
        "srs": srs,
        "initial_validations": graph_state["initial_validations"],
    }


def _repair_stage(
    graph_state: SRSGraphState,
    stage: StageName,
    artifact,
    dependencies: dict,
):
    srs = graph_state["srs"]
    repair_attempts = dict(graph_state["repair_attempts"])
    repair_errors = dict(graph_state["repair_errors"])
    repair_blocked = dict(graph_state["repair_blocked"])

    repair_attempts[stage] = repair_attempts.get(stage, 0) + 1
    attempt = repair_attempts[stage]
    max_attempts = graph_state["repair_service"].config.max_attempts
    prev_val = _validation_for(srs, stage) or {}
    err_count = len(prev_val.get("errors", []))
    log_repair_start(stage, attempt, max_attempts, err_count)

    repair_result = graph_state["repair_service"].repair(
        stage=stage,
        artifact=artifact,
        validation_result=prev_val,
        requirements=graph_state["requirements"],
        dependencies=dependencies,
    )
    lat_ms = repair_result.metrics.latency_ms if repair_result.metrics else 0
    if repair_result.metrics:
        record_repair_metrics(srs.metrics, stage, attempt, repair_result.metrics)
    if repair_result.error:
        repair_errors[stage] = [*repair_errors.get(stage, []), repair_result.error]
        repair_blocked[stage] = True
        log_repair_result(stage, attempt, success=False, latency_ms=lat_ms)
        _write_repair_metadata(graph_state, stage, prev_val, repair_attempts, repair_errors)
        return {"srs": srs, "repair_attempts": repair_attempts, "repair_errors": repair_errors, "repair_blocked": repair_blocked}
    if repair_result.artifact is None:
        repair_errors[stage] = [*repair_errors.get(stage, []), {"stage": stage, "error_type": "InvalidRepairOutput", "message": "Repair returned no artifact."}]
        repair_blocked[stage] = True
        log_repair_result(stage, attempt, success=False, latency_ms=lat_ms)
        _write_repair_metadata(graph_state, stage, prev_val, repair_attempts, repair_errors)
        return {"srs": srs, "repair_attempts": repair_attempts, "repair_errors": repair_errors, "repair_blocked": repair_blocked}

    log_repair_result(stage, attempt, success=True, latency_ms=lat_ms)
    _set_artifact(srs, stage, repair_result.artifact)
    return {"srs": srs, "repair_attempts": repair_attempts, "repair_errors": repair_errors}


async def _arepair_stage(
    graph_state: SRSGraphState,
    stage: StageName,
    artifact,
    dependencies: dict,
):
    srs = graph_state["srs"]
    repair_attempts = dict(graph_state["repair_attempts"])
    repair_errors = dict(graph_state["repair_errors"])
    repair_blocked = dict(graph_state["repair_blocked"])

    repair_attempts[stage] = repair_attempts.get(stage, 0) + 1
    attempt = repair_attempts[stage]
    max_attempts = graph_state["repair_service"].config.max_attempts
    prev_val = _validation_for(srs, stage) or {}
    err_count = len(prev_val.get("errors", []))
    log_repair_start(stage, attempt, max_attempts, err_count)

    repair_result = await graph_state["repair_service"].arepair(
        stage=stage,
        artifact=artifact,
        validation_result=prev_val,
        requirements=graph_state["requirements"],
        dependencies=dependencies,
    )
    lat_ms = repair_result.metrics.latency_ms if repair_result.metrics else 0
    if repair_result.metrics:
        record_repair_metrics(srs.metrics, stage, attempt, repair_result.metrics)
    if repair_result.error:
        repair_errors[stage] = [*repair_errors.get(stage, []), repair_result.error]
        repair_blocked[stage] = True
        log_repair_result(stage, attempt, success=False, latency_ms=lat_ms)
        _write_repair_metadata(graph_state, stage, prev_val, repair_attempts, repair_errors)
        return {"srs": srs, "repair_attempts": repair_attempts, "repair_errors": repair_errors, "repair_blocked": repair_blocked}
    if repair_result.artifact is None:
        repair_errors[stage] = [*repair_errors.get(stage, []), {"stage": stage, "error_type": "InvalidRepairOutput", "message": "Repair returned no artifact."}]
        repair_blocked[stage] = True
        log_repair_result(stage, attempt, success=False, latency_ms=lat_ms)
        _write_repair_metadata(graph_state, stage, prev_val, repair_attempts, repair_errors)
        return {"srs": srs, "repair_attempts": repair_attempts, "repair_errors": repair_errors, "repair_blocked": repair_blocked}

    log_repair_result(stage, attempt, success=True, latency_ms=lat_ms)
    _set_artifact(srs, stage, repair_result.artifact)
    return {"srs": srs, "repair_attempts": repair_attempts, "repair_errors": repair_errors}


def _write_repair_metadata(
    graph_state: SRSGraphState,
    stage: StageName,
    final_validation: dict,
    repair_attempts: dict[str, int] | None = None,
    repair_errors: dict[str, list[dict]] | None = None,
) -> None:
    srs = graph_state["srs"]
    attempts = repair_attempts or graph_state["repair_attempts"]
    errors = repair_errors or graph_state["repair_errors"]
    initial_validation = graph_state["initial_validations"].get(stage, final_validation)
    srs.repair_metadata[stage] = {
        "initial_validation": initial_validation,
        "final_validation": final_validation,
        "repair_attempts": attempts.get(stage, 0),
        "repair_success": bool(
            attempts.get(stage, 0) > 0
            and not initial_validation.get("passed")
            and final_validation.get("passed")
        ),
        "repair_errors": errors.get(stage, []),
        "max_repair_attempts": graph_state["repair_service"].config.max_attempts,
    }


def _complete_stage(
    state: SRSState,
    config: SRSConfig,
    provider: LLMProvider,
    stage: str,
    messages: list[dict],
) -> LLMResponse | None:
    try:
        response = provider.complete(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    except Exception as exc:
        state.status = "failed"
        state.provider_errors.append({"stage": stage, "message": str(exc), "error_type": exc.__class__.__name__})
        log_stage_error(stage, exc.__class__.__name__, str(exc))
        return None
    record_stage_metrics(state.metrics, stage, response)
    return response


async def _acomplete_stage(
    state: SRSState,
    config: SRSConfig,
    provider: LLMProvider,
    stage: str,
    messages: list[dict],
) -> LLMResponse | None:
    try:
        response = await provider.acomplete(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    except Exception as exc:
        state.status = "failed"
        state.provider_errors.append({"stage": stage, "message": str(exc), "error_type": exc.__class__.__name__})
        log_stage_error(stage, exc.__class__.__name__, str(exc))
        return None
    record_stage_metrics(state.metrics, stage, response)
    return response


def _parse_stage_object(
    state: SRSState,
    stage: str,
    content: str,
    expected_key: str,
):
    try:
        parsed = clean_json_response(content)
    except json.JSONDecodeError as exc:
        state.status = "failed"
        state.parse_errors.append({"stage": stage, "message": str(exc)})
        log_stage_error(stage, "JSONDecodeError", f"Failed to parse model response JSON: {str(exc)[:120]}")
        return None

    value = parsed.get(expected_key) if isinstance(parsed, dict) else None
    if value is None and isinstance(parsed, dict):
        # Fallback check
        fallbacks = {
            "overview_section": "overview",
            "functional_requirements": "functional",
            "non_functional_requirements": "non_functional",
            "traceability_matrix": "traceability",
        }
        alt_key = fallbacks.get(expected_key)
        if alt_key and alt_key in parsed:
            value = parsed[alt_key]

    if value is None:
        state.status = "failed"
        state.parse_errors.append({"stage": stage, "message": f"Missing expected key '{expected_key}'."})
        log_stage_error(stage, "MissingKeyError", f"Missing key '{expected_key}' in output.")
        return None
    return value


# ==============================================================================
# Public Runner Functions
# ==============================================================================

def run_srs_graph(
    config: SRSConfig,
    requirements: dict,
    hld_annex: dict | None = None,
    lld_annex: dict | None = None,
    ui_annex: dict | None = None,
    provider: LLMProvider | None = None,
) -> SRSState:
    from llm.factory import get_llm_provider

    llm_provider = provider or get_llm_provider(config.provider)
    repair_service = ArtifactRepairService(
        config=ArtifactRepairConfig(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_attempts=getattr(config, "max_repair_attempts", MAX_REPAIR_ATTEMPTS),
        ),
        provider=llm_provider,
    )

    req_ids = [str(f.get("id")) for f in requirements.get("functional_requirements", []) if f.get("id")]
    nfr_ids = [str(n.get("id")) for n in requirements.get("non_functional_requirements", []) if n.get("id")]

    initial_state: SRSGraphState = {
        "config": config,
        "requirements": requirements,
        "requirement_ids": req_ids,
        "nfr_ids": nfr_ids,
        "annexes": {
            "hld_annex": hld_annex,
            "lld_annex": lld_annex,
            "ui_annex": ui_annex,
        },
        "provider": llm_provider,
        "repair_service": repair_service,
        "srs": SRSState(
            job_id=config.job_id,
            project_name=config.project_name,
            raw_requirements=requirements,
            hld_annex=hld_annex,
            lld_annex=lld_annex,
            ui_annex=ui_annex,
        ),
        "repair_attempts": {"overview": 0, "functional": 0, "non_functional": 0, "traceability": 0},
        "repair_errors": {"overview": [], "functional": [], "non_functional": [], "traceability": []},
        "initial_validations": {},
        "repair_blocked": {"overview": False, "functional": False, "non_functional": False, "traceability": False},
    }
    return build_srs_graph().invoke(initial_state)["srs"]


async def arun_srs_graph(
    config: SRSConfig,
    requirements: dict,
    hld_annex: dict | None = None,
    lld_annex: dict | None = None,
    ui_annex: dict | None = None,
    provider: LLMProvider | None = None,
) -> SRSState:
    from llm.factory import get_llm_provider

    llm_provider = provider or get_llm_provider(config.provider)
    repair_service = ArtifactRepairService(
        config=ArtifactRepairConfig(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_attempts=getattr(config, "max_repair_attempts", MAX_REPAIR_ATTEMPTS),
        ),
        provider=llm_provider,
    )

    req_ids = [str(f.get("id")) for f in requirements.get("functional_requirements", []) if f.get("id")]
    nfr_ids = [str(n.get("id")) for n in requirements.get("non_functional_requirements", []) if n.get("id")]

    initial_state: SRSGraphState = {
        "config": config,
        "requirements": requirements,
        "requirement_ids": req_ids,
        "nfr_ids": nfr_ids,
        "annexes": {
            "hld_annex": hld_annex,
            "lld_annex": lld_annex,
            "ui_annex": ui_annex,
        },
        "provider": llm_provider,
        "repair_service": repair_service,
        "srs": SRSState(
            job_id=config.job_id,
            project_name=config.project_name,
            raw_requirements=requirements,
            hld_annex=hld_annex,
            lld_annex=lld_annex,
            ui_annex=ui_annex,
        ),
        "repair_attempts": {"overview": 0, "functional": 0, "non_functional": 0, "traceability": 0},
        "repair_errors": {"overview": [], "functional": [], "non_functional": [], "traceability": []},
        "initial_validations": {},
        "repair_blocked": {"overview": False, "functional": False, "non_functional": False, "traceability": False},
    }
    return (await build_async_srs_graph().ainvoke(initial_state))["srs"]
