from __future__ import annotations

import logging
from groq import Groq
from config.config import GROQ_API_KEY, EXPERT_MODEL
from schemas.ir_schema import IntermediateRepresentation
from schemas.api_models import (
    ValidationError,
    ValidationReport,
    Severity,
    NamingViolation,
    OverDesignFlag,
)
from validators.consistency_engine import ConsistencyEngine
from validators.overdesign_detector import OverDesignDetector
from validators.naming_enforcer import NamingEnforcer

logger = logging.getLogger(__name__)


EXPERT_SYSTEM_PROMPT = """
You are a Principal Software Architect and UML Validation Expert.

Analyze UML validation problems and provide concise,
technical correction guidance.

Focus on:

* missing methods
* undefined participants
* invalid relationships
* naming violations
* missing entities
* requirement traceability
* consistency fixes

Return only actionable correction instructions.
"""


def _overdesign_to_errors(flags: list[OverDesignFlag]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for flag in flags:
        errors.append(ValidationError(
            rule_id="OVERDESIGN",
            severity=Severity.HIGH,
            message=f"{flag.element_type} '{flag.element_name}': {flag.reason}",
            suggestion="Remove the element or map it to a requirement.",
            educational_feedback=flag.educational_feedback,
        ))
    return errors


def _naming_to_errors(violations: list[NamingViolation]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for violation in violations:
        if violation.auto_fixed:
            continue
        errors.append(ValidationError(
            rule_id="NAMING",
            severity=Severity.MEDIUM,
            message=f"{violation.location}: '{violation.current_name}'",
            suggestion=f"Use '{violation.expected_name}' ({violation.convention}).",
        ))
    return errors


class ExpertAgent:
    """
    Runs deterministic validation modules and generates concise guidance
    for fixing issues on the next IR regeneration.
    """

    def __init__(
        self,
        consistency_engine: ConsistencyEngine,
        overdesign_detector: OverDesignDetector,
        naming_enforcer: NamingEnforcer,
    ) -> None:
        self.client = Groq(api_key=GROQ_API_KEY)
        self.consistency_engine = consistency_engine
        self.overdesign_detector = overdesign_detector
        self.naming_enforcer = naming_enforcer

    def validate(
        self,
        ir: IntermediateRepresentation,
        requirement_ids: list[str],
        include_guidance: bool = True,
    ) -> tuple[ValidationReport, list[ValidationError], str]:
        """
        Validate IR and return the report, retry errors, and expert guidance.
        """
        consistency_report = self.consistency_engine.validate(ir)
        traceability_matrix, overdesign_flags = self.overdesign_detector.detect(
            ir, requirement_ids
        )
        ir, naming_violations = self.naming_enforcer.enforce(ir)

        overdesign_errors = _overdesign_to_errors(overdesign_flags)
        naming_errors = _naming_to_errors(naming_violations)
        combined_errors = (
            list(consistency_report.errors)
            + overdesign_errors
            + naming_errors
        )

        critical_errors = [
            e for e in consistency_report.errors if e.severity == Severity.CRITICAL
        ]
        overdesign_blockers = [
            f for f in overdesign_flags
            if f.element_type in ("class", "entity", "sequence")
        ]
        naming_blockers = [v for v in naming_violations if not v.auto_fixed]
        should_retry = bool(critical_errors or overdesign_blockers or naming_blockers)

        report = ValidationReport(
            passed=consistency_report.passed and not overdesign_blockers and not naming_blockers,
            consistency_score=consistency_report.consistency_score,
            total_checks=consistency_report.total_checks,
            passed_checks=consistency_report.passed_checks,
            errors=combined_errors,
            traceability_matrix=traceability_matrix,
            overdesign_flags=overdesign_flags,
            naming_violations=naming_violations,
            naming_violations_fixed=sum(1 for v in naming_violations if v.auto_fixed),
        )

        guidance = ""
        if should_retry and include_guidance:
            guidance = self.generate_guidance(combined_errors)

        return report, combined_errors, guidance

    def generate_guidance(self, errors: list[ValidationError]) -> str:
        if not errors:
            return ""

        error_text = "\n".join([
            f"- {e.rule_id}: {e.message}"
            for e in errors
        ])

        prompt = f"""
```

Analyze these UML validation errors
and provide concise correction guidance.

Validation Errors:
{error_text}
"""

        response = self.client.chat.completions.create(
            model=EXPERT_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": EXPERT_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        guidance = response.choices[0].message.content

        # limit guidance size
        return guidance[:800]