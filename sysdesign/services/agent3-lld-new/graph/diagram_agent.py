from __future__ import annotations

from typing import Protocol, runtime_checkable

from graph.candidate import CandidateConfig, CandidateState, run_candidate
from llm.provider import LLMProvider


@runtime_checkable
class DiagramGenerationAgent(Protocol):
    def generate(
        self,
        requirements: str,
        requirement_ids: list[str],
    ) -> CandidateState:
        ...


class CandidateDiagramAgent:
    def __init__(
        self,
        config: CandidateConfig,
        provider: LLMProvider,
    ) -> None:
        self.config = config
        self.provider = provider

    def generate(
        self,
        requirements: str,
        requirement_ids: list[str],
    ) -> CandidateState:
        return run_candidate(
            config=self.config,
            requirements=requirements,
            requirement_ids=requirement_ids,
            provider=self.provider,
        )
