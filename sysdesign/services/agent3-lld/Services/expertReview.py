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


def _build_candidate_summary_for_reviewer(c: CandidateState, requirements: str) -> dict:
    val = _validation_summary(c)
    classes = (c.class_diagram.get("classes", []) if isinstance(c.class_diagram, dict) else []) or []
    er_entities = (c.er_diagram.get("entities", []) if isinstance(c.er_diagram, dict) else []) or []
    sequences = (c.sequence_diagrams if isinstance(c.sequence_diagrams, list) else []) or []

    class_names = [cls.get("name") for cls in classes if isinstance(cls, dict) and cls.get("name")]
    er_names = [ent.get("name") for ent in er_entities if isinstance(ent, dict) and ent.get("name")]
    matching_names = list(set(class_names).intersection(set(er_names)))
    missing_in_er = list(set(class_names) - set(er_names))

    # Inspect class methods
    classes_with_methods = [
        cls.get("name") for cls in classes
        if isinstance(cls, dict) and (cls.get("methods", []) or [])
    ]
    is_methodless = len(class_names) > 0 and len(classes_with_methods) == 0

    # Inspect sequence interaction use cases & architectural participants
    arch_keywords = ("controller", "service", "repository", "frontend", "ui")
    speculative_arch_used = set()
    use_cases = []
    for seq in sequences:
        if not isinstance(seq, dict):
            continue
        participants = [str(p) for p in seq.get("participants", []) if str(p)]
        for p in participants:
            p_lower = p.lower()
            if any(p_lower == kw or p_lower.endswith(kw) for kw in arch_keywords) and p not in class_names:
                speculative_arch_used.add(p)
        item_count = len(seq.get("items", seq.get("messages", [])) or [])
        use_cases.append({
            "name": seq.get("name", "Unnamed Sequence"),
            "participants": participants,
            "interaction_count": item_count,
        })

    is_failed_hld = "provisional" in requirements.lower() or "failed" in requirements.lower()
    hld_grounding = "Provisional / Ungrounded (HLD failed/unavailable)" if is_failed_hld else "Grounded"

    return {
        "candidate_id": c.candidate_id,
        "model": c.model,
        "status": c.status,
        "stage_validation_status": {
            "class": "passed" if (c.class_validation or {}).get("passed") else "failed",
            "er": "passed" if (c.er_validation or {}).get("passed") else "failed",
            "sequence": "passed" if (c.sequence_validation or {}).get("passed") else "failed",
        },
        "error_counts": {
            "critical": val["critical_errors"],
            "high": val["high_errors"],
            "medium": val["medium_errors"],
            "total": val["total_errors"],
        },
        "cross_diagram_consistency": {
            "passed": val["consistency_passed"],
            "score": f"{val['consistency_score']}%",
            "critical_violations": val["violations"][:5],
        },
        "class_sequence_method_consistency": {
            "all_called_methods_defined": len(val["missing_methods_called"]) == 0,
            "missing_methods_called": val["missing_methods_called"][:4],
            "methodless_classes_with_sequence_calls": bool(is_methodless and sequences),
        },
        "class_er_correspondence": {
            "class_count": len(class_names),
            "er_entity_count": len(er_names),
            "matching_entities": matching_names,
            "unmatched_classes": missing_in_er,
        },
        "sequence_use_case_coverage": {
            "sequence_count": len(sequences),
            "use_cases": use_cases[:4],
        },
        "architectural_grounding": {
            "hld_status": hld_grounding,
            "speculative_architectural_participants": sorted(list(speculative_arch_used)),
        },
        "eligibility": "ELIGIBLE" if val["critical_errors"] == 0 else f"INELIGIBLE ({val['critical_errors']} critical errors)",
    }


def build_expert_review_prompt(
    requirements: str,
    orchestration_result: OrchestrationResult,
) -> str:
    candidate_summaries = [
        _build_candidate_summary_for_reviewer(c, requirements)
        for c in orchestration_result.candidates.values()
    ]

    payload = {
        "requirements": requirements,
        "allowed_candidate_ids": list(orchestration_result.candidates.keys()),
        "candidates": candidate_summaries,
        "selection_rules": [
            "1. Candidates marked 'ELIGIBLE' with 0 critical errors MUST be chosen over candidates marked 'INELIGIBLE'.",
            "2. Behavioral-structural consistency is mandatory: Sequence Diagrams calling undeclared methods on classes is a CRITICAL violation (CV-001).",
            "3. Diagram counts (having more Sequence Diagrams or Classes) must NEVER justify selecting a candidate with critical validation errors over a cleaner candidate.",
            "4. If all candidates have validation issues, select the candidate with the fewest critical and high-severity errors that is most structurally sound and repairable.",
        ],
        "output_format": {
            "selected_candidate_id": "candidate_1 | candidate_2 | candidate_3",
            "reason": "Detailed technical rationale explaining why the chosen candidate has the fewest critical errors and best structural/behavioral consistency",
            "confidence": 0.95
        }
    }
    return (
        "Review the candidate design outputs and select the strongest structurally and behaviorally correct candidate.\n"
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
    selected_val = _validation_summary(selected)
    crit_count = selected_val["critical_errors"]
    if crit_count == 0:
        desc = f"Selected {selected.candidate_id} ({selected.model}) based on verified zero critical errors and superior structural/behavioral consistency."
    else:
        desc = f"Selected {selected.candidate_id} ({selected.model}) as the most repairable candidate ({crit_count} critical error(s)); all candidates have validation issues."

    return ExpertReviewResult(
        selected_candidate_id=selected.candidate_id,
        reason=f"{desc} (Fallback reason: {fallback_reason})",
        confidence=0.90 if crit_count == 0 else 0.60,
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
    if candidate.status == "failed" or total_elements == 0:
        status_priority = 3
    elif candidate.status == "valid" and validation["critical_errors"] == 0:
        status_priority = 0
    elif validation["critical_errors"] == 0:
        status_priority = 1
    else:
        status_priority = 2

    return (
        empty_penalty,
        status_priority,
        validation["critical_errors"],      # Fewer critical errors (ascending)
        validation["high_errors"],          # Fewer high errors (ascending)
        validation["total_errors"],         # Fewer total errors (ascending)
        -validation["passed_checks"],       # More passed checks (descending)
        -total_elements,                    # Secondary tie-breaker only!
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
    if candidate.consistency_validation is None and candidate.final_ir:
        try:
            from Services.validationService import ValidationService
            from utils.irMapper import convert_to_ir
            candidate.consistency_validation = ValidationService.validate(
                convert_to_ir(candidate.final_ir)
            )
        except Exception:
            pass

    total_checks = 0
    passed_checks = 0
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    seen_issue_signatures = set()
    violations = []
    missing_methods_called = []

    # 1. Process consistency validation (canonical cross-diagram checks: CV-001..CV-012, naming, overdesign)
    consistency_val = candidate.consistency_validation or {}
    c_report = consistency_val.get("report") or {}
    total_checks += int(c_report.get("total_checks", 0) or 0)
    passed_checks += int(c_report.get("passed_checks", 0) or 0)

    for error in c_report.get("errors", []) or []:
        rule_id = str(error.get("rule_id", "")).upper()
        msg = str(error.get("message", "")).strip()
        sev = str(error.get("severity", "")).lower()
        if sev not in severity_counts:
            sev = "high"
        sig = (rule_id, msg.lower())
        if sig not in seen_issue_signatures:
            seen_issue_signatures.add(sig)
            severity_counts[sev] += 1
            violations.append(f"{rule_id}: {msg}")
            if rule_id == "CV-001":
                missing_methods_called.append(msg)

    # 2. Process stage validations (AST & schema checks: class, er, sequence)
    for stage_name, validation in [
        ("class", candidate.class_validation),
        ("er", candidate.er_validation),
        ("sequence", candidate.sequence_validation),
    ]:
        validation = validation or {}
        total_checks += int(validation.get("total_checks", 0) or 0)
        passed_checks += int(validation.get("passed_checks", 0) or 0)
        for error in validation.get("errors", []) or []:
            code = str(error.get("code", error.get("rule_id", ""))).upper()
            msg = str(error.get("message", "")).strip()
            sev = str(error.get("severity", "")).lower()
            if sev not in severity_counts:
                sev = "high"
            if code == "UNKNOWN_RECEIVER_METHOD" or "not defined on receiving class" in msg.lower():
                missing_methods_called.append(msg)
                sev = "critical"
                sig = ("CV-001_EQUIV", msg.lower())
            else:
                sig = (code, msg.lower())

            if sig not in seen_issue_signatures:
                seen_issue_signatures.add(sig)
                severity_counts[sev] += 1
                violations.append(f"{code}: {msg}")

        for warning in validation.get("warnings", []) or []:
            code = str(warning.get("code", warning.get("rule_id", ""))).upper()
            msg = str(warning.get("message", "")).strip()
            sig = (code, msg.lower())
            if sig not in seen_issue_signatures:
                seen_issue_signatures.add(sig)
                severity_counts["low"] += 1

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
        "violations": violations,
        "missing_methods_called": list(set(missing_methods_called)),
        "consistency_passed": bool(c_report.get("passed", False) if c_report else (severity_counts["critical"] == 0 and severity_counts["high"] == 0)),
        "consistency_score": float(c_report.get("consistency_score", 0.0) if c_report else (round(passed_checks / total_checks * 100, 2) if total_checks else 0.0)),
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
    usable = [c for c in candidates.values() if c.status != "failed"]
    if selected.status == "failed" and usable:
        return f"Expert selected failed candidate '{result.selected_candidate_id}' while usable candidates existed."

    # Enforce deterministic eligibility rules
    if usable:
        best_candidate = min(usable, key=_fallback_sort_key)
        selected_val = _validation_summary(selected)
        best_val = _validation_summary(best_candidate)

        # Rule 1: Cannot select candidate with critical errors if another usable candidate has 0 critical errors
        if selected_val["critical_errors"] > 0 and best_val["critical_errors"] == 0:
            return (
                f"Expert selected candidate '{result.selected_candidate_id}' with "
                f"{selected_val['critical_errors']} critical error(s) ({selected_val['missing_methods_called']}), "
                f"while '{best_candidate.candidate_id}' has 0 critical errors. Deterministic eligibility rule overrides selection."
            )

        # Rule 2: Cannot select candidate with more critical errors than best available
        if selected_val["critical_errors"] > best_val["critical_errors"]:
            return (
                f"Expert selected candidate '{result.selected_candidate_id}' with "
                f"{selected_val['critical_errors']} critical error(s), but '{best_candidate.candidate_id}' "
                f"has only {best_val['critical_errors']} critical error(s). Deterministic eligibility rule overrides selection."
            )

        # Rule 3: If tied on critical errors, cannot select candidate with significantly worse high errors
        if selected_val["critical_errors"] == best_val["critical_errors"] and selected_val["high_errors"] > best_val["high_errors"] + 2:
            return (
                f"Expert selected candidate '{result.selected_candidate_id}' with "
                f"{selected_val['high_errors']} high error(s), but '{best_candidate.candidate_id}' "
                f"has only {best_val['high_errors']} high error(s). Deterministic eligibility rule overrides selection."
            )

    return ""


def _safe_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message[:300] if message else exc.__class__.__name__
