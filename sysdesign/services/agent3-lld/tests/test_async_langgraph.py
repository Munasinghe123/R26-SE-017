import asyncio
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig
from graph.candidate_graph import arun_candidate_graph
from graph.ensemble_graph import arun_ensemble_graph, arun_multi_agent_graph
from llm.provider import LLMResponse


def class_output(name: str) -> str:
    return (
        '{"class_diagram":{"classes":['
        f'{{"name":"{name}","attributes":["id"],"methods":["save{name}()"]}},'
        f'{{"name":"{name}Repository","attributes":["storage"],"methods":["save{name}()"]}}'
        f'],"relationships":[{{"source":"{name}Repository","target":"{name}",'
        '"type":"association","cardinality":"1"}]}}'
    )


def er_output(name: str) -> str:
    return (
        '{"er_diagram":{"entities":['
        f'{{"name":"{name}","attributes":["id"],"primary_key":"id"}}'
        '],"relationships":[]}}'
    )


def invalid_er_output(name: str) -> str:
    return (
        '{"er_diagram":{"entities":['
        f'{{"name":"{name}","attributes":["id"],"primary_key":""}}'
        '],"relationships":[]}}'
    )


def sequence_output(name: str) -> str:
    return (
        '{"sequence_diagrams":[{"name":"Save '
        f'{name}","description":"Save flow","participants":["{name}","{name}Repository"],'
        f'"messages":[{{"from":"{name}","to":"{name}Repository","message":"save{name}()"}}]}}]}}'
    )


def configs() -> list[CandidateConfig]:
    return [
        CandidateConfig("candidate_1", "provider-1", "model-1"),
        CandidateConfig("candidate_2", "provider-2", "model-2"),
        CandidateConfig("candidate_3", "provider-3", "model-3"),
    ]


class AsyncDelayProvider:
    def __init__(self, name, delay=0.02, outputs=None, error_on_call=None, tracker=None):
        self.name = name
        self.delay = delay
        self.outputs = list(outputs or [
            class_output(name),
            er_output(name),
            sequence_output(name),
        ])
        self.error_on_call = error_on_call
        self.calls = []
        self.tracker = tracker

    def complete(self, **kwargs):
        raise AssertionError("sync complete should not be used by async graph")

    async def acomplete(self, *, model, messages, temperature, max_tokens):
        call_number = len(self.calls) + 1
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if self.tracker is not None:
            self.tracker["active"] += 1
            self.tracker["max_active"] = max(self.tracker["max_active"], self.tracker["active"])
            self.tracker["starts"].append((self.name, call_number, time.perf_counter()))
            first_call_event = self.tracker.get("all_first_calls_started")
            if first_call_event is not None and call_number == 1:
                first_call_count = sum(
                    1 for _, started_call, _ in self.tracker["starts"]
                    if started_call == 1
                )
                if first_call_count >= 3:
                    first_call_event.set()
        try:
            if (
                self.tracker is not None
                and self.tracker.get("wait_for_first_calls")
                and call_number == 1
            ):
                await asyncio.wait_for(
                    self.tracker["all_first_calls_started"].wait(),
                    timeout=1,
                )
            await asyncio.sleep(self.delay)
            if self.error_on_call == call_number:
                raise RuntimeError(f"{self.name} provider failed")
            return LLMResponse(
                content=self.outputs.pop(0),
                provider=f"fake-{self.name}",
                model=model,
                input_tokens=call_number,
                output_tokens=call_number + 10,
                total_tokens=call_number + 20,
                latency_ms=float(call_number),
            )
        finally:
            if self.tracker is not None:
                self.tracker["active"] -= 1


class AsyncExpertProvider:
    def __init__(self, completed=None):
        self.completed = completed
        self.calls = []

    def complete(self, **kwargs):
        raise AssertionError("sync complete should not be used by async graph")

    async def acomplete(self, *, model, messages, temperature, max_tokens):
        self.calls.append(messages)
        if self.completed is not None and len(self.completed) != 3:
            raise AssertionError("expert review started before all candidates completed")
        return LLMResponse(
            content='{"selected_candidate_id":"candidate_1","reason":"selected","confidence":0.8}',
            provider="fake-expert",
            model=model,
        )


class AsyncGraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_candidate_async_graph_preserves_valid_output(self):
        provider = AsyncDelayProvider("Order", delay=0)

        state = await arun_candidate_graph(
            CandidateConfig("candidate_1", "fake", "model-x"),
            "Build ordering.",
            ["REQ-001"],
            provider,
        )

        self.assertEqual(state.status, "valid")
        self.assertIsNotNone(state.final_ir)
        self.assertEqual(len(provider.calls), 3)
        self.assertEqual(state.metrics.model_call_count, 3)

    async def test_candidate_async_repair_path_preserves_metadata(self):
        provider = AsyncDelayProvider(
            "Order",
            delay=0,
            outputs=[
                class_output("Order"),
                invalid_er_output("Order"),
                er_output("Order"),
                sequence_output("Order"),
            ],
        )

        state = await arun_candidate_graph(
            CandidateConfig("candidate_1", "fake", "model-x"),
            "Build ordering.",
            [],
            provider,
        )

        self.assertEqual(state.status, "valid")
        self.assertEqual(state.repair_metadata["er"]["repair_attempts"], 1)
        self.assertTrue(state.repair_metadata["er"]["repair_success"])
        self.assertIn("er_repair_1", state.metrics.stages)

    async def test_three_candidate_branches_overlap_in_async_fanout(self):
        tracker = {
            "active": 0,
            "max_active": 0,
            "starts": [],
            "all_first_calls_started": asyncio.Event(),
            "wait_for_first_calls": True,
        }
        providers = {
            "candidate_1": AsyncDelayProvider("Order", delay=0.05, tracker=tracker),
            "candidate_2": AsyncDelayProvider("Invoice", delay=0.05, tracker=tracker),
            "candidate_3": AsyncDelayProvider("Payment", delay=0.05, tracker=tracker),
        }
        sequential_expected = 3 * 3 * 0.05

        started = time.perf_counter()
        result = await arun_ensemble_graph(
            requirements="Build system.",
            requirement_ids=["REQ-001"],
            candidate_configs=configs(),
            providers=providers,
        )
        duration = time.perf_counter() - started

        self.assertEqual(list(result.candidates.keys()), ["candidate_1", "candidate_2", "candidate_3"])
        self.assertEqual(result.valid_agents, 3)
        self.assertGreaterEqual(tracker["max_active"], 3)
        self.assertGreater(sequential_expected, 0)
        self.assertGreater(duration, 0)

    async def test_one_slow_candidate_does_not_block_other_candidate_start(self):
        tracker = {
            "active": 0,
            "max_active": 0,
            "starts": [],
            "all_first_calls_started": asyncio.Event(),
            "wait_for_first_calls": True,
        }
        providers = {
            "candidate_1": AsyncDelayProvider("Order", delay=0.1, tracker=tracker),
            "candidate_2": AsyncDelayProvider("Invoice", delay=0.02, tracker=tracker),
            "candidate_3": AsyncDelayProvider("Payment", delay=0.02, tracker=tracker),
        }

        await arun_ensemble_graph(
            requirements="Build system.",
            requirement_ids=[],
            candidate_configs=configs(),
            providers=providers,
        )

        first_call_starts = [
            start for _, call_number, start in tracker["starts"]
            if call_number == 1
        ]
        self.assertEqual(len(first_call_starts), 3)
        self.assertTrue(tracker["all_first_calls_started"].is_set())
        self.assertGreaterEqual(tracker["max_active"], 3)

    async def test_failed_candidate_does_not_cancel_other_async_branches(self):
        providers = {
            "candidate_1": AsyncDelayProvider("Order", delay=0),
            "candidate_2": AsyncDelayProvider("Invoice", delay=0, error_on_call=1),
            "candidate_3": AsyncDelayProvider("Payment", delay=0),
        }

        result = await arun_ensemble_graph(
            requirements="Build system.",
            requirement_ids=[],
            candidate_configs=configs(),
            providers=providers,
        )

        self.assertEqual(result.candidates["candidate_1"].status, "valid")
        self.assertEqual(result.candidates["candidate_2"].status, "failed")
        self.assertEqual(result.candidates["candidate_3"].status, "valid")
        self.assertEqual(len(providers["candidate_3"].calls), 3)

    async def test_async_completion_order_does_not_change_aggregation_order(self):
        providers = {
            "candidate_1": AsyncDelayProvider("Order", delay=0.08),
            "candidate_2": AsyncDelayProvider("Invoice", delay=0.01),
            "candidate_3": AsyncDelayProvider("Payment", delay=0.03),
        }

        result = await arun_ensemble_graph(
            requirements="Build system.",
            requirement_ids=[],
            candidate_configs=configs(),
            providers=providers,
        )

        self.assertEqual(list(result.candidates.keys()), ["candidate_1", "candidate_2", "candidate_3"])

    async def test_expert_review_runs_after_all_async_candidates_finish(self):
        completed = set()

        class CompletingProvider(AsyncDelayProvider):
            async def acomplete(self, **kwargs):
                response = await super().acomplete(**kwargs)
                if len(self.calls) == 3:
                    completed.add(self.name)
                return response

        providers = {
            "candidate_1": CompletingProvider("Order", delay=0.01),
            "candidate_2": CompletingProvider("Invoice", delay=0.01),
            "candidate_3": CompletingProvider("Payment", delay=0.01),
        }

        with patch(
            "graph.ensemble_graph.ValidationService.validate",
            return_value={
                "report": {"passed": True, "errors": []},
                "errors": [],
                "expert_guidance": "",
            },
        ):
            result = await arun_multi_agent_graph(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=configs(),
                providers=providers,
                expert_review_provider=AsyncExpertProvider(completed),
            )

        self.assertEqual(result.selected_candidate.candidate_id, "candidate_1")
        self.assertEqual(completed, {"Order", "Invoice", "Payment"})


if __name__ == "__main__":
    unittest.main()
