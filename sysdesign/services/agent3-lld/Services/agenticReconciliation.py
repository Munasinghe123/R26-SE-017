from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal

import config.config as app_config
from Services.expertRepair import ExpertRepairConfig, ExpertRepairResult, ExpertRepairService
from Services.validationService import ValidationService
from llm.factory import get_llm_provider
from llm.provider import LLMProvider
from utils.irMapper import convert_to_ir


MAX_AGENT_ITERATIONS = app_config.MAX_AGENT_ITERATIONS
AgentDecisionAction = Literal["PASS", "REPAIR", "SEMANTIC_GAP", "MAX_ITERATIONS_REACHED"]


@dataclass
class AgentDecision:
    action: AgentDecisionAction
    reason: str
    targets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "targets": list(self.targets),
        }


@dataclass
class AgenticReconciliationResult:
    final_ir: dict
    validation_report: dict
    iterations: int
    status: str
    stop_reason: str
    repair_metadata: dict = field(default_factory=dict)
    agent_trace: list[dict] = field(default_factory=list)
    unresolved_issues: list[dict] = field(default_factory=list)

    def metadata(self) -> dict:
        return {
            "status": self.status,
            "iterations": self.iterations,
            "max_iterations": MAX_AGENT_ITERATIONS,
            "stop_reason": self.stop_reason,
            "unresolved_issues": list(self.unresolved_issues),
        }


class AgenticReconciliationService:
    @staticmethod
    def get_expert_repair_config() -> ExpertRepairConfig:
        return ExpertRepairConfig(
            provider=app_config.EXPERT_REPAIR_PROVIDER,
            model=app_config.EXPERT_REPAIR_MODEL,
            temperature=app_config.EXPERT_REPAIR_TEMPERATURE,
            max_tokens=app_config.EXPERT_REPAIR_MAX_TOKENS,
        )

    @staticmethod
    def build_expert_repair_service(
        config: ExpertRepairConfig,
        provider: LLMProvider | None = None,
    ) -> ExpertRepairService:
        llm_provider = provider or get_llm_provider(config.provider)
        return ExpertRepairService(config=config, provider=llm_provider)

    @staticmethod
    def reconcile(
        *,
        selected_final_ir: dict,
        requirements: str,
        requirement_ids: list[str],
        initial_validation_result: dict | None = None,
        context: dict | None = None,
        repair_service: ExpertRepairService | None = None,
        repair_config: ExpertRepairConfig | None = None,
        provider: LLMProvider | None = None,
    ) -> AgenticReconciliationResult:
        current_ir = deepcopy(selected_final_ir)
        trace: list[dict] = []
        repair_metadata: dict = {
            "attempts": [],
            "max_iterations": MAX_AGENT_ITERATIONS,
        }
        latest_report: dict = {}
        validation_result = initial_validation_result
        service = repair_service

        for iteration in range(1, MAX_AGENT_ITERATIONS + 1):
            if validation_result is None:
                validation_result = ValidationService.validate(
                    convert_to_ir(current_ir),
                    requirement_ids=requirement_ids,
                )

            latest_report = dict(validation_result.get("report") or {})
            trace.append(_validator_trace(iteration, latest_report))

            if latest_report.get("passed"):
                return AgenticReconciliationResult(
                    final_ir=current_ir,
                    validation_report=latest_report,
                    iterations=iteration,
                    status="passed",
                    stop_reason="validation_passed",
                    repair_metadata=repair_metadata,
                    agent_trace=trace,
                    unresolved_issues=[],
                )

            decision = decide_reconciliation_action(
                latest_report,
                current_ir=current_ir,
                requirements=requirements,
                iteration=iteration,
            )
            trace.append({
                "iteration": iteration,
                "agent": "expert_decision",
                **decision.to_dict(),
            })

            if decision.action == "SEMANTIC_GAP":
                return AgenticReconciliationResult(
                    final_ir=current_ir,
                    validation_report=latest_report,
                    iterations=iteration,
                    status="semantic_gap",
                    stop_reason="semantic_gap",
                    repair_metadata=repair_metadata,
                    agent_trace=trace,
                    unresolved_issues=_collect_unresolved_issues(latest_report),
                )

            if decision.action != "REPAIR":
                return AgenticReconciliationResult(
                    final_ir=current_ir,
                    validation_report=latest_report,
                    iterations=iteration,
                    status="repair_not_possible",
                    stop_reason=decision.reason,
                    repair_metadata=repair_metadata,
                    agent_trace=trace,
                    unresolved_issues=_collect_unresolved_issues(latest_report),
                )

            if iteration >= MAX_AGENT_ITERATIONS:
                trace.append({
                    "iteration": iteration,
                    "agent": "expert_decision",
                    "action": "MAX_ITERATIONS_REACHED",
                    "reason": "Reached the final agentic reconciliation iteration limit.",
                })
                return AgenticReconciliationResult(
                    final_ir=current_ir,
                    validation_report=latest_report,
                    iterations=iteration,
                    status="max_iterations_reached",
                    stop_reason="max_iterations_reached",
                    repair_metadata=repair_metadata,
                    agent_trace=trace,
                    unresolved_issues=_collect_unresolved_issues(latest_report),
                )

            if service is None:
                config = repair_config or AgenticReconciliationService.get_expert_repair_config()
                service = AgenticReconciliationService.build_expert_repair_service(
                    config=config,
                    provider=provider,
                )

            repair_result = service.repair(
                final_ir=current_ir,
                validation_report=latest_report,
                requirements=requirements,
                requirement_ids=requirement_ids,
                repair_guidance=decision.to_dict(),
                context=context or {},
            )
            repair_attempt = _repair_attempt(iteration, repair_result)
            repair_metadata["attempts"].append(repair_attempt)
            trace.append({
                "iteration": iteration,
                "agent": "expert_repair",
                "status": "failed" if repair_result.error else "completed",
                "error": repair_result.error,
            })

            if repair_result.error or repair_result.final_ir is None:
                return AgenticReconciliationResult(
                    final_ir=current_ir,
                    validation_report=latest_report,
                    iterations=iteration,
                    status="repair_not_possible",
                    stop_reason="repair_failed",
                    repair_metadata=repair_metadata,
                    agent_trace=trace,
                    unresolved_issues=_collect_unresolved_issues(latest_report),
                )

            current_ir = deepcopy(repair_result.final_ir)
            validation_result = None

        return AgenticReconciliationResult(
            final_ir=current_ir,
            validation_report=latest_report,
            iterations=MAX_AGENT_ITERATIONS,
            status="max_iterations_reached",
            stop_reason="max_iterations_reached",
            repair_metadata=repair_metadata,
            agent_trace=trace,
            unresolved_issues=_collect_unresolved_issues(latest_report),
        )


def decide_reconciliation_action(
    validation_report: dict,
    *,
    current_ir: dict,
    requirements: str,
    iteration: int,
) -> AgentDecision:
    if validation_report.get("passed"):
        return AgentDecision("PASS", "Final validation passed.")

    issues = _collect_unresolved_issues(validation_report)
    if not issues:
        return AgentDecision("PASS", "No validation issues were reported.")

    semantic_gap = _semantic_gap_issue(issues, current_ir=current_ir, requirements=requirements)
    if semantic_gap:
        return AgentDecision(
            "SEMANTIC_GAP",
            semantic_gap.get("message", "Validation requires unsupported domain semantics."),
            targets=[semantic_gap.get("target", "")],
        )

    repairable = [issue for issue in issues if _is_repairable_issue(issue)]
    if repairable and len(repairable) == len(issues):
        return AgentDecision(
            "REPAIR",
            "All current validation issues are structural and have enough evidence for targeted repair.",
            targets=[issue.get("target", "") for issue in repairable if issue.get("target")],
        )

    if repairable:
        return AgentDecision(
            "REPAIR",
            "Repairable structural issues are present; unresolved non-structural issues will remain in final validation if not fixed.",
            targets=[issue.get("target", "") for issue in repairable if issue.get("target")],
        )

    return AgentDecision(
        "SEMANTIC_GAP",
        "No safe deterministic repair path exists for the reported issues.",
        targets=[issue.get("target", "") for issue in issues if issue.get("target")],
    )


def _validator_trace(iteration: int, validation_report: dict) -> dict:
    issues = _collect_unresolved_issues(validation_report)
    return {
        "iteration": iteration,
        "agent": "final_validator",
        "status": "passed" if validation_report.get("passed") else "failed",
        "issues": len(issues),
        "critical_errors": sum(1 for issue in issues if issue.get("severity") == "critical"),
        "high_errors": sum(1 for issue in issues if issue.get("severity") == "high"),
    }


def _repair_attempt(iteration: int, repair_result: ExpertRepairResult) -> dict:
    return {
        "iteration": iteration,
        "status": "failed" if repair_result.error else "completed",
        "error": repair_result.error,
        "metrics": repair_result.metrics,
    }


def _collect_unresolved_issues(validation_report: dict) -> list[dict]:
    issues: list[dict] = []
    for error in validation_report.get("errors", []) or []:
        if not isinstance(error, dict):
            continue
        issues.append({
            "source": "error",
            "rule_id": error.get("rule_id", ""),
            "severity": error.get("severity", ""),
            "message": error.get("message", ""),
            "target": error.get("path", error.get("rule_id", "")),
        })
    for flag in validation_report.get("overdesign_flags", []) or []:
        if not isinstance(flag, dict):
            continue
        issues.append({
            "source": "overdesign",
            "rule_id": "OVERDESIGN",
            "severity": "high",
            "message": flag.get("reason", ""),
            "target": f"{flag.get('element_type', '')}:{flag.get('element_name', '')}",
        })
    for violation in validation_report.get("naming_violations", []) or []:
        if not isinstance(violation, dict) or violation.get("auto_fixed"):
            continue
        issues.append({
            "source": "naming",
            "rule_id": "NAMING",
            "severity": "medium",
            "message": violation.get("location", ""),
            "target": violation.get("current_name", ""),
        })
    return issues


def _semantic_gap_issue(
    issues: list[dict],
    *,
    current_ir: dict,
    requirements: str,
) -> dict | None:
    requirements_text = requirements.lower()
    for issue in issues:
        text = f"{issue.get('message', '')} {issue.get('target', '')}".lower()
        if any(token in text for token in ["actor", "persistent", "domain entity"]):
            return issue
        if any(token in text for token in ["customer_id", "product_id", "cart_items", "cartitem", "cart item"]):
            return issue
        if "foreign key" in text and "no entity" in text:
            return issue
        if "no corresponding er entity" in text and not _concept_explicitly_supported(text, current_ir, requirements_text):
            return issue
        if issue.get("rule_id") == "OVERDESIGN" and "no requirement_ids" in text:
            return issue
    return None


def _concept_explicitly_supported(text: str, current_ir: dict, requirements_text: str) -> bool:
    concept_names = _canonical_names(current_ir)
    return any(name.lower() in text and name.lower() in requirements_text for name in concept_names)


def _canonical_names(current_ir: dict) -> set[str]:
    names: set[str] = set()
    for cls in (current_ir.get("class_diagram", {}) or {}).get("classes", []) or []:
        if isinstance(cls, dict) and cls.get("name"):
            names.add(str(cls["name"]))
    for entity in (current_ir.get("er_diagram", {}) or {}).get("entities", []) or []:
        if isinstance(entity, dict) and entity.get("name"):
            names.add(str(entity["name"]))
    for seq in current_ir.get("sequence_diagrams", []) or []:
        if isinstance(seq, dict):
            names.update(str(p) for p in seq.get("participants", []) or [] if str(p).strip())
    return names


def _is_repairable_issue(issue: dict) -> bool:
    rule_id = str(issue.get("rule_id", "")).upper()
    message = str(issue.get("message", "")).lower()
    if rule_id in {
        "CV-001",
        "CV-002",
        "CV-003",
        "CV-004",
        "CV-005",
        "CV-006",
        "CV-007",
        "CV-008",
        "NAMING",
        "VALIDATION-ERROR",
    }:
        return True
    return any(
        token in message
        for token in [
            "method",
            "participant",
            "primary key",
            "relationship endpoint",
            "canonical",
            "naming",
            "missing reference",
            "malformed",
        ]
    )
