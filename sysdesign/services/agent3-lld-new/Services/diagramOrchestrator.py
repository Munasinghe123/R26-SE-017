from __future__ import annotations

from dataclasses import dataclass

from graph.candidate import CandidateState


@dataclass
class OrchestrationResult:
    candidates: dict[str, CandidateState]
    total_agents: int
    completed_agents: int
    valid_agents: int
    invalid_agents: int
    failed_agents: int
    total_model_calls: int
    total_tokens: int | None
    total_latency_ms: float | None


def _build_orchestration_result(
    total_agents: int,
    candidates: dict[str, CandidateState],
) -> OrchestrationResult:
    total_model_calls = 0
    total_tokens = 0
    saw_token_metric = False
    total_latency_ms = 0.0
    saw_latency_metric = False

    for candidate in candidates.values():
        total_model_calls += candidate.metrics.model_call_count

        if candidate.metrics.total_tokens is not None:
            saw_token_metric = True
            total_tokens += candidate.metrics.total_tokens

        if candidate.metrics.total_latency_ms is not None:
            saw_latency_metric = True
            total_latency_ms += candidate.metrics.total_latency_ms

    return OrchestrationResult(
        candidates=candidates,
        total_agents=total_agents,
        completed_agents=len(candidates),
        valid_agents=sum(1 for candidate in candidates.values() if candidate.status == "valid"),
        invalid_agents=sum(1 for candidate in candidates.values() if candidate.status == "invalid"),
        failed_agents=sum(1 for candidate in candidates.values() if candidate.status == "failed"),
        total_model_calls=total_model_calls,
        total_tokens=total_tokens if saw_token_metric else None,
        total_latency_ms=total_latency_ms if saw_latency_metric else None,
    )


def _safe_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message[:300] if message else exc.__class__.__name__
