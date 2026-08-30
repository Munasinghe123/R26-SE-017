from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from graph.candidate_prompts import COMMON_UML_SKILL
from llm.provider import LLMProvider
from utils.jsonCleaner import clean_json_response


RepairStage = Literal["class", "er", "sequence"]


@dataclass
class ArtifactRepairConfig:
    provider: str
    model: str
    temperature: float = 0
    max_tokens: int = 3500
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
        stage: RepairStage,
        artifact: dict | list,
        validation_result: dict,
        requirements: str,
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
        stage: RepairStage,
        artifact: dict | list,
        validation_result: dict,
        requirements: str,
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


def _system_prompt(stage: RepairStage) -> str:
    return (
        "You repair one existing UML IR artifact using deterministic validation "
        f"errors. Repair only the {stage} artifact. Return only valid JSON."
    )


def _repair_prompt(
    *,
    stage: RepairStage,
    artifact: dict | list,
    validation_result: dict,
    requirements: str,
    dependencies: dict,
) -> str:
    return f"""
{COMMON_UML_SKILL.instructions}

ROLE

Repair an existing UML IR artifact.

SOURCE OF TRUTH

1. Requirements
2. Validated upstream artifacts supplied in dependencies
3. Existing artifact being repaired
4. Deterministic validation errors

GOAL

Resolve the supplied validation errors using the smallest justified local changes.

RULES

- Do not regenerate the artifact from scratch.
- Preserve valid existing content.
- Do not invent unsupported functionality.
- Preserve canonical class, entity, and method names unless correcting a specifically identified error.
- Do not modify unrelated elements.
- Do not contradict validated upstream artifacts.
- Resolve every validation error that can safely be resolved locally.
- If no safe local repair exists, preserve the artifact rather than inventing upstream changes.
- Return only valid JSON matching the expected artifact schema.
- No markdown.
- No comments.
- No explanatory prose.

DEPENDENCY RULES

- Class repair is grounded only in Requirements.
- ER repair is grounded in Requirements plus the validated Class Diagram.
- Sequence repair is grounded in Requirements plus the validated Class Diagram and validated ER Diagram.
- Downstream repair must not modify or contradict upstream artifacts.
- Sequence repair must reuse exact Class names and exact receiver method names from the Class Diagram.

OUTPUT SCHEMA

{_output_schema(stage)}

INPUT

Stage:
{stage}

Requirements:
{requirements}

Dependencies:
{json.dumps(dependencies, ensure_ascii=True)}

Existing Artifact:
{json.dumps({_stage_key(stage): artifact}, ensure_ascii=True)}

Validation Result:
{json.dumps(validation_result, ensure_ascii=True)}
""".strip()


def _output_schema(stage: RepairStage) -> str:
    if stage == "class":
        return """
{
  "class_diagram": {
    "classes": [
      {
        "name": "string",
        "attributes": ["string"],
        "methods": ["string"]
      }
    ],
    "relationships": [
      {
        "source": "string",
        "target": "string",
        "type": "association",
        "cardinality": "string"
      }
    ]
  }
}
""".strip()
    if stage == "er":
        return """
{
  "er_diagram": {
    "entities": [
      {
        "name": "string",
        "attributes": ["string"],
        "primary_key": "string"
      }
    ],
    "relationships": [
      {
        "name": "semantic relationship verb or verb phrase",
        "source": "string",
        "target": "string",
        "type": "one-to-one | one-to-many | many-to-one | many-to-many",
        "source_multiplicity": "1 | 0..1 | 0..* | 1..*",
        "target_multiplicity": "1 | 0..1 | 0..* | 1..*",
        "evidence": "string"
      }
    ]
  }
}
""".strip()
    return """
{
  "sequence_diagrams": [
    {
      "name": "string",
      "description": "string",
      "participants": ["string"],
      "participant_types": {
        "<participant_name>": "<participant_type>"
      },
      "logic_blocks": [],
      "messages": [
        {
          "from": "string",
          "to": "string",
          "message": "string",
          "activate": false,
          "deactivate": false
        }
      ]
    }
  ]
}
""".strip()


def _stage_key(stage: RepairStage) -> str:
    return {
        "class": "class_diagram",
        "er": "er_diagram",
        "sequence": "sequence_diagrams",
    }[stage]


def _extract_stage_artifact(stage: RepairStage, parsed):
    if not isinstance(parsed, dict):
        return None
    return parsed.get(_stage_key(stage))
