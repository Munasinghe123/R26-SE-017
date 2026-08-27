from __future__ import annotations

import config.config as app_config
from graph.candidate import CandidateConfig, CandidateState, run_candidate
from llm.factory import get_llm_provider
from llm.provider import LLMProvider


class CandidateService:
    """
    Internal orchestration entry point for running one dependency-aware
    candidate pipeline. This is intentionally not wired to public routes yet.
    """

    @staticmethod
    def get_candidate_1_config() -> CandidateConfig:
        return CandidateService._build_candidate_config(
            candidate_id="candidate_1",
            provider=app_config.CANDIDATE_1_PROVIDER,
            model=app_config.CANDIDATE_1_MODEL,
            temperature=app_config.CANDIDATE_1_TEMPERATURE,
            max_tokens=app_config.CANDIDATE_1_MAX_TOKENS,
        )

    @staticmethod
    def get_candidate_2_config() -> CandidateConfig:
        return CandidateService._build_candidate_config(
            candidate_id="candidate_2",
            provider=app_config.CANDIDATE_2_PROVIDER,
            model=app_config.CANDIDATE_2_MODEL,
            temperature=app_config.CANDIDATE_2_TEMPERATURE,
            max_tokens=app_config.CANDIDATE_2_MAX_TOKENS,
        )

    @staticmethod
    def get_candidate_3_config() -> CandidateConfig:
        return CandidateService._build_candidate_config(
            candidate_id="candidate_3",
            provider=app_config.CANDIDATE_3_PROVIDER,
            model=app_config.CANDIDATE_3_MODEL,
            temperature=app_config.CANDIDATE_3_TEMPERATURE,
            max_tokens=app_config.CANDIDATE_3_MAX_TOKENS,
        )

    @staticmethod
    def _build_candidate_config(
        candidate_id: str,
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> CandidateConfig:
        return CandidateConfig(
            candidate_id=candidate_id,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @staticmethod
    def run_candidate_internal(
        requirements: str,
        requirement_ids: list[str] | None = None,
        candidate_config: CandidateConfig | None = None,
        provider: LLMProvider | None = None,
    ) -> CandidateState:
        config = candidate_config or CandidateService.get_candidate_1_config()
        llm_provider = provider or get_llm_provider(config.provider)
        return run_candidate(
            config=config,
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            provider=llm_provider,
        )
