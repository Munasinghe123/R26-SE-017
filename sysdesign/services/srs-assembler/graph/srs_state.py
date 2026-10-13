from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, TypedDict, Any

from llm.provider import LLMProvider, LLMResponse
from services.artifact_repair import ArtifactRepairService

SRSStatus = Literal["valid", "invalid", "failed"]
StageName = Literal["overview", "functional", "non_functional", "traceability"]
MAX_REPAIR_ATTEMPTS = int(os.getenv("MAX_REPAIR_ATTEMPTS", "2"))


@dataclass
class SRSConfig:
    job_id: str
    project_name: str
    provider: str = "openrouter"
    model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")
    temperature: float = 0.0
    max_tokens: int = 3500
    max_repair_attempts: int = 2


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
class SRSMetrics:
    stages: dict[str, StageMetrics] = field(default_factory=dict)
    total_tokens: int | None = None
    total_latency_ms: float = 0.0
    model_call_count: int = 0


@dataclass
class SRSState:
    job_id: str
    project_name: str
    status: SRSStatus = "failed"

    # Inputs
    raw_requirements: dict[str, Any] = field(default_factory=dict)
    hld_annex: dict[str, Any] | None = None
    lld_annex: dict[str, Any] | None = None
    ui_annex: dict[str, Any] | None = None

    # Overview Stage
    overview_response: str = ""
    overview_section: dict[str, Any] | None = None
    overview_validation: dict[str, Any] | None = None

    # Functional Requirements Stage
    functional_response: str = ""
    functional_section: list[dict[str, Any]] | None = None
    functional_validation: dict[str, Any] | None = None

    # Non-Functional Requirements Stage
    non_functional_response: str = ""
    non_functional_section: list[dict[str, Any]] | None = None
    non_functional_validation: dict[str, Any] | None = None

    # Traceability Matrix Stage
    traceability_response: str = ""
    traceability_matrix: list[dict[str, Any]] | None = None
    traceability_validation: dict[str, Any] | None = None

    # Final Output
    final_ir: dict[str, Any] | None = None
    final_srs_markdown: str = ""
    repair_metadata: dict[str, dict] = field(default_factory=dict)
    parse_errors: list[dict] = field(default_factory=list)
    provider_errors: list[dict] = field(default_factory=list)
    metrics: SRSMetrics = field(default_factory=SRSMetrics)


class SRSGraphState(TypedDict):
    config: SRSConfig
    requirements: dict[str, Any]
    requirement_ids: list[str]
    nfr_ids: list[str]
    annexes: dict[str, Any]
    provider: LLMProvider
    repair_service: ArtifactRepairService
    srs: SRSState
    repair_attempts: dict[str, int]
    repair_errors: dict[str, list[dict]]
    initial_validations: dict[str, dict]
    repair_blocked: dict[str, bool]


def record_stage_metrics(metrics: SRSMetrics, stage: str, response: LLMResponse) -> None:
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


def record_repair_metrics(
    metrics: SRSMetrics, stage: str, attempt: int, repair_metrics: dict
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


def all_stage_validations_passed(state: SRSState) -> bool:
    return all(
        [
            bool((state.overview_validation or {}).get("passed")),
            bool((state.functional_validation or {}).get("passed")),
            bool((state.non_functional_validation or {}).get("passed")),
            bool((state.traceability_validation or {}).get("passed")),
        ]
    )
