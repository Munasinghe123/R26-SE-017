from __future__ import annotations

from typing import Protocol, runtime_checkable

from graph.srs_state import SRSConfig, SRSState
from graph.srs_graph import run_srs_graph, arun_srs_graph
from llm.provider import LLMProvider


@runtime_checkable
class SRSAgentProtocol(Protocol):
    def generate(
        self,
        config: SRSConfig,
        requirements: dict,
        hld_annex: dict | None = None,
        lld_annex: dict | None = None,
        ui_annex: dict | None = None,
    ) -> SRSState:
        ...

    async def agenerate(
        self,
        config: SRSConfig,
        requirements: dict,
        hld_annex: dict | None = None,
        lld_annex: dict | None = None,
        ui_annex: dict | None = None,
    ) -> SRSState:
        ...


class SRSAgent:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider

    def generate(
        self,
        config: SRSConfig,
        requirements: dict,
        hld_annex: dict | None = None,
        lld_annex: dict | None = None,
        ui_annex: dict | None = None,
    ) -> SRSState:
        return run_srs_graph(
            config=config,
            requirements=requirements,
            hld_annex=hld_annex,
            lld_annex=lld_annex,
            ui_annex=ui_annex,
            provider=self.provider,
        )

    async def agenerate(
        self,
        config: SRSConfig,
        requirements: dict,
        hld_annex: dict | None = None,
        lld_annex: dict | None = None,
        ui_annex: dict | None = None,
    ) -> SRSState:
        return await arun_srs_graph(
            config=config,
            requirements=requirements,
            hld_annex=hld_annex,
            lld_annex=lld_annex,
            ui_annex=ui_annex,
            provider=self.provider,
        )
