from __future__ import annotations

from collections.abc import Mapping, Sequence

import config.config as app_config
from Services.diagramOrchestrator import OrchestrationResult
from graph.candidate import CandidateConfig, CandidateState
from graph.ensemble_graph import arun_ensemble_graph, run_ensemble_graph
from graph.diagram_agent import CandidateDiagramAgent, DiagramGenerationAgent
from llm.factory import get_llm_provider
from llm.provider import LLMProvider


class CandidateService:
    """
    Internal orchestration entry point for running one dependency-aware
    candidate pipeline. This is intentionally not wired to public routes yet.
    """

    @staticmethod
    def get_candidate_config(candidate_number: int) -> CandidateConfig:
        if candidate_number not in (1, 2, 3):
            raise ValueError(f"Unsupported candidate number: {candidate_number}")

        return CandidateService._build_candidate_config(
            candidate_id=f"candidate_{candidate_number}",
            provider=getattr(app_config, f"CANDIDATE_{candidate_number}_PROVIDER"),
            model=getattr(app_config, f"CANDIDATE_{candidate_number}_MODEL"),
            temperature=getattr(app_config, f"CANDIDATE_{candidate_number}_TEMPERATURE"),
            max_tokens=getattr(app_config, f"CANDIDATE_{candidate_number}_MAX_TOKENS"),
        )

    @staticmethod
    def get_candidate_configs() -> list[CandidateConfig]:
        return [
            CandidateService.get_candidate_config(candidate_number)
            for candidate_number in (1, 2, 3)
        ]

    @staticmethod
    def get_candidate_1_config() -> CandidateConfig:
        return CandidateService.get_candidate_config(1)

    @staticmethod
    def get_candidate_2_config() -> CandidateConfig:
        return CandidateService.get_candidate_config(2)

    @staticmethod
    def get_candidate_3_config() -> CandidateConfig:
        return CandidateService.get_candidate_config(3)

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
        agent = CandidateService.build_candidate_agent(
            config=config,
            provider=provider,
        )
        return agent.generate(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
        )

    @staticmethod
    def build_candidate_agent(
        config: CandidateConfig,
        provider: LLMProvider | None = None,
    ) -> DiagramGenerationAgent:
        llm_provider = provider or get_llm_provider(config.provider)
        return CandidateDiagramAgent(
            config=config,
            provider=llm_provider,
        )

    @staticmethod
    def run_all_candidates_internal(
        requirements: str,
        requirement_ids: list[str] | None = None,
        candidate_configs: Sequence[CandidateConfig] | None = None,
        providers: Mapping[str, LLMProvider] | None = None,
    ) -> OrchestrationResult:
        configs = list(candidate_configs or CandidateService.get_candidate_configs())
        return run_ensemble_graph(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            candidate_configs=configs,
            providers=providers or {},
        )

    @staticmethod
    async def arun_all_candidates_internal(
        requirements: str,
        requirement_ids: list[str] | None = None,
        candidate_configs: Sequence[CandidateConfig] | None = None,
        providers: Mapping[str, LLMProvider] | None = None,
    ) -> OrchestrationResult:
        configs = list(candidate_configs or CandidateService.get_candidate_configs())
        return await arun_ensemble_graph(
            requirements=requirements,
            requirement_ids=requirement_ids or [],
            candidate_configs=configs,
            providers=providers or {},
        )
