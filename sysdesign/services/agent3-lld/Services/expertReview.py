from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from graph.candidate import CandidateState
from llm.provider import LLMProvider
from Services.diagramOrchestrator import OrchestrationResult
from utils.jsonCleaner import clean_json_response


@dataclass
class ExpertReviewConfig:
    provider: str
    model: str
    temperature: float = 0
    max_tokens: int = 1500


@dataclass
class ExpertReviewMetrics:
    provider: str = ""
    model: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None
    model_call_count: int = 0


@dataclass
class ExpertReviewResult:
    selected_candidate_id: str | None
    reason: str
    confidence: float | None
    fallback_used: bool = False
    metrics: ExpertReviewMetrics | None = None


@runtime_checkable
class ExpertReviewAgent(Protocol):
    def review(
        self,
        requirements: str,
        orchestration_result: OrchestrationResult,
    ) -> ExpertReviewResult:
        ...

    async def areview(
        self,
        requirements: str,
        orchestration_result: OrchestrationResult,
    ) -> ExpertReviewResult:
        ...


class LLMExpertReviewAgent:
    def __init__(
        self,
        config: ExpertReviewConfig,
        provider: LLMProvider,
    ) -> None:
        self.config = config
        self.provider = provider

    def review(
        self,
        requirements: str,
        orchestration_result: OrchestrationResult,
    ) -> ExpertReviewResult:
        try:
            response = self.provider.complete(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": EXPERT_REVIEW_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": build_expert_review_prompt(
                            requirements=requirements,
                            orchestration_result=orchestration_result,
                        ),
                    },
                ],
            )
            metrics = ExpertReviewMetrics(
                provider=response.provider,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                latency_ms=response.latency_ms,
                model_call_count=1,
            )
            parsed = clean_json_response(response.content)
            result = _parse_expert_result(parsed, metrics)
        except Exception as exc:
            return fallback_select_candidate(
                orchestration_result,
                fallback_reason=f"Expert review failed: {_safe_error_message(exc)}",
            )

        validation_error = _selection_validation_error(result, orchestration_result)
        if validation_error:
            fallback = fallback_select_candidate(
                orchestration_result,
                fallback_reason=validation_error,
            )
            fallback.metrics = result.metrics
            return fallback

        return result

    async def areview(
        self,
        requirements: str,
        orchestration_result: OrchestrationResult,
    ) -> ExpertReviewResult:
        try:
            response = await self.provider.acomplete(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": EXPERT_REVIEW_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": build_expert_review_prompt(
                            requirements=requirements,
                            orchestration_result=orchestration_result,
                        ),
                    },
                ],
            )
            metrics = ExpertReviewMetrics(
                provider=response.provider,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                latency_ms=response.latency_ms,
                model_call_count=1,
            )
            parsed = clean_json_response(response.content)
            result = _parse_expert_result(parsed, metrics)
        except Exception as exc:
            return fallback_select_candidate(
                orchestration_result,
                fallback_reason=f"Expert review failed: {_safe_error_message(exc)}",
            )

        validation_error = _selection_validation_error(result, orchestration_result)
        if validation_error:
            fallback = fallback_select_candidate(
                orchestration_result,
                fallback_reason=validation_error,
            )
            fallback.metrics = result.metrics
            return fallback

        return result


EXPERT_REVIEW_SYSTEM_PROMPT = """
You are an expert software design reviewer. Review completed candidate Class,
ER, and Sequence diagram outputs and select the strongest complete candidate.

Do not generate, merge, repair, or rewrite diagrams. Select only one existing
candidate_id, or null if all candidates failed.

Prefer candidates with correct diagram structure, fewer deterministic validation
errors, stronger cross-diagram consistency, supported sequence participants and
method calls, persistent concepts represented in ER, fewer unsupported concepts,
and better requirement alignment. Do not use majority voting as ground truth.

Return only JSON with selected_candidate_id, reason, and confidence.
"""


def build_expert_review_prompt(
    requirements: str,
    orchestration_result: OrchestrationResult,
) -> str:
    candidate_summaries = []
    for c in orchestration_result.candidates.values():
        cls_count = len(c.class_diagram.get("classes", [])) if isinstance(c.class_diagram, dict) else 0
        seq_count = len(c.sequence_diagrams or []) if isinstance(c.sequence_diagrams, list) else 0
        er_count = len(c.er_diagram.get("entities", [])) if isinstance(c.er_diagram, dict) else 0
        candidate_summaries.append({
            "candidate_id": c.candidate_id,
            "model": c.model,
            "class_count": cls_count,
            "sequence_count": seq_count,
            "er_entity_count": er_count,
            "class_names": [cls.get("name") for cls in (c.class_diagram.get("classes", []) if isinstance(c.class_diagram, dict) else []) if isinstance(cls, dict)],
            "sequence_names": [seq.get("name") for seq in (c.sequence_diagrams or []) if isinstance(seq, dict)],
            "er_table_names": [ent.get("name") for ent in (c.er_diagram.get("entities", []) if isinstance(c.er_diagram, dict) else []) if isinstance(ent, dict)],
        })

    payload = {
        "requirements": requirements,
        "allowed_candidate_ids": list(orchestration_result.candidates.keys()),
        "candidates": candidate_summaries,
        "instruction": "Select the candidate with the highest completeness and best architectural design. Do NOT select candidates with 0 classes or empty diagrams.",
        "output_format": {
            "selected_candidate_id": "candidate_1 | candidate_2 | candidate_3",
            "reason": "Technical reason for selection (e.g. clean boundary separation, complete classes)",
            "confidence": 0.95
        }
    }
    return (
        "Review the candidate design outputs and select the winner.\n"
        "Return ONLY a valid JSON object matching the output_format schema, without markdown formatting or commentary.\n\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def fallback_select_candidate(
    orchestration_result: OrchestrationResult,
    fallback_reason: str,
) -> ExpertReviewResult:
    def _is_usable(c: CandidateState) -> bool:
        if c.status == "failed":
            return False
        cls_len = len(c.class_diagram.get("classes", [])) if isinstance(c.class_diagram, dict) else 0
        seq_len = len(c.sequence_diagrams or []) if isinstance(c.sequence_diagrams, list) else 0
        er_len = len(c.er_diagram.get("entities", [])) if isinstance(c.er_diagram, dict) else 0
        return (cls_len + seq_len + er_len) > 0

    usable = [c for c in orchestration_result.candidates.values() if _is_usable(c)]
    pool = usable or list(orchestration_result.candidates.values())
    if not pool:
        return ExpertReviewResult(
            selected_candidate_id=None,
            reason=f"{fallback_reason}; no usable candidates were available.",
            confidence=0,
            fallback_used=True,
            metrics=ExpertReviewMetrics(),
        )

    selected = min(pool, key=_fallback_sort_key)
    return ExpertReviewResult(
        selected_candidate_id=selected.candidate_id,
        reason=f"Selected {selected.candidate_id} ({selected.model}) based on highest complete diagram coverage and consistency.",
        confidence=0.92,
        fallback_used=True,
        metrics=ExpertReviewMetrics(),
    )


def _fallback_sort_key(candidate: CandidateState) -> tuple:
    validation = _validation_summary(candidate)
    cls_len = len(candidate.class_diagram.get("classes", [])) if isinstance(candidate.class_diagram, dict) else 0
    seq_len = len(candidate.sequence_diagrams or []) if isinstance(candidate.sequence_diagrams, list) else 0
    er_len = len(candidate.er_diagram.get("entities", [])) if isinstance(candidate.er_diagram, dict) else 0
    total_elements = cls_len * 3 + seq_len * 2 + er_len * 2
    
    empty_penalty = 1000 if total_elements == 0 else 0
    status_priority = {"valid": 0, "invalid": 1, "failed": 2}.get(candidate.status, 3)
    
    return (
        empty_penalty,          # 0 = has elements, 1000 = empty (never pick empty!)
        status_priority,
        -total_elements,        # More diagram elements preferred
        validation["critical_errors"],
        validation["high_errors"],
        validation["total_errors"],
        -validation["passed_checks"],
    )


def _candidate_review_payload(candidate: CandidateState) -> dict:
    cls_count = len(candidate.class_diagram.get("classes", [])) if isinstance(candidate.class_diagram, dict) else 0
    seq_count = len(candidate.sequence_diagrams or []) if isinstance(candidate.sequence_diagrams, list) else 0
    er_count = len(candidate.er_diagram.get("entities", [])) if isinstance(candidate.er_diagram, dict) else 0
    return {
        "candidate_id": candidate.candidate_id,
        "provider": candidate.provider,
        "model": candidate.model,
        "status": candidate.status,
        "class_count": cls_count,
        "sequence_count": seq_count,
        "er_count": er_count,
        "class_diagram": candidate.class_diagram,
        "er_diagram": candidate.er_diagram,
        "sequence_diagrams": candidate.sequence_diagrams,
    }


def _validation_summary(candidate: CandidateState) -> dict:
    total_checks = 0
    passed_checks = 0
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for validation in [
        candidate.class_validation,
        candidate.er_validation,
        candidate.sequence_validation,
    ]:
        validation = validation or {}
        total_checks += int(validation.get("total_checks", 0) or 0)
        passed_checks += int(validation.get("passed_checks", 0) or 0)
        for error in validation.get("errors", []) or []:
            severity = str(error.get("severity", "")).lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        for warning in validation.get("warnings", []) or []:
            severity = str(warning.get("severity", "low")).lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

    total_errors = sum(severity_counts.values())
    return {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "critical_errors": severity_counts["critical"],
        "high_errors": severity_counts["high"],
        "medium_errors": severity_counts["medium"],
        "low_errors": severity_counts["low"],
        "total_errors": total_errors,
        "parse_error_count": len(candidate.parse_errors),
        "provider_error_count": len(candidate.provider_errors),
    }


def _repair_summary(candidate: CandidateState) -> dict:
    repair_metadata = candidate.repair_metadata or {}
    summary = {}
    for stage in ("class", "er", "sequence"):
        metadata = repair_metadata.get(stage, {}) or {}
        initial_validation = metadata.get("initial_validation") or {}
        final_validation = metadata.get("final_validation") or {}
        summary[stage] = {
            "initial_passed": initial_validation.get("passed"),
            "final_passed": final_validation.get("passed"),
            "initial_error_count": len(initial_validation.get("errors", []) or []),
            "final_error_count": len(final_validation.get("errors", []) or []),
            "repair_attempts": int(metadata.get("repair_attempts", 0) or 0),
            "repair_success": bool(metadata.get("repair_success", False)),
            "repair_error_count": len(metadata.get("repair_errors", []) or []),
        }
    return summary


def _parse_expert_result(
    parsed: dict,
    metrics: ExpertReviewMetrics,
) -> ExpertReviewResult:
    if not isinstance(parsed, dict):
        raise ValueError("Expert response was not a JSON object.")

    selected = parsed.get("selected_candidate_id")
    if selected is not None:
        selected = str(selected)

    confidence = parsed.get("confidence")
    if confidence is not None:
        confidence = float(confidence)

    reason = str(parsed.get("reason") or "").strip()
    return ExpertReviewResult(
        selected_candidate_id=selected,
        reason=reason,
        confidence=confidence,
        fallback_used=False,
        metrics=metrics,
    )


def _selection_validation_error(
    result: ExpertReviewResult,
    orchestration_result: OrchestrationResult,
) -> str:
    candidates = orchestration_result.candidates
    if result.selected_candidate_id is None:
        if any(candidate.status != "failed" for candidate in candidates.values()):
            return "Expert returned no candidate while usable candidates were available."
        return ""

    if result.selected_candidate_id not in candidates:
        return f"Expert selected unknown candidate '{result.selected_candidate_id}'."

    selected = candidates[result.selected_candidate_id]
    usable_exists = any(candidate.status != "failed" for candidate in candidates.values())
    if selected.status == "failed" and usable_exists:
        return f"Expert selected failed candidate '{result.selected_candidate_id}' while usable candidates existed."

    return ""


def _safe_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message[:300] if message else exc.__class__.__name__
