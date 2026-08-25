from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from graph.candidate_prompts import (
    build_class_prompt,
    build_er_prompt,
    build_sequence_prompt,
)
from llm.factory import get_llm_provider
from llm.provider import LLMProvider, LLMResponse
from utils.jsonCleaner import clean_json_response
from validators.stage_validators import (
    validate_class_diagram,
    validate_er_diagram,
    validate_sequence_diagrams,
)


CandidateStatus = Literal["valid", "invalid", "failed"]


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
    llm_provider = provider or get_llm_provider(config.provider)

    class_response = _complete_stage(
        state,
        config,
        llm_provider,
        "class",
        [
            {
                "role": "system",
                "content": "You generate only UML class diagram JSON.",
            },
            {
                "role": "user",
                "content": build_class_prompt(requirements, requirement_ids),
            },
        ],
    )
    if class_response is None:
        return state
    state.class_response = class_response.content
    state.class_diagram = _parse_stage_object(state, "class", state.class_response, "class_diagram")
    if state.class_diagram is None:
        return state
    state.class_validation = validate_class_diagram(state.class_diagram)

    er_response = _complete_stage(
        state,
        config,
        llm_provider,
        "er",
        [
            {
                "role": "system",
                "content": "You generate only ER diagram JSON from the provided class diagram.",
            },
            {
                "role": "user",
                "content": build_er_prompt(requirements, state.class_diagram),
            },
        ],
    )
    if er_response is None:
        return state
    state.er_response = er_response.content
    state.er_diagram = _parse_stage_object(state, "er", state.er_response, "er_diagram")
    if state.er_diagram is None:
        return state
    state.er_validation = validate_er_diagram(state.er_diagram, state.class_diagram)

    sequence_response = _complete_stage(
        state,
        config,
        llm_provider,
        "sequence",
        [
            {
                "role": "system",
                "content": "You generate only sequence diagram JSON from the provided class and ER diagrams.",
            },
            {
                "role": "user",
                "content": build_sequence_prompt(requirements, state.class_diagram, state.er_diagram),
            },
        ],
    )
    if sequence_response is None:
        return state
    state.sequence_response = sequence_response.content
    state.sequence_diagrams = _parse_stage_object(
        state,
        "sequence",
        state.sequence_response,
        "sequence_diagrams",
    )
    if state.sequence_diagrams is None:
        return state
    state.sequence_validation = validate_sequence_diagrams(state.sequence_diagrams, state.class_diagram)

    state.final_ir = {
        "class_diagram": state.class_diagram,
        "er_diagram": state.er_diagram,
        "sequence_diagrams": state.sequence_diagrams,
    }
    state.status = "valid" if _all_stage_validations_passed(state) else "invalid"
    return state


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


def _all_stage_validations_passed(state: CandidateState) -> bool:
    return all([
        bool((state.class_validation or {}).get("passed")),
        bool((state.er_validation or {}).get("passed")),
        bool((state.sequence_validation or {}).get("passed")),
    ])
