from __future__ import annotations

import config.config as app_config
from Services.diagramOrchestrator import OrchestrationResult
from Services.expertReview import (
    ExpertReviewAgent,
    ExpertReviewConfig,
    ExpertReviewResult,
    LLMExpertReviewAgent,
)
from llm.factory import get_llm_provider
from llm.provider import LLMProvider


class ExpertReviewService:
    @staticmethod
    def get_expert_review_config() -> ExpertReviewConfig:
        return ExpertReviewConfig(
            provider=app_config.EXPERT_REVIEW_PROVIDER,
            model=app_config.EXPERT_REVIEW_MODEL,
            temperature=app_config.EXPERT_REVIEW_TEMPERATURE,
            max_tokens=app_config.EXPERT_REVIEW_MAX_TOKENS,
        )

    @staticmethod
    def build_expert_review_agent(
        config: ExpertReviewConfig,
        provider: LLMProvider | None = None,
    ) -> ExpertReviewAgent:
        llm_provider = provider or get_llm_provider(config.provider)
        return LLMExpertReviewAgent(
            config=config,
            provider=llm_provider,
        )

    @staticmethod
    def review_candidates_internal(
        requirements: str,
        orchestration_result: OrchestrationResult,
        config: ExpertReviewConfig | None = None,
        provider: LLMProvider | None = None,
    ) -> ExpertReviewResult:
        expert_config = config or ExpertReviewService.get_expert_review_config()
        agent = ExpertReviewService.build_expert_review_agent(
            config=expert_config,
            provider=provider,
        )
        return agent.review(
            requirements=requirements,
            orchestration_result=orchestration_result,
        )

    @staticmethod
    async def areview_candidates_internal(
        requirements: str,
        orchestration_result: OrchestrationResult,
        config: ExpertReviewConfig | None = None,
        provider: LLMProvider | None = None,
    ) -> ExpertReviewResult:
        expert_config = config or ExpertReviewService.get_expert_review_config()
        agent = ExpertReviewService.build_expert_review_agent(
            config=expert_config,
            provider=provider,
        )
        return await agent.areview(
            requirements=requirements,
            orchestration_result=orchestration_result,
        )
