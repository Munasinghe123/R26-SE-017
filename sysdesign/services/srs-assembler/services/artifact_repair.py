from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal, Any

from llm.provider import LLMProvider
from utils.json_cleaner import clean_json_response

SRSStage = Literal["overview", "functional", "non_functional", "traceability"]


@dataclass
class ArtifactRepairConfig:
    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 4000
    max_attempts: int = 2


@dataclass
class ArtifactRepairResult:
    artifact: dict | list | None
    response_content: str = ""
    error: dict | None = None
    metrics: dict = field(default_factory=dict)


class ArtifactRepairService:
    def __init__(
        self,
        config: ArtifactRepairConfig,
        provider: LLMProvider,
    ) -> None:
        self.config = config
        self.provider = provider

    def repair(
        self,
        *,
        stage: SRSStage,
        artifact: dict | list,
        validation_result: dict,
        requirements: dict,
        dependencies: dict | None = None,
    ) -> ArtifactRepairResult:
        try:
            response = self.provider.complete(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": _system_prompt(stage),
                    },
                    {
                        "role": "user",
                        "content": _repair_prompt(
                            stage=stage,
                            artifact=artifact,
                            validation_result=validation_result,
                            requirements=requirements,
                            dependencies=dependencies or {},
                        ),
                    },
                ],
            )
        except Exception as exc:
            return ArtifactRepairResult(
                artifact=None,
                error={
                    "stage": stage,
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
            )

        metrics = {
            "provider": response.provider,
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
            "latency_ms": response.latency_ms,
        }

        try:
            parsed = clean_json_response(response.content)
        except Exception as exc:
            return ArtifactRepairResult(
                artifact=None,
                response_content=response.content,
                error={
                    "stage": stage,
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
                metrics=metrics,
            )

        artifact_value = _extract_stage_artifact(stage, parsed)
        if artifact_value is None:
            return ArtifactRepairResult(
                artifact=None,
                response_content=response.content,
                error={
                    "stage": stage,
                    "error_type": "InvalidRepairOutput",
                    "message": f"Repair response missing expected key '{_stage_key(stage)}'.",
                },
                metrics=metrics,
            )

        return ArtifactRepairResult(
            artifact=artifact_value,
            response_content=response.content,
            metrics=metrics,
        )

    async def arepair(
        self,
        *,
        stage: SRSStage,
        artifact: dict | list,
        validation_result: dict,
        requirements: dict,
        dependencies: dict | None = None,
    ) -> ArtifactRepairResult:
        try:
            response = await self.provider.acomplete(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": _system_prompt(stage),
                    },
                    {
                        "role": "user",
                        "content": _repair_prompt(
                            stage=stage,
                            artifact=artifact,
                            validation_result=validation_result,
                            requirements=requirements,
                            dependencies=dependencies or {},
                        ),
                    },
                ],
            )
        except Exception as exc:
            return ArtifactRepairResult(
                artifact=None,
                error={
                    "stage": stage,
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
            )

        metrics = {
            "provider": response.provider,
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
            "latency_ms": response.latency_ms,
        }

        try:
            parsed = clean_json_response(response.content)
        except Exception as exc:
            return ArtifactRepairResult(
                artifact=None,
                response_content=response.content,
                error={
                    "stage": stage,
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
                metrics=metrics,
            )

        artifact_value = _extract_stage_artifact(stage, parsed)
        if artifact_value is None:
            return ArtifactRepairResult(
                artifact=None,
                response_content=response.content,
                error={
                    "stage": stage,
                    "error_type": "InvalidRepairOutput",
                    "message": f"Repair response missing expected key '{_stage_key(stage)}'.",
                },
                metrics=metrics,
            )

        return ArtifactRepairResult(
            artifact=artifact_value,
            response_content=response.content,
            metrics=metrics,
        )


def _system_prompt(stage: SRSStage) -> str:
    return (
        f"You are an IEEE 29148 / ISO 25010 Requirements Engineering Repair Specialist. "
        f"You repair one existing SRS artifact ('{stage}') by resolving deterministic validation errors. "
        f"Return ONLY valid JSON with no markdown wrapping or conversational text."
    )


def _repair_prompt(
    *,
    stage: SRSStage,
    artifact: dict | list,
    validation_result: dict,
    requirements: dict,
    dependencies: dict,
) -> str:
    return f"""
ROLE:
Repair an existing IEEE 29148 SRS specification artifact.

GOAL:
Resolve all deterministic validation errors using the smallest justified modifications.

RULES:
- Do NOT rewrite valid sections or change requirement IDs.
- Preserve all existing requirement IDs.
- For functional requirements: ensure normative phrasing ("The system shall...") and add concrete acceptance criteria.
- For non-functional requirements: ensure valid ISO/IEC 25010 characteristic and quantitative target metrics.
- Return ONLY valid JSON matching the expected output schema.
- No markdown, no explanations, no chat text.

STAGE: {stage}

REQUIREMENTS:
{json.dumps(requirements, ensure_ascii=True)}

UPSTREAM DEPENDENCIES:
{json.dumps(dependencies, ensure_ascii=True)}

EXISTING ARTIFACT BEING REPAIRED:
{json.dumps({_stage_key(stage): artifact}, ensure_ascii=True)}

VALIDATION ERRORS:
{json.dumps(validation_result.get("errors", []), ensure_ascii=True)}

OUTPUT SCHEMA:
{_output_schema(stage)}
""".strip()


def _stage_key(stage: SRSStage) -> str:
    return {
        "overview": "overview_section",
        "functional": "functional_requirements",
        "non_functional": "non_functional_requirements",
        "traceability": "traceability_matrix",
    }[stage]


def _extract_stage_artifact(stage: SRSStage, parsed: Any):
    if not isinstance(parsed, dict):
        return None
    key = _stage_key(stage)
    if key in parsed:
        return parsed[key]
    # Fallback keys
    fallbacks = {
        "overview": ["overview", "section_overview"],
        "functional": ["functional", "requirements"],
        "non_functional": ["non_functional", "nfrs"],
        "traceability": ["traceability", "rtm"],
    }
    for alt in fallbacks.get(stage, []):
        if alt in parsed:
            return parsed[alt]
    return None


def _output_schema(stage: SRSStage) -> str:
    if stage == "overview":
        return """
{
  "overview_section": {
    "purpose": "A clear, descriptive statement (>20 chars) of the software purpose",
    "scope": "System boundary, objectives, and benefits",
    "product_perspective": "Context within larger system or standalone architecture",
    "acronyms_and_glossary": [
      {
        "term": "e.g. RBAC",
        "definition": "Role-Based Access Control - Authorization model based on user roles"
      }
    ],
    "standards_compliance": [
      {
        "standard": "e.g. ISO/IEC/IEEE 29148:2018",
        "category": "Software Engineering Standard | Regulatory Privacy | Accessibility",
        "scope_and_applicability": "Governs requirements specification and verification"
      }
    ],
    "user_characteristics": [
      {
        "role": "e.g. System Administrator",
        "description": "Responsibilities and skill level"
      }
    ],
    "external_interfaces": [
      {
        "name": "e.g. Payment Gateway API",
        "category": "Third-Party SaaS API | Software Interface | Communication Protocol",
        "purpose": "Why this external interface is required",
        "protocol": "e.g. HTTPS / REST JSON"
      }
    ],
    "assumptions_and_dependencies": ["Assumptions or environmental dependencies"],
    "design_constraints": ["Constraints or regulatory requirements"]
  }
}
""".strip()
    if stage == "functional":
        return """
{
  "functional_requirements": [
    {
      "id": "FR-1",
      "title": "Requirement title",
      "statement": "The system shall authenticate users with multi-factor tokens.",
      "priority": "High | Medium | Low",
      "acceptance_criteria": [
        "Given valid credentials, When user submits token, Then access is granted"
      ]
    }
  ]
}
""".strip()
    if stage == "non_functional":
        return """
{
  "non_functional_requirements": [
    {
      "id": "NFR-1",
      "iso_characteristic": "performance_efficiency | security | usability | reliability | maintainability | portability",
      "description": "Full description of quality attribute",
      "target_metric": "< 300ms p95 latency under standard load"
    }
  ]
}
""".strip()
    return """
{
  "traceability_matrix": [
    {
      "requirement_id": "FR-1",
      "allocated_component": "AuthService / API Gateway",
      "verification_method": "Test | Inspection | Demonstration | Analysis"
    }
  ]
}
""".strip()
