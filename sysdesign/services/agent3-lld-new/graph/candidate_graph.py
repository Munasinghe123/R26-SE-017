from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from Services.artifactRepair import ArtifactRepairConfig, ArtifactRepairService
from graph.candidate_prompts import (
    build_class_prompt,
    build_er_prompt,
    build_sequence_prompt,
)
from llm.provider import LLMProvider
from validators.stage_validators import (
    validate_class_diagram,
    validate_er_diagram,
    validate_sequence_diagrams,
)


StageName = Literal["class", "er", "sequence"]
RouteName = Literal[
    "mark_failed",
    "validate_class",
    "validate_er",
    "validate_sequence",
    "repair_class",
    "repair_er",
    "repair_sequence",
    "generate_er",
    "generate_sequence",
    "assemble_final_ir",
]


class CandidateGraphState(TypedDict):
    config: object
    requirements: str
    requirement_ids: list[str]
    provider: LLMProvider
    repair_service: ArtifactRepairService
    candidate: object
    repair_attempts: dict[str, int]
    repair_errors: dict[str, list[dict]]
    initial_validations: dict[str, dict]
    repair_blocked: dict[str, bool]


def run_candidate_graph(
    config,
    requirements: str,
    requirement_ids: list[str] | None = None,
    provider: LLMProvider | None = None,
):
    from graph.candidate import CandidateState, MAX_REPAIR_ATTEMPTS
    from llm.factory import get_llm_provider

    llm_provider = provider or get_llm_provider(config.provider)
    repair_service = ArtifactRepairService(
        config=ArtifactRepairConfig(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_attempts=MAX_REPAIR_ATTEMPTS,
        ),
        provider=llm_provider,
    )
    initial_state: CandidateGraphState = {
        "config": config,
        "requirements": requirements,
        "requirement_ids": requirement_ids or [],
        "provider": llm_provider,
        "repair_service": repair_service,
        "candidate": CandidateState(
            candidate_id=config.candidate_id,
            provider=config.provider,
            model=config.model,
        ),
        "repair_attempts": {"class": 0, "er": 0, "sequence": 0},
        "repair_errors": {"class": [], "er": [], "sequence": []},
        "initial_validations": {},
        "repair_blocked": {"class": False, "er": False, "sequence": False},
    }
    return build_candidate_graph().invoke(initial_state)["candidate"]


async def arun_candidate_graph(
    config,
    requirements: str,
    requirement_ids: list[str] | None = None,
    provider: LLMProvider | None = None,
):
    from graph.candidate import CandidateState, MAX_REPAIR_ATTEMPTS
    from llm.factory import get_llm_provider

    llm_provider = provider or get_llm_provider(config.provider)
    repair_service = ArtifactRepairService(
        config=ArtifactRepairConfig(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_attempts=MAX_REPAIR_ATTEMPTS,
        ),
        provider=llm_provider,
    )
    initial_state: CandidateGraphState = {
        "config": config,
        "requirements": requirements,
        "requirement_ids": requirement_ids or [],
        "provider": llm_provider,
        "repair_service": repair_service,
        "candidate": CandidateState(
            candidate_id=config.candidate_id,
            provider=config.provider,
            model=config.model,
        ),
        "repair_attempts": {"class": 0, "er": 0, "sequence": 0},
        "repair_errors": {"class": [], "er": [], "sequence": []},
        "initial_validations": {},
        "repair_blocked": {"class": False, "er": False, "sequence": False},
    }
    return (await build_async_candidate_graph().ainvoke(initial_state))["candidate"]


def build_candidate_graph():
    graph = StateGraph(CandidateGraphState)

    graph.add_node("generate_class", _generate_class)
    graph.add_node("parse_class", _parse_class)
    graph.add_node("validate_class", _validate_class)
    graph.add_node("repair_class", _repair_class)
    graph.add_node("generate_er", _generate_er)
    graph.add_node("parse_er", _parse_er)
    graph.add_node("validate_er", _validate_er)
    graph.add_node("repair_er", _repair_er)
    graph.add_node("generate_sequence", _generate_sequence)
    graph.add_node("parse_sequence", _parse_sequence)
    graph.add_node("validate_sequence", _validate_sequence)
    graph.add_node("repair_sequence", _repair_sequence)
    graph.add_node("assemble_final_ir", _assemble_final_ir)
    graph.add_node("mark_failed", _mark_failed)

    graph.add_edge(START, "generate_class")
    graph.add_conditional_edges(
        "generate_class",
        _route_after_generation("class", "parse_class"),
        {"mark_failed": "mark_failed", "parse_class": "parse_class"},
    )
    graph.add_conditional_edges(
        "parse_class",
        _route_after_parse("class", "validate_class"),
        {"mark_failed": "mark_failed", "validate_class": "validate_class"},
    )
    graph.add_conditional_edges(
        "validate_class",
        _route_after_validation("class", "repair_class", "generate_er"),
        {"repair_class": "repair_class", "generate_er": "generate_er"},
    )
    graph.add_conditional_edges(
        "repair_class",
        _route_after_repair("class", "validate_class", "generate_er"),
        {"validate_class": "validate_class", "generate_er": "generate_er"},
    )

    graph.add_conditional_edges(
        "generate_er",
        _route_after_generation("er", "parse_er"),
        {"mark_failed": "mark_failed", "parse_er": "parse_er"},
    )
    graph.add_conditional_edges(
        "parse_er",
        _route_after_parse("er", "validate_er"),
        {"mark_failed": "mark_failed", "validate_er": "validate_er"},
    )
    graph.add_conditional_edges(
        "validate_er",
        _route_after_validation("er", "repair_er", "generate_sequence"),
        {"repair_er": "repair_er", "generate_sequence": "generate_sequence"},
    )
    graph.add_conditional_edges(
        "repair_er",
        _route_after_repair("er", "validate_er", "generate_sequence"),
        {"validate_er": "validate_er", "generate_sequence": "generate_sequence"},
    )

    graph.add_conditional_edges(
        "generate_sequence",
        _route_after_generation("sequence", "parse_sequence"),
        {"mark_failed": "mark_failed", "parse_sequence": "parse_sequence"},
    )
    graph.add_conditional_edges(
        "parse_sequence",
        _route_after_parse("sequence", "validate_sequence"),
        {"mark_failed": "mark_failed", "validate_sequence": "validate_sequence"},
    )
    graph.add_conditional_edges(
        "validate_sequence",
        _route_after_validation("sequence", "repair_sequence", "assemble_final_ir"),
        {"repair_sequence": "repair_sequence", "assemble_final_ir": "assemble_final_ir"},
    )
    graph.add_conditional_edges(
        "repair_sequence",
        _route_after_repair("sequence", "validate_sequence", "assemble_final_ir"),
        {"validate_sequence": "validate_sequence", "assemble_final_ir": "assemble_final_ir"},
    )

    graph.add_edge("assemble_final_ir", END)
    graph.add_edge("mark_failed", END)
    return graph.compile()


def build_async_candidate_graph():
    graph = StateGraph(CandidateGraphState)

    graph.add_node("generate_class", _agenerate_class)
    graph.add_node("parse_class", _parse_class)
    graph.add_node("validate_class", _validate_class)
    graph.add_node("repair_class", _arepair_class)
    graph.add_node("generate_er", _agenerate_er)
    graph.add_node("parse_er", _parse_er)
    graph.add_node("validate_er", _validate_er)
    graph.add_node("repair_er", _arepair_er)
    graph.add_node("generate_sequence", _agenerate_sequence)
    graph.add_node("parse_sequence", _parse_sequence)
    graph.add_node("validate_sequence", _validate_sequence)
    graph.add_node("repair_sequence", _arepair_sequence)
    graph.add_node("assemble_final_ir", _assemble_final_ir)
    graph.add_node("mark_failed", _mark_failed)

    graph.add_edge(START, "generate_class")
    graph.add_conditional_edges(
        "generate_class",
        _route_after_generation("class", "parse_class"),
        {"mark_failed": "mark_failed", "parse_class": "parse_class"},
    )
    graph.add_conditional_edges(
        "parse_class",
        _route_after_parse("class", "validate_class"),
        {"mark_failed": "mark_failed", "validate_class": "validate_class"},
    )
    graph.add_conditional_edges(
        "validate_class",
        _route_after_validation("class", "repair_class", "generate_er"),
        {"repair_class": "repair_class", "generate_er": "generate_er"},
    )
    graph.add_conditional_edges(
        "repair_class",
        _route_after_repair("class", "validate_class", "generate_er"),
        {"validate_class": "validate_class", "generate_er": "generate_er"},
    )

    graph.add_conditional_edges(
        "generate_er",
        _route_after_generation("er", "parse_er"),
        {"mark_failed": "mark_failed", "parse_er": "parse_er"},
    )
    graph.add_conditional_edges(
        "parse_er",
        _route_after_parse("er", "validate_er"),
        {"mark_failed": "mark_failed", "validate_er": "validate_er"},
    )
    graph.add_conditional_edges(
        "validate_er",
        _route_after_validation("er", "repair_er", "generate_sequence"),
        {"repair_er": "repair_er", "generate_sequence": "generate_sequence"},
    )
    graph.add_conditional_edges(
        "repair_er",
        _route_after_repair("er", "validate_er", "generate_sequence"),
        {"validate_er": "validate_er", "generate_sequence": "generate_sequence"},
    )

    graph.add_conditional_edges(
        "generate_sequence",
        _route_after_generation("sequence", "parse_sequence"),
        {"mark_failed": "mark_failed", "parse_sequence": "parse_sequence"},
    )
    graph.add_conditional_edges(
        "parse_sequence",
        _route_after_parse("sequence", "validate_sequence"),
        {"mark_failed": "mark_failed", "validate_sequence": "validate_sequence"},
    )
    graph.add_conditional_edges(
        "validate_sequence",
        _route_after_validation("sequence", "repair_sequence", "assemble_final_ir"),
        {"repair_sequence": "repair_sequence", "assemble_final_ir": "assemble_final_ir"},
    )
    graph.add_conditional_edges(
        "repair_sequence",
        _route_after_repair("sequence", "validate_sequence", "assemble_final_ir"),
        {"validate_sequence": "validate_sequence", "assemble_final_ir": "assemble_final_ir"},
    )

    graph.add_edge("assemble_final_ir", END)
    graph.add_edge("mark_failed", END)
    return graph.compile()


def _generate_class(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _complete_stage

    candidate = graph_state["candidate"]
    response = _complete_stage(
        candidate,
        graph_state["config"],
        graph_state["provider"],
        "class",
        [
            {"role": "system", "content": "You generate only UML class diagram JSON."},
            {
                "role": "user",
                "content": build_class_prompt(
                    graph_state["requirements"],
                    graph_state["requirement_ids"],
                ),
            },
        ],
    )
    if response is not None:
        candidate.class_response = response.content
    return {"candidate": candidate}


async def _agenerate_class(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _acomplete_stage

    candidate = graph_state["candidate"]
    response = await _acomplete_stage(
        candidate,
        graph_state["config"],
        graph_state["provider"],
        "class",
        [
            {"role": "system", "content": "You generate only UML class diagram JSON."},
            {
                "role": "user",
                "content": build_class_prompt(
                    graph_state["requirements"],
                    graph_state["requirement_ids"],
                ),
            },
        ],
    )
    if response is not None:
        candidate.class_response = response.content
    return {"candidate": candidate}


def _parse_class(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _parse_stage_object

    candidate = graph_state["candidate"]
    candidate.class_diagram = _parse_stage_object(
        candidate,
        "class",
        candidate.class_response,
        "class_diagram",
    )
    return {"candidate": candidate}


def _validate_class(graph_state: CandidateGraphState) -> CandidateGraphState:
    return _validate_stage(graph_state, "class", validate_class_diagram)


def _repair_class(graph_state: CandidateGraphState) -> CandidateGraphState:
    return _repair_stage(graph_state, "class", graph_state["candidate"].class_diagram, {})


async def _arepair_class(graph_state: CandidateGraphState) -> CandidateGraphState:
    return await _arepair_stage(graph_state, "class", graph_state["candidate"].class_diagram, {})


def _generate_er(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _complete_stage

    candidate = graph_state["candidate"]
    response = _complete_stage(
        candidate,
        graph_state["config"],
        graph_state["provider"],
        "er",
        [
            {
                "role": "system",
                "content": "You generate only ER diagram JSON from the provided class diagram.",
            },
            {
                "role": "user",
                "content": build_er_prompt(
                    graph_state["requirements"],
                    candidate.class_diagram,
                ),
            },
        ],
    )
    if response is not None:
        candidate.er_response = response.content
    return {"candidate": candidate}


async def _agenerate_er(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _acomplete_stage

    candidate = graph_state["candidate"]
    response = await _acomplete_stage(
        candidate,
        graph_state["config"],
        graph_state["provider"],
        "er",
        [
            {
                "role": "system",
                "content": "You generate only ER diagram JSON from the provided class diagram.",
            },
            {
                "role": "user",
                "content": build_er_prompt(
                    graph_state["requirements"],
                    candidate.class_diagram,
                ),
            },
        ],
    )
    if response is not None:
        candidate.er_response = response.content
    return {"candidate": candidate}


def _parse_er(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _parse_stage_object

    candidate = graph_state["candidate"]
    candidate.er_diagram = _parse_stage_object(
        candidate,
        "er",
        candidate.er_response,
        "er_diagram",
    )
    return {"candidate": candidate}


def _validate_er(graph_state: CandidateGraphState) -> CandidateGraphState:
    candidate = graph_state["candidate"]
    return _validate_stage(
        graph_state,
        "er",
        lambda artifact: validate_er_diagram(artifact, candidate.class_diagram),
    )


def _repair_er(graph_state: CandidateGraphState) -> CandidateGraphState:
    candidate = graph_state["candidate"]
    return _repair_stage(
        graph_state,
        "er",
        candidate.er_diagram,
        {"class_diagram": candidate.class_diagram},
    )


async def _arepair_er(graph_state: CandidateGraphState) -> CandidateGraphState:
    candidate = graph_state["candidate"]
    return await _arepair_stage(
        graph_state,
        "er",
        candidate.er_diagram,
        {"class_diagram": candidate.class_diagram},
    )


def _generate_sequence(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _complete_stage

    candidate = graph_state["candidate"]
    response = _complete_stage(
        candidate,
        graph_state["config"],
        graph_state["provider"],
        "sequence",
        [
            {
                "role": "system",
                "content": "You generate only sequence diagram JSON from the provided class and ER diagrams.",
            },
            {
                "role": "user",
                "content": build_sequence_prompt(
                    graph_state["requirements"],
                    candidate.class_diagram,
                    candidate.er_diagram,
                ),
            },
        ],
    )
    if response is not None:
        candidate.sequence_response = response.content
    return {"candidate": candidate}


async def _agenerate_sequence(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _acomplete_stage

    candidate = graph_state["candidate"]
    response = await _acomplete_stage(
        candidate,
        graph_state["config"],
        graph_state["provider"],
        "sequence",
        [
            {
                "role": "system",
                "content": "You generate only sequence diagram JSON from the provided class and ER diagrams.",
            },
            {
                "role": "user",
                "content": build_sequence_prompt(
                    graph_state["requirements"],
                    candidate.class_diagram,
                    candidate.er_diagram,
                ),
            },
        ],
    )
    if response is not None:
        candidate.sequence_response = response.content
    return {"candidate": candidate}


def _parse_sequence(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _parse_stage_object

    candidate = graph_state["candidate"]
    candidate.sequence_diagrams = _parse_stage_object(
        candidate,
        "sequence",
        candidate.sequence_response,
        "sequence_diagrams",
    )
    return {"candidate": candidate}


def _validate_sequence(graph_state: CandidateGraphState) -> CandidateGraphState:
    candidate = graph_state["candidate"]
    return _validate_stage(
        graph_state,
        "sequence",
        lambda artifact: validate_sequence_diagrams(artifact, candidate.class_diagram),
    )


def _repair_sequence(graph_state: CandidateGraphState) -> CandidateGraphState:
    candidate = graph_state["candidate"]
    return _repair_stage(
        graph_state,
        "sequence",
        candidate.sequence_diagrams,
        {
            "class_diagram": candidate.class_diagram,
            "er_diagram": candidate.er_diagram,
        },
    )


async def _arepair_sequence(graph_state: CandidateGraphState) -> CandidateGraphState:
    candidate = graph_state["candidate"]
    return await _arepair_stage(
        graph_state,
        "sequence",
        candidate.sequence_diagrams,
        {
            "class_diagram": candidate.class_diagram,
            "er_diagram": candidate.er_diagram,
        },
    )


def _validate_stage(graph_state: CandidateGraphState, stage: StageName, validator):
    candidate = graph_state["candidate"]
    artifact = _artifact_for(candidate, stage)
    validation = validator(artifact)
    _set_validation(candidate, stage, validation)
    graph_state["initial_validations"].setdefault(stage, validation)
    _write_repair_metadata(graph_state, stage, validation)
    return {
        "candidate": candidate,
        "initial_validations": graph_state["initial_validations"],
    }


def _repair_stage(
    graph_state: CandidateGraphState,
    stage: StageName,
    artifact,
    dependencies: dict,
):
    from graph.candidate import _record_repair_metrics

    candidate = graph_state["candidate"]
    repair_attempts = dict(graph_state["repair_attempts"])
    repair_errors = dict(graph_state["repair_errors"])
    repair_blocked = dict(graph_state["repair_blocked"])

    repair_attempts[stage] = repair_attempts.get(stage, 0) + 1
    repair_result = graph_state["repair_service"].repair(
        stage=stage,
        artifact=artifact,
        validation_result=_validation_for(candidate, stage),
        requirements=graph_state["requirements"],
        dependencies=dependencies,
    )
    if repair_result.metrics:
        _record_repair_metrics(
            candidate.metrics,
            stage,
            repair_attempts[stage],
            repair_result.metrics,
        )
    if repair_result.error:
        repair_errors[stage] = [*repair_errors.get(stage, []), repair_result.error]
        repair_blocked[stage] = True
        _write_repair_metadata(graph_state, stage, _validation_for(candidate, stage), repair_attempts, repair_errors)
        return {
            "candidate": candidate,
            "repair_attempts": repair_attempts,
            "repair_errors": repair_errors,
            "repair_blocked": repair_blocked,
        }
    if repair_result.artifact is None:
        repair_errors[stage] = [
            *repair_errors.get(stage, []),
            {
                "stage": stage,
                "error_type": "InvalidRepairOutput",
                "message": "Repair returned no artifact.",
            },
        ]
        repair_blocked[stage] = True
        _write_repair_metadata(graph_state, stage, _validation_for(candidate, stage), repair_attempts, repair_errors)
        return {
            "candidate": candidate,
            "repair_attempts": repair_attempts,
            "repair_errors": repair_errors,
            "repair_blocked": repair_blocked,
        }

    _set_artifact(candidate, stage, repair_result.artifact)
    return {
        "candidate": candidate,
        "repair_attempts": repair_attempts,
        "repair_errors": repair_errors,
    }


async def _arepair_stage(
    graph_state: CandidateGraphState,
    stage: StageName,
    artifact,
    dependencies: dict,
):
    from graph.candidate import _record_repair_metrics

    candidate = graph_state["candidate"]
    repair_attempts = dict(graph_state["repair_attempts"])
    repair_errors = dict(graph_state["repair_errors"])
    repair_blocked = dict(graph_state["repair_blocked"])

    repair_attempts[stage] = repair_attempts.get(stage, 0) + 1
    repair_result = await graph_state["repair_service"].arepair(
        stage=stage,
        artifact=artifact,
        validation_result=_validation_for(candidate, stage),
        requirements=graph_state["requirements"],
        dependencies=dependencies,
    )
    if repair_result.metrics:
        _record_repair_metrics(
            candidate.metrics,
            stage,
            repair_attempts[stage],
            repair_result.metrics,
        )
    if repair_result.error:
        repair_errors[stage] = [*repair_errors.get(stage, []), repair_result.error]
        repair_blocked[stage] = True
        _write_repair_metadata(graph_state, stage, _validation_for(candidate, stage), repair_attempts, repair_errors)
        return {
            "candidate": candidate,
            "repair_attempts": repair_attempts,
            "repair_errors": repair_errors,
            "repair_blocked": repair_blocked,
        }
    if repair_result.artifact is None:
        repair_errors[stage] = [
            *repair_errors.get(stage, []),
            {
                "stage": stage,
                "error_type": "InvalidRepairOutput",
                "message": "Repair returned no artifact.",
            },
        ]
        repair_blocked[stage] = True
        _write_repair_metadata(graph_state, stage, _validation_for(candidate, stage), repair_attempts, repair_errors)
        return {
            "candidate": candidate,
            "repair_attempts": repair_attempts,
            "repair_errors": repair_errors,
            "repair_blocked": repair_blocked,
        }

    _set_artifact(candidate, stage, repair_result.artifact)
    return {
        "candidate": candidate,
        "repair_attempts": repair_attempts,
        "repair_errors": repair_errors,
    }


def _assemble_final_ir(graph_state: CandidateGraphState) -> CandidateGraphState:
    from graph.candidate import _all_stage_validations_passed

    candidate = graph_state["candidate"]
    candidate.final_ir = {
        "class_diagram": candidate.class_diagram,
        "er_diagram": candidate.er_diagram,
        "sequence_diagrams": candidate.sequence_diagrams,
    }
    candidate.status = "valid" if _all_stage_validations_passed(candidate) else "invalid"
    return {"candidate": candidate}


def _mark_failed(graph_state: CandidateGraphState) -> CandidateGraphState:
    candidate = graph_state["candidate"]
    candidate.status = "failed"
    return {"candidate": candidate}


def _route_after_generation(stage: StageName, next_node: RouteName):
    def route(graph_state: CandidateGraphState) -> RouteName:
        provider_errors = graph_state["candidate"].provider_errors or []
        if provider_errors and provider_errors[-1].get("stage") == stage:
            return "mark_failed"
        return next_node

    return route


def _route_after_parse(stage: StageName, next_node: RouteName):
    def route(graph_state: CandidateGraphState) -> RouteName:
        return "mark_failed" if _artifact_for(graph_state["candidate"], stage) is None else next_node

    return route


def _route_after_validation(stage: StageName, repair_node: RouteName, next_node: RouteName):
    def route(graph_state: CandidateGraphState) -> RouteName:
        validation = _validation_for(graph_state["candidate"], stage) or {}
        if validation.get("passed"):
            return next_node
        if graph_state["repair_blocked"].get(stage):
            return next_node
        if graph_state["repair_attempts"].get(stage, 0) < graph_state["repair_service"].config.max_attempts:
            return repair_node
        return next_node

    return route


def _route_after_repair(stage: StageName, validate_node: RouteName, next_node: RouteName):
    def route(graph_state: CandidateGraphState) -> RouteName:
        return next_node if graph_state["repair_blocked"].get(stage) else validate_node

    return route


def _write_repair_metadata(
    graph_state: CandidateGraphState,
    stage: StageName,
    final_validation: dict,
    repair_attempts: dict[str, int] | None = None,
    repair_errors: dict[str, list[dict]] | None = None,
) -> None:
    candidate = graph_state["candidate"]
    attempts = repair_attempts or graph_state["repair_attempts"]
    errors = repair_errors or graph_state["repair_errors"]
    initial_validation = graph_state["initial_validations"].get(stage, final_validation)
    candidate.repair_metadata[stage] = {
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


def _artifact_for(candidate, stage: StageName):
    if stage == "class":
        return candidate.class_diagram
    if stage == "er":
        return candidate.er_diagram
    return candidate.sequence_diagrams


def _set_artifact(candidate, stage: StageName, artifact) -> None:
    if stage == "class":
        candidate.class_diagram = artifact
    elif stage == "er":
        candidate.er_diagram = artifact
    else:
        candidate.sequence_diagrams = artifact


def _validation_for(candidate, stage: StageName):
    if stage == "class":
        return candidate.class_validation
    if stage == "er":
        return candidate.er_validation
    return candidate.sequence_validation


def _set_validation(candidate, stage: StageName, validation: dict) -> None:
    if stage == "class":
        candidate.class_validation = validation
    elif stage == "er":
        candidate.er_validation = validation
    else:
        candidate.sequence_validation = validation
