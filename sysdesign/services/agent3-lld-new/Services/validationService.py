import logging
from validators.consistency_engine import ConsistencyEngine
from validators.naming_enforcer import NamingEnforcer
from validators.overdesign_detector import OverDesignDetector
from validators.expert_agent import ExpertAgent
from schemas.api_models import ValidationError, Severity, ValidationReport

logger = logging.getLogger(__name__)


class ValidationService:

    @staticmethod
    def validate(ir, requirement_ids=None):
        requirement_ids = requirement_ids or []

        consistency = ConsistencyEngine()
        naming = NamingEnforcer()
        overdesign = OverDesignDetector()
        
        expert_agent = ExpertAgent(
            consistency_engine=consistency,
            overdesign_detector=overdesign,
            naming_enforcer=naming,
        )

        try:
            report, errors, expert_guidance = expert_agent.validate(
                ir,
                requirement_ids=requirement_ids,
                include_guidance=False, 
            )

            return {
                "report": report.to_dict(),
                "errors": [err.to_dict() for err in errors],
                "expert_guidance": expert_guidance,
            }
        except Exception as exc:
            logger.exception("Validation failed: %s", exc)

            fallback_error = ValidationError(
                rule_id="VALIDATION-ERROR",
                severity=Severity.HIGH,
                message=str(exc),
                suggestion="Review the IR mapping and validation inputs.",
            )
            fallback_report = ValidationReport(
                passed=False,
                consistency_score=0.0,
                total_checks=0,
                passed_checks=0,
                errors=[fallback_error],
            )

            return {
                "report": fallback_report.to_dict(),
                "errors": [],
                "expert_guidance": "",
            }