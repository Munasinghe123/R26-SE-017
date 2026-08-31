from __future__ import annotations

import json
from dataclasses import dataclass, field

from graph.candidate_prompts import COMMON_UML_SKILL
from llm.provider import LLMProvider
from utils.jsonCleaner import clean_json_response


@dataclass
class ExpertRepairConfig:
    provider: str
    model: str
    temperature: float = 0
    max_tokens: int = 3500


@dataclass
class ExpertRepairResult:
    final_ir: dict | None
    response_content: str = ""
    error: dict | None = None
    metrics: dict = field(default_factory=dict)


class ExpertRepairService:
    def __init__(self, config: ExpertRepairConfig, provider: LLMProvider) -> None:
        self.config = config
        self.provider = provider

    def repair(
        self,
        *,
        final_ir: dict,
        validation_report: dict,
        requirements: str,
        requirement_ids: list[str],
        repair_guidance: dict | None = None,
        context: dict | None = None,
    ) -> ExpertRepairResult:
        try:
            response = self.provider.complete(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": EXPERT_REPAIR_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": build_expert_repair_prompt(
                            final_ir=final_ir,
                            validation_report=validation_report,
                            requirements=requirements,
                            requirement_ids=requirement_ids,
                            repair_guidance=repair_guidance or {},
                            context=context or {},
                        ),
                    },
                ],
            )
        except Exception as exc:
            return ExpertRepairResult(
                final_ir=None,
                error={
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
            return ExpertRepairResult(
                final_ir=None,
                response_content=response.content,
                error={
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
                metrics=metrics,
            )

        repaired_ir = _extract_final_ir(parsed)
        if repaired_ir is None:
            return ExpertRepairResult(
                final_ir=None,
                response_content=response.content,
                error={
                    "error_type": "InvalidRepairOutput",
                    "message": "Repair response missing a complete final UML IR.",
                },
                metrics=metrics,
            )

        return ExpertRepairResult(
            final_ir=repaired_ir,
            response_content=response.content,
            metrics=metrics,
        )

    async def arepair(
        self,
        *,
        final_ir: dict,
        validation_report: dict,
        requirements: str,
        requirement_ids: list[str],
        repair_guidance: dict | None = None,
        context: dict | None = None,
    ) -> ExpertRepairResult:
        try:
            response = await self.provider.acomplete(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": EXPERT_REPAIR_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": build_expert_repair_prompt(
                            final_ir=final_ir,
                            validation_report=validation_report,
                            requirements=requirements,
                            requirement_ids=requirement_ids,
                            repair_guidance=repair_guidance or {},
                            context=context or {},
                        ),
                    },
                ],
            )
        except Exception as exc:
            return ExpertRepairResult(
                final_ir=None,
                error={
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
            return ExpertRepairResult(
                final_ir=None,
                response_content=response.content,
                error={
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
                metrics=metrics,
            )

        repaired_ir = _extract_final_ir(parsed)
        if repaired_ir is None:
            return ExpertRepairResult(
                final_ir=None,
                response_content=response.content,
                error={
                    "error_type": "InvalidRepairOutput",
                    "message": "Repair response missing a complete final UML IR.",
                },
                metrics=metrics,
            )

        return ExpertRepairResult(
            final_ir=repaired_ir,
            response_content=response.content,
            metrics=metrics,
        )


EXPERT_REPAIR_SYSTEM_PROMPT = """
You repair a selected canonical UML JSON IR using deterministic validation
failures. Return only valid JSON. Do not invent unsupported requirements,
entities, relationships, identifiers, actors, methods, or business behavior.
""".strip()


def build_expert_repair_prompt(
    *,
    final_ir: dict,
    validation_report: dict,
    requirements: str,
    requirement_ids: list[str],
    repair_guidance: dict,
    context: dict,
) -> str:
    failures = _validation_failures(validation_report)
    return f"""
{COMMON_UML_SKILL.instructions}

ROLE

Repair the existing final UML IR with the smallest safe corrections.

SOURCE OF TRUTH

1. Original requirements
2. Requirement IDs
3. Current final IR
4. Deterministic validation failures
5. Explicit repair guidance supplied by the reconciliation controller

STRICT GUARDRAILS

- Do not regenerate the system from scratch.
- Preserve valid existing class, ER, and sequence content.
- Do not invent persistent entities from actors.
- Do not invent entities from *_id fields.
- Do not invent entities from nested API payload fields such as cart_items.
- Do not guess cardinality.
- Do not add relationships unless both endpoints and the relationship are supported by source inputs.
- Do not create Product, Customer, CartItem, User, or similar concepts unless explicitly supported as domain/persistent concepts.
- Fix only validation failures that can be resolved from existing supported structures.
- Return the complete corrected IR JSON only.
- No markdown, comments, or prose.

OUTPUT SCHEMA

{{
  "class_diagram": {{
    "classes": [
      {{
        "name": "string",
        "attributes": ["string"],
        "methods": ["string"],
        "requirement_ids": ["REQ-001"]
      }}
    ],
    "relationships": [
      {{
        "source": "string",
        "target": "string",
        "type": "association",
        "cardinality": "1..*"
      }}
    ]
  }},
  "er_diagram": {{
    "entities": [
      {{
        "name": "string",
        "attributes": ["string"],
        "primary_key": "string",
        "requirement_ids": ["REQ-001"]
      }}
    ],
    "relationships": [
      {{
        "name": "semantic relationship verb or verb phrase",
        "source": "string",
        "target": "string",
        "type": "one-to-one | one-to-many | many-to-one | many-to-many",
        "source_multiplicity": "1 | 0..1 | 0..* | 1..*",
        "target_multiplicity": "1 | 0..1 | 0..* | 1..*",
        "evidence": "string"
      }}
    ]
  }},
  "sequence_diagrams": [
    {{
      "name": "string",
      "description": "string",
      "requirement_ids": ["REQ-001"],
      "participants": ["string"],
      "participant_types": {{}},
      "logic_blocks": [],
      "messages": []
    }}
  ]
}}

INPUT

Requirements:
{requirements}

Requirement IDs:
{json.dumps(requirement_ids, ensure_ascii=True)}

Repair Guidance:
{json.dumps(repair_guidance, ensure_ascii=True)}

Context:
{json.dumps(context, ensure_ascii=True)}

Validation Failures:
{json.dumps(failures, ensure_ascii=True)}

Current Final IR:
{json.dumps(final_ir, ensure_ascii=True)}
""".strip()


def _validation_failures(validation_report: dict) -> dict:
    return {
        "passed": validation_report.get("passed"),
        "errors": validation_report.get("errors", []) or [],
        "overdesign_flags": validation_report.get("overdesign_flags", []) or [],
        "naming_violations": validation_report.get("naming_violations", []) or [],
    }


def _extract_final_ir(parsed) -> dict | None:
    if not isinstance(parsed, dict):
        return None
    if "final_ir" in parsed and isinstance(parsed["final_ir"], dict):
        parsed = parsed["final_ir"]
    required_keys = {"class_diagram", "er_diagram", "sequence_diagrams"}
    if required_keys.issubset(parsed.keys()):
        return parsed
    return None
