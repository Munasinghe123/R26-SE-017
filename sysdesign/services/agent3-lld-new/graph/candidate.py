from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Literal

from llm.provider import LLMProvider, LLMResponse
from utils.jsonCleaner import clean_json_response

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
    from graph.candidate_graph import run_candidate_graph

    return run_candidate_graph(
        config=config,
        requirements=requirements,
        requirement_ids=requirement_ids,
        provider=provider,
    )


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
        state.provider_errors.append(
            {
                "stage": stage,
                "message": str(exc),
                "error_type": exc.__class__.__name__,
            }
        )
        return None

    _record_stage_metrics(state.metrics, stage, response)
    return response


async def _acomplete_stage(
    state: CandidateState,
    config: CandidateConfig,
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
        state.provider_errors.append(
            {
                "stage": stage,
                "message": str(exc),
                "error_type": exc.__class__.__name__,
            }
        )
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
        state.parse_errors.append(
            {
                "stage": stage,
                "message": str(exc),
            }
        )
        return None

    value = parsed.get(expected_key) if isinstance(parsed, dict) else None
    if value is None:
        state.status = "failed"
        state.parse_errors.append(
            {
                "stage": stage,
                "message": f"Missing expected key '{expected_key}'.",
            }
        )
        return None
    return value


def _record_stage_metrics(
    metrics: CandidateMetrics, stage: str, response: LLMResponse
) -> None:
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
    return all(
        [
            bool((state.class_validation or {}).get("passed")),
            bool((state.er_validation or {}).get("passed")),
            bool((state.sequence_validation or {}).get("passed")),
        ]
    )
