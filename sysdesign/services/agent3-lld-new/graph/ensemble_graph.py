from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from Services.agenticReconciliation import (
    AgentDecision,
    AgenticReconciliationResult,
    AgenticReconciliationService,
    MAX_AGENT_ITERATIONS,
    _collect_unresolved_issues,
    _repair_attempt,
    _validator_trace,
    decide_reconciliation_action,
)
from graph.candidate import CandidateConfig, CandidateState
from graph.candidate_graph import arun_candidate_graph, run_candidate_graph
from llm.provider import LLMProvider
from Services.diagramOrchestrator import (
    OrchestrationResult,
    _build_orchestration_result,
    _safe_error_message,
)
from Services.expertRepair import ExpertRepairConfig, ExpertRepairService
from Services.expertReview import ExpertReviewConfig, ExpertReviewResult
from Services.expertReviewService import ExpertReviewService
from Services.multiAgentGeneration import MultiAgentGenerationResult
from Services.validationService import ValidationService
from utils.irMapper import convert_to_ir


ReconciliationRoute = Literal[
    "finish_reconciliation",
    "expert_repair",
]


def _merge_candidate_results(
    left: dict[str, CandidateState] | None,
    right: dict[str, CandidateState] | None,
) -> dict[str, CandidateState]:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


class EnsembleGraphState(TypedDict, total=False):
    requirements: str
    requirement_ids: list[str]
    candidate_configs: list[CandidateConfig]
    providers: dict[str, LLMProvider]
    candidate_results: Annotated[dict[str, CandidateState], _merge_candidate_results]
    current_config: CandidateConfig
    current_provider: LLMProvider | None
    orchestration_result: OrchestrationResult
    expert_review: ExpertReviewResult
    expert_review_config: ExpertReviewConfig | None
    expert_review_provider: LLMProvider | None
    selected_candidate: CandidateState | None
    current_final_ir: dict | None
    initial_validation_result: dict | None
    validation_result: dict | None
    latest_validation_report: dict
    reconciliation_decision: AgentDecision | None
    reconciliation_iterations: int
    reconciliation_status: str
    reconciliation_stop_reason: str
    repair_metadata: dict
    agent_trace: list[dict]
    unresolved_issues: list[dict]
    repair_service: ExpertRepairService | None
    repair_config: ExpertRepairConfig | None
    repair_provider: LLMProvider | None
    reconciliation: AgenticReconciliationResult | None
    final_validation_report: dict | None
    multi_agent_result: MultiAgentGenerationResult


def run_ensemble_graph(
    *,
    requirements: str,
    requirement_ids: list[str] | None = None,
    candidate_configs: Sequence[CandidateConfig],
    providers: Mapping[str, LLMProvider] | None = None,
) -> OrchestrationResult:
    initial_state: EnsembleGraphState = {
        "requirements": requirements,
        "requirement_ids": list(requirement_ids or []),
        "candidate_configs": [deepcopy(config) for config in candidate_configs],
        "providers": dict(providers or {}),
        "candidate_results": {},
    }
    final_state = build_ensemble_graph().invoke(initial_state)
    return final_state["orchestration_result"]


async def arun_ensemble_graph(
    *,
    requirements: str,
    requirement_ids: list[str] | None = None,
    candidate_configs: Sequence[CandidateConfig],
    providers: Mapping[str, LLMProvider] | None = None,
) -> OrchestrationResult:
    initial_state: EnsembleGraphState = {
        "requirements": requirements,
        "requirement_ids": list(requirement_ids or []),
        "candidate_configs": [deepcopy(config) for config in candidate_configs],
        "providers": dict(providers or {}),
        "candidate_results": {},
    }
    final_state = await build_async_ensemble_graph().ainvoke(initial_state)
    return final_state["orchestration_result"]


def run_multi_agent_graph(
    *,
    requirements: str,
    requirement_ids: list[str] | None = None,
    candidate_configs: Sequence[CandidateConfig],
    providers: Mapping[str, LLMProvider] | None = None,
    expert_review_config: ExpertReviewConfig | None = None,
    expert_review_provider: LLMProvider | None = None,
    repair_service: ExpertRepairService | None = None,
    repair_config: ExpertRepairConfig | None = None,
    repair_provider: LLMProvider | None = None,
) -> MultiAgentGenerationResult:
    initial_state: EnsembleGraphState = {
        "requirements": requirements,
        "requirement_ids": list(requirement_ids or []),
        "candidate_configs": [deepcopy(config) for config in candidate_configs],
        "providers": dict(providers or {}),
        "candidate_results": {},
        "expert_review_config": expert_review_config,
        "expert_review_provider": expert_review_provider,
        "repair_service": repair_service,
        "repair_config": repair_config,
        "repair_provider": repair_provider,
        "repair_metadata": {
            "attempts": [],
            "max_iterations": MAX_AGENT_ITERATIONS,
        },
        "agent_trace": [],
        "reconciliation_iterations": 0,
    }
    final_state = build_multi_agent_graph().invoke(initial_state)
    return final_state["multi_agent_result"]


async def arun_multi_agent_graph(
    *,
    requirements: str,
    requirement_ids: list[str] | None = None,
    candidate_configs: Sequence[CandidateConfig],
    providers: Mapping[str, LLMProvider] | None = None,
    expert_review_config: ExpertReviewConfig | None = None,
    expert_review_provider: LLMProvider | None = None,
    repair_service: ExpertRepairService | None = None,
    repair_config: ExpertRepairConfig | None = None,
    repair_provider: LLMProvider | None = None,
) -> MultiAgentGenerationResult:
    initial_state: EnsembleGraphState = {
        "requirements": requirements,
        "requirement_ids": list(requirement_ids or []),
        "candidate_configs": [deepcopy(config) for config in candidate_configs],
        "providers": dict(providers or {}),
        "candidate_results": {},
        "expert_review_config": expert_review_config,
        "expert_review_provider": expert_review_provider,
        "repair_service": repair_service,
        "repair_config": repair_config,
        "repair_provider": repair_provider,
        "repair_metadata": {
            "attempts": [],
            "max_iterations": MAX_AGENT_ITERATIONS,
        },
        "agent_trace": [],
        "reconciliation_iterations": 0,
    }
    final_state = await build_async_multi_agent_graph().ainvoke(initial_state)
    return final_state["multi_agent_result"]


def build_ensemble_graph():
    graph = StateGraph(EnsembleGraphState)

    graph.add_node("prepare_candidates", _prepare_candidates)
    graph.add_node("run_candidate", _run_candidate_worker)
    graph.add_node("aggregate_candidates", _aggregate_candidates)

    graph.add_edge(START, "prepare_candidates")
    graph.add_conditional_edges("prepare_candidates", _dispatch_candidates)
    graph.add_edge("run_candidate", "aggregate_candidates")
    graph.add_edge("aggregate_candidates", END)
    return graph.compile()


def build_async_ensemble_graph():
    graph = StateGraph(EnsembleGraphState)

    graph.add_node("prepare_candidates", _prepare_candidates)
    graph.add_node("run_candidate", _arun_candidate_worker)
    graph.add_node("aggregate_candidates", _aggregate_candidates)

    graph.add_edge(START, "prepare_candidates")
    graph.add_conditional_edges("prepare_candidates", _dispatch_candidates)
    graph.add_edge("run_candidate", "aggregate_candidates")
    graph.add_edge("aggregate_candidates", END)
    return graph.compile()


def build_multi_agent_graph():
    graph = _build_candidate_ensemble_builder()
    graph.add_node("expert_review", _expert_review)
    graph.add_node("select_candidate", _select_candidate)
    graph.add_node("final_validate", _final_validate)
    graph.add_node("decide_reconciliation", _decide_reconciliation)
    graph.add_node("expert_repair", _expert_repair)
    graph.add_node("finish_reconciliation", _finish_reconciliation)
    graph.add_node("build_multi_agent_result", _build_multi_agent_result)

    graph.add_edge("aggregate_candidates", "expert_review")
    graph.add_edge("expert_review", "select_candidate")
    graph.add_conditional_edges(
        "select_candidate",
        _route_after_selection,
        {
            "build_multi_agent_result": "build_multi_agent_result",
            "final_validate": "final_validate",
        },
    )
    graph.add_edge("final_validate", "decide_reconciliation")
    graph.add_conditional_edges(
        "decide_reconciliation",
        _route_after_reconciliation_decision,
        {
            "finish_reconciliation": "finish_reconciliation",
            "expert_repair": "expert_repair",
        },
    )
    graph.add_conditional_edges(
        "expert_repair",
        _route_after_expert_repair,
        {
            "finish_reconciliation": "finish_reconciliation",
            "final_validate": "final_validate",
        },
    )
    graph.add_edge("finish_reconciliation", "build_multi_agent_result")
    graph.add_edge("build_multi_agent_result", END)
    return graph.compile()


def build_async_multi_agent_graph():
    graph = _build_async_candidate_ensemble_builder()
    graph.add_node("expert_review", _aexpert_review)
    graph.add_node("select_candidate", _select_candidate)
    graph.add_node("final_validate", _final_validate)
    graph.add_node("decide_reconciliation", _decide_reconciliation)
    graph.add_node("expert_repair", _aexpert_repair)
    graph.add_node("finish_reconciliation", _finish_reconciliation)
    graph.add_node("build_multi_agent_result", _build_multi_agent_result)

    graph.add_edge("aggregate_candidates", "expert_review")
    graph.add_edge("expert_review", "select_candidate")
    graph.add_conditional_edges(
        "select_candidate",
        _route_after_selection,
        {
            "build_multi_agent_result": "build_multi_agent_result",
            "final_validate": "final_validate",
        },
    )
    graph.add_edge("final_validate", "decide_reconciliation")
    graph.add_conditional_edges(
        "decide_reconciliation",
        _route_after_reconciliation_decision,
        {
            "finish_reconciliation": "finish_reconciliation",
            "expert_repair": "expert_repair",
        },
    )
    graph.add_conditional_edges(
        "expert_repair",
        _route_after_expert_repair,
        {
            "finish_reconciliation": "finish_reconciliation",
            "final_validate": "final_validate",
        },
    )
    graph.add_edge("finish_reconciliation", "build_multi_agent_result")
    graph.add_edge("build_multi_agent_result", END)
    return graph.compile()


def _build_candidate_ensemble_builder():
    graph = StateGraph(EnsembleGraphState)

    graph.add_node("prepare_candidates", _prepare_candidates)
    graph.add_node("run_candidate", _run_candidate_worker)
    graph.add_node("aggregate_candidates", _aggregate_candidates)

    graph.add_edge(START, "prepare_candidates")
    graph.add_conditional_edges("prepare_candidates", _dispatch_candidates)
    graph.add_edge("run_candidate", "aggregate_candidates")
    return graph


def _build_async_candidate_ensemble_builder():
    graph = StateGraph(EnsembleGraphState)

    graph.add_node("prepare_candidates", _prepare_candidates)
    graph.add_node("run_candidate", _arun_candidate_worker)
    graph.add_node("aggregate_candidates", _aggregate_candidates)

    graph.add_edge(START, "prepare_candidates")
    graph.add_conditional_edges("prepare_candidates", _dispatch_candidates)
    graph.add_edge("run_candidate", "aggregate_candidates")
    return graph


def _prepare_candidates(state: EnsembleGraphState) -> EnsembleGraphState:
    return {
        "requirement_ids": list(state.get("requirement_ids") or []),
        "candidate_configs": [deepcopy(config) for config in state.get("candidate_configs", [])],
        "providers": dict(state.get("providers") or {}),
        "candidate_results": {},
    }


def _dispatch_candidates(state: EnsembleGraphState) -> list[Send]:
    providers = state.get("providers") or {}
    return [
        Send(
            "run_candidate",
            {
                "requirements": state["requirements"],
                "requirement_ids": list(state.get("requirement_ids") or []),
                "current_config": deepcopy(config),
                "current_provider": providers.get(config.candidate_id),
            },
        )
        for config in state.get("candidate_configs", [])
    ]


def _run_candidate_worker(state: EnsembleGraphState) -> EnsembleGraphState:
    config = state["current_config"]
    try:
        candidate = run_candidate_graph(
            config=deepcopy(config),
            requirements=state["requirements"],
            requirement_ids=list(state.get("requirement_ids") or []),
            provider=state.get("current_provider"),
        )
    except Exception as exc:
        candidate = CandidateState(
            candidate_id=config.candidate_id,
            provider="",
            model="",
            status="failed",
            provider_errors=[{
                "stage": "agent",
                "message": _safe_error_message(exc),
                "error_type": exc.__class__.__name__,
            }],
        )

    return {"candidate_results": {candidate.candidate_id: deepcopy(candidate)}}


async def _arun_candidate_worker(state: EnsembleGraphState) -> EnsembleGraphState:
    config = state["current_config"]
    try:
        candidate = await arun_candidate_graph(
            config=deepcopy(config),
            requirements=state["requirements"],
            requirement_ids=list(state.get("requirement_ids") or []),
            provider=state.get("current_provider"),
        )
    except Exception as exc:
        candidate = CandidateState(
            candidate_id=config.candidate_id,
            provider="",
            model="",
            status="failed",
            provider_errors=[{
                "stage": "agent",
                "message": _safe_error_message(exc),
                "error_type": exc.__class__.__name__,
            }],
        )

    return {"candidate_results": {candidate.candidate_id: deepcopy(candidate)}}


def _aggregate_candidates(state: EnsembleGraphState) -> EnsembleGraphState:
    unordered_candidates = state.get("candidate_results") or {}
    ordered_candidates = {
        config.candidate_id: unordered_candidates[config.candidate_id]
        for config in state.get("candidate_configs", [])
        if config.candidate_id in unordered_candidates
    }
    return {
        "orchestration_result": _build_orchestration_result(
            total_agents=len(state.get("candidate_configs", [])),
            candidates=ordered_candidates,
        )
    }


def _expert_review(state: EnsembleGraphState) -> EnsembleGraphState:
    expert_review = ExpertReviewService.review_candidates_internal(
        requirements=state["requirements"],
        orchestration_result=state["orchestration_result"],
        config=state.get("expert_review_config"),
        provider=state.get("expert_review_provider"),
    )
    return {"expert_review": expert_review}


async def _aexpert_review(state: EnsembleGraphState) -> EnsembleGraphState:
    expert_review = await ExpertReviewService.areview_candidates_internal(
        requirements=state["requirements"],
        orchestration_result=state["orchestration_result"],
        config=state.get("expert_review_config"),
        provider=state.get("expert_review_provider"),
    )
    return {"expert_review": expert_review}


def _select_candidate(state: EnsembleGraphState) -> EnsembleGraphState:
    expert_review = state["expert_review"]
    selected_candidate = (
        state["orchestration_result"].candidates.get(expert_review.selected_candidate_id)
        if expert_review.selected_candidate_id
        else None
    )
    return {
        "selected_candidate": selected_candidate,
        "current_final_ir": deepcopy(selected_candidate.final_ir)
        if selected_candidate and selected_candidate.final_ir
        else None,
    }


def _final_validate(state: EnsembleGraphState) -> EnsembleGraphState:
    current_final_ir = state.get("current_final_ir")
    iteration = int(state.get("reconciliation_iterations", 0) or 0) + 1
    validation_result = ValidationService.validate(
        convert_to_ir(current_final_ir),
        requirement_ids=state.get("requirement_ids") or [],
    )
    latest_report = dict(validation_result.get("report") or {})
    trace = [
        *(state.get("agent_trace") or []),
        _validator_trace(iteration, latest_report),
    ]
    result = {
        "validation_result": validation_result,
        "latest_validation_report": latest_report,
        "reconciliation_iterations": iteration,
        "agent_trace": trace,
    }
    if state.get("initial_validation_result") is None:
        result["initial_validation_result"] = validation_result
    return result


def _decide_reconciliation(state: EnsembleGraphState) -> EnsembleGraphState:
    iteration = int(state.get("reconciliation_iterations", 0) or 0)
    latest_report = state.get("latest_validation_report") or {}
    current_final_ir = state.get("current_final_ir") or {}

    if latest_report.get("passed"):
        return {
            "reconciliation_status": "passed",
            "reconciliation_stop_reason": "validation_passed",
            "unresolved_issues": [],
            "reconciliation_decision": AgentDecision("PASS", "Final validation passed."),
        }

    decision = decide_reconciliation_action(
        latest_report,
        current_ir=current_final_ir,
        requirements=state["requirements"],
        iteration=iteration,
    )
    trace = [
        *(state.get("agent_trace") or []),
        {
            "iteration": iteration,
            "agent": "expert_decision",
            **decision.to_dict(),
        },
    ]

    if decision.action == "SEMANTIC_GAP":
        return {
            "reconciliation_decision": decision,
            "agent_trace": trace,
            "reconciliation_status": "semantic_gap",
            "reconciliation_stop_reason": "semantic_gap",
            "unresolved_issues": _collect_unresolved_issues(latest_report),
        }

    if decision.action != "REPAIR":
        return {
            "reconciliation_decision": decision,
            "agent_trace": trace,
            "reconciliation_status": "repair_not_possible",
            "reconciliation_stop_reason": decision.reason,
            "unresolved_issues": _collect_unresolved_issues(latest_report),
        }

    if iteration >= MAX_AGENT_ITERATIONS:
        trace.append({
            "iteration": iteration,
            "agent": "expert_decision",
            "action": "MAX_ITERATIONS_REACHED",
            "reason": "Reached the final agentic reconciliation iteration limit.",
        })
        return {
            "reconciliation_decision": AgentDecision(
                "MAX_ITERATIONS_REACHED",
                "Reached the final agentic reconciliation iteration limit.",
            ),
            "agent_trace": trace,
            "reconciliation_status": "max_iterations_reached",
            "reconciliation_stop_reason": "max_iterations_reached",
            "unresolved_issues": _collect_unresolved_issues(latest_report),
        }

    return {
        "reconciliation_decision": decision,
        "agent_trace": trace,
    }


def _expert_repair(state: EnsembleGraphState) -> EnsembleGraphState:
    service = state.get("repair_service")
    if service is None:
        service = AgenticReconciliationService.build_expert_repair_service(
            config=state.get("repair_config")
            or AgenticReconciliationService.get_expert_repair_config(),
            provider=state.get("repair_provider"),
        )

    iteration = int(state.get("reconciliation_iterations", 0) or 0)
    repair_result = service.repair(
        final_ir=state.get("current_final_ir") or {},
        validation_report=state.get("latest_validation_report") or {},
        requirements=state["requirements"],
        requirement_ids=state.get("requirement_ids") or [],
        repair_guidance=(
            state["reconciliation_decision"].to_dict()
            if state.get("reconciliation_decision")
            else {}
        ),
        context=_reconciliation_context(state),
    )
    repair_metadata = deepcopy(state.get("repair_metadata") or {
        "attempts": [],
        "max_iterations": MAX_AGENT_ITERATIONS,
    })
    repair_metadata.setdefault("attempts", []).append(
        _repair_attempt(iteration, repair_result)
    )
    repair_metadata.setdefault("max_iterations", MAX_AGENT_ITERATIONS)
    trace = [
        *(state.get("agent_trace") or []),
        {
            "iteration": iteration,
            "agent": "expert_repair",
            "status": "failed" if repair_result.error else "completed",
            "error": repair_result.error,
        },
    ]

    if repair_result.error or repair_result.final_ir is None:
        return {
            "repair_service": service,
            "repair_metadata": repair_metadata,
            "agent_trace": trace,
            "reconciliation_status": "repair_not_possible",
            "reconciliation_stop_reason": "repair_failed",
            "unresolved_issues": _collect_unresolved_issues(
                state.get("latest_validation_report") or {}
            ),
        }

    return {
        "repair_service": service,
        "repair_metadata": repair_metadata,
        "agent_trace": trace,
        "current_final_ir": deepcopy(repair_result.final_ir),
        "validation_result": None,
    }


async def _aexpert_repair(state: EnsembleGraphState) -> EnsembleGraphState:
    service = state.get("repair_service")
    if service is None:
        service = AgenticReconciliationService.build_expert_repair_service(
            config=state.get("repair_config")
            or AgenticReconciliationService.get_expert_repair_config(),
            provider=state.get("repair_provider"),
        )

    iteration = int(state.get("reconciliation_iterations", 0) or 0)
    repair_result = await service.arepair(
        final_ir=state.get("current_final_ir") or {},
        validation_report=state.get("latest_validation_report") or {},
        requirements=state["requirements"],
        requirement_ids=state.get("requirement_ids") or [],
        repair_guidance=(
            state["reconciliation_decision"].to_dict()
            if state.get("reconciliation_decision")
            else {}
        ),
        context=_reconciliation_context(state),
    )
    repair_metadata = deepcopy(state.get("repair_metadata") or {
        "attempts": [],
        "max_iterations": MAX_AGENT_ITERATIONS,
    })
    repair_metadata.setdefault("attempts", []).append(
        _repair_attempt(iteration, repair_result)
    )
    repair_metadata.setdefault("max_iterations", MAX_AGENT_ITERATIONS)
    trace = [
        *(state.get("agent_trace") or []),
        {
            "iteration": iteration,
            "agent": "expert_repair",
            "status": "failed" if repair_result.error else "completed",
            "error": repair_result.error,
        },
    ]

    if repair_result.error or repair_result.final_ir is None:
        return {
            "repair_service": service,
            "repair_metadata": repair_metadata,
            "agent_trace": trace,
            "reconciliation_status": "repair_not_possible",
            "reconciliation_stop_reason": "repair_failed",
            "unresolved_issues": _collect_unresolved_issues(
                state.get("latest_validation_report") or {}
            ),
        }

    return {
        "repair_service": service,
        "repair_metadata": repair_metadata,
        "agent_trace": trace,
        "current_final_ir": deepcopy(repair_result.final_ir),
        "validation_result": None,
    }


def _finish_reconciliation(state: EnsembleGraphState) -> EnsembleGraphState:
    latest_report = state.get("latest_validation_report") or {}
    status = state.get("reconciliation_status") or "repair_not_possible"
    stop_reason = state.get("reconciliation_stop_reason") or status
    unresolved_issues = state.get("unresolved_issues")
    if unresolved_issues is None:
        unresolved_issues = [] if latest_report.get("passed") else _collect_unresolved_issues(latest_report)

    reconciliation = AgenticReconciliationResult(
        final_ir=deepcopy(state.get("current_final_ir") or {}),
        validation_report=latest_report,
        iterations=int(state.get("reconciliation_iterations", 0) or 0),
        status=status,
        stop_reason=stop_reason,
        repair_metadata=deepcopy(state.get("repair_metadata") or {
            "attempts": [],
            "max_iterations": MAX_AGENT_ITERATIONS,
        }),
        agent_trace=list(state.get("agent_trace") or []),
        unresolved_issues=list(unresolved_issues or []),
    )
    return {
        "reconciliation": reconciliation,
        "final_validation_report": dict(reconciliation.validation_report or {}),
    }


def _build_multi_agent_result(state: EnsembleGraphState) -> EnsembleGraphState:
    return {
        "multi_agent_result": MultiAgentGenerationResult(
            orchestration=state["orchestration_result"],
            expert_review=state["expert_review"],
            selected_candidate=state.get("selected_candidate"),
            initial_validation_result=state.get("initial_validation_result"),
            reconciliation=state.get("reconciliation"),
            final_validation_report=state.get("final_validation_report"),
        )
    }


def _route_after_selection(state: EnsembleGraphState) -> str:
    selected_candidate = state.get("selected_candidate")
    if selected_candidate is None or not selected_candidate.final_ir:
        return "build_multi_agent_result"
    return "final_validate"


def _route_after_reconciliation_decision(state: EnsembleGraphState) -> ReconciliationRoute:
    decision = state.get("reconciliation_decision")
    if not decision or decision.action != "REPAIR":
        return "finish_reconciliation"
    if state.get("reconciliation_status"):
        return "finish_reconciliation"
    return "expert_repair"


def _route_after_expert_repair(state: EnsembleGraphState) -> str:
    if state.get("reconciliation_status"):
        return "finish_reconciliation"
    return "final_validate"


def _reconciliation_context(state: EnsembleGraphState) -> dict:
    selected_candidate = state.get("selected_candidate")
    expert_review = state["expert_review"]
    return {
        "selected_candidate_id": selected_candidate.candidate_id if selected_candidate else None,
        "class_diagram": selected_candidate.class_diagram if selected_candidate else None,
        "er_diagram": selected_candidate.er_diagram if selected_candidate else None,
        "sequence_diagrams": selected_candidate.sequence_diagrams if selected_candidate else None,
        "expert_review": {
            "reason": expert_review.reason,
            "confidence": expert_review.confidence,
            "fallback_used": expert_review.fallback_used,
        },
    }
