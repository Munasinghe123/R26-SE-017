from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Literal

from Services.artifactRepair import ArtifactRepairConfig, ArtifactRepairService
from graph.candidate_prompts import (
    build_class_prompt,
    build_er_prompt,
    build_sequence_prompt,
    build_unified_lld_prompt,
)
from llm.provider import LLMProvider, LLMResponse
from utils.jsonCleaner import clean_json_response
from validators.stage_validators import (
    validate_class_diagram,
    validate_er_diagram,
    validate_sequence_diagrams,
)


CandidateStatus = Literal["valid", "invalid", "failed"]
MAX_REPAIR_ATTEMPTS = int(os.getenv("MAX_REPAIR_ATTEMPTS", "2"))


@dataclass
class CandidateConfig:
    candidate_id: str
    provider: str
    model: str
    temperature: float = 0
    max_tokens: int = 3500


@dataclass
class StageMetrics:
    provider: str = ""
    model: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None
    model_call_count: int = 0


@dataclass
class CandidateMetrics:
    stages: dict[str, StageMetrics] = field(default_factory=dict)
    total_tokens: int | None = None
    total_latency_ms: float = 0
    model_call_count: int = 0


@dataclass
class CandidateState:
    candidate_id: str
    provider: str
    model: str
    status: CandidateStatus = "failed"

    class_response: str = ""
    class_diagram: dict | None = None
    class_validation: dict | None = None

    er_response: str = ""
    er_diagram: dict | None = None
    er_validation: dict | None = None

    sequence_response: str = ""
    sequence_diagrams: list[dict] | None = None
    sequence_validation: dict | None = None

    final_ir: dict | None = None
    repair_metadata: dict[str, dict] = field(default_factory=dict)
    parse_errors: list[dict] = field(default_factory=list)
    provider_errors: list[dict] = field(default_factory=list)
    metrics: CandidateMetrics = field(default_factory=CandidateMetrics)


def run_candidate(
    config: CandidateConfig,
    requirements: str,
    requirement_ids: list[str] | None = None,
    provider: LLMProvider | None = None,
) -> CandidateState:
    state = CandidateState(
        candidate_id=config.candidate_id,
        provider=config.provider,
        model=config.model,
    )
    if provider is None:
        from llm.factory import get_llm_provider

        llm_provider = get_llm_provider(config.provider)
    else:
        llm_provider = provider

    unified_prompt = build_unified_lld_prompt(requirements, requirement_ids)
    response = _complete_stage(
        state,
        config,
        llm_provider,
        "unified",
        [
            {
                "role": "system",
                "content": "You are a Principal Software Architect. Return only valid JSON for Low-Level Design (class_diagram, er_diagram, sequence_diagrams).",
            },
            {
                "role": "user",
                "content": unified_prompt,
            },
        ],
    )
    if response is None or not response.content:
        return state

    parsed_json = clean_json_response(response.content)
    if not isinstance(parsed_json, dict):
        state.parse_errors.append({"stage": "unified", "error": "Output was not a JSON object"})
        return state

    state.class_diagram = parsed_json.get("class_diagram") or {}
    state.er_diagram = parsed_json.get("er_diagram") or {}
    state.sequence_diagrams = parsed_json.get("sequence_diagrams") or []

    state.final_ir = {
        "class_diagram": state.class_diagram,
        "er_diagram": state.er_diagram,
        "sequence_diagrams": state.sequence_diagrams,
    }
    state.status = "valid"
    return state


def _validate_and_repair_stage(
    *,
    state: CandidateState,
    repair_service: ArtifactRepairService,
    stage: Literal["class", "er", "sequence"],
    artifact,
    requirements: str,
    dependencies: dict,
    validator,
):
    initial_validation = validator(artifact)
    current_artifact = artifact
    current_validation = initial_validation
    repair_errors: list[dict] = []
    repair_attempts = 0

    while not current_validation.get("passed") and repair_attempts < repair_service.config.max_attempts:
        repair_attempts += 1
        repair_result = repair_service.repair(
            stage=stage,
            artifact=current_artifact,
            validation_result=current_validation,
            requirements=requirements,
            dependencies=dependencies,
        )
        if repair_result.metrics:
            _record_repair_metrics(state.metrics, stage, repair_attempts, repair_result.metrics)
        if repair_result.error:
            repair_errors.append(repair_result.error)
            break
        if repair_result.artifact is None:
            repair_errors.append({
                "stage": stage,
                "error_type": "InvalidRepairOutput",
                "message": "Repair returned no artifact.",
            })
            break

        current_artifact = repair_result.artifact
        current_validation = validator(current_artifact)

    repair_success = bool(
        repair_attempts > 0
        and not initial_validation.get("passed")
        and current_validation.get("passed")
    )
    state.repair_metadata[stage] = {
        "initial_validation": initial_validation,
        "final_validation": current_validation,
        "repair_attempts": repair_attempts,
        "repair_success": repair_success,
        "repair_errors": repair_errors,
        "max_repair_attempts": repair_service.config.max_attempts,
    }
    return current_artifact, current_validation


def _complete_stage(
    state: CandidateState,
    config: CandidateConfig,
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
        state.provider_errors.append({
            "stage": stage,
            "message": str(exc),
            "error_type": exc.__class__.__name__,
        })
        return None

    _record_stage_metrics(state.metrics, stage, response)
    return response


def _parse_stage_object(
    state: CandidateState,
    stage: str,
    content: str,
    expected_key: str,
):
    try:
        parsed = clean_json_response(content)
    except json.JSONDecodeError as exc:
        state.status = "failed"
        state.parse_errors.append({
            "stage": stage,
            "message": str(exc),
        })
        return None

    value = parsed.get(expected_key) if isinstance(parsed, dict) else None
    if value is None:
        state.status = "failed"
        state.parse_errors.append({
            "stage": stage,
            "message": f"Missing expected key '{expected_key}'.",
        })
        return None
    return value


def _record_stage_metrics(metrics: CandidateMetrics, stage: str, response: LLMResponse) -> None:
    metrics.stages[stage] = StageMetrics(
        provider=response.provider,
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        total_tokens=response.total_tokens,
        latency_ms=response.latency_ms,
        model_call_count=1,
    )
    metrics.model_call_count += 1

    if response.latency_ms is not None:
        metrics.total_latency_ms += response.latency_ms

    if response.total_tokens is not None:
        metrics.total_tokens = (metrics.total_tokens or 0) + response.total_tokens


def _record_repair_metrics(
    metrics: CandidateMetrics,
    stage: str,
    attempt: int,
    repair_metrics: dict,
) -> None:
    metrics.stages[f"{stage}_repair_{attempt}"] = StageMetrics(
        provider=repair_metrics.get("provider", ""),
        model=repair_metrics.get("model", ""),
        input_tokens=repair_metrics.get("input_tokens"),
        output_tokens=repair_metrics.get("output_tokens"),
        total_tokens=repair_metrics.get("total_tokens"),
        latency_ms=repair_metrics.get("latency_ms"),
        model_call_count=1,
    )
    metrics.model_call_count += 1

    latency_ms = repair_metrics.get("latency_ms")
    if latency_ms is not None:
        metrics.total_latency_ms += latency_ms

    total_tokens = repair_metrics.get("total_tokens")
    if total_tokens is not None:
        metrics.total_tokens = (metrics.total_tokens or 0) + total_tokens


def _all_stage_validations_passed(state: CandidateState) -> bool:
    return all([
        bool((state.class_validation or {}).get("passed")),
        bool((state.er_validation or {}).get("passed")),
        bool((state.sequence_validation or {}).get("passed")),
    ])
