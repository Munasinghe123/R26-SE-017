import inspect
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

import Services.diagramOrchestrator as orchestrator_module
from graph.candidate import CandidateConfig, CandidateMetrics, CandidateState
from graph.ensemble_graph import run_ensemble_graph
from Services.diagramOrchestrator import OrchestrationResult, _build_orchestration_result


def configs() -> list[CandidateConfig]:
    return [
        CandidateConfig("candidate_1", "provider-1", "model-1"),
        CandidateConfig("candidate_2", "provider-2", "model-2"),
        CandidateConfig("candidate_3", "provider-3", "model-3"),
    ]


def state(
    candidate_id: str,
    status: str,
    model_calls: int = 0,
    tokens: int | None = None,
    latency_ms: float = 0.0,
) -> CandidateState:
    return CandidateState(
        candidate_id=candidate_id,
        provider=f"provider-{candidate_id}",
        model=f"model-{candidate_id}",
        status=status,
        metrics=CandidateMetrics(
            total_tokens=tokens,
            total_latency_ms=latency_ms,
            model_call_count=model_calls,
        ),
    )


class EnsembleAggregationTests(unittest.TestCase):
    def test_ensemble_graph_accepts_candidate_configs_and_aggregates_in_order(self):
        calls: list[str] = []
        candidates = {
            "candidate_1": state("candidate_1", "valid"),
            "candidate_2": state("candidate_2", "invalid"),
            "candidate_3": state("candidate_3", "failed"),
        }

        def fake_worker(**kwargs):
            candidate_id = kwargs["config"].candidate_id
            calls.append(candidate_id)
            return deepcopy(candidates[candidate_id])

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=fake_worker):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
            )

        self.assertIsInstance(result, OrchestrationResult)
        self.assertEqual(calls, ["candidate_1", "candidate_2", "candidate_3"])
        self.assertEqual(list(result.candidates.keys()), ["candidate_1", "candidate_2", "candidate_3"])

    def test_aggregation_module_has_no_provider_factory_env_or_groq_dependency(self):
        source = inspect.getsource(orchestrator_module)

        self.assertNotIn("get_llm_provider", source)
        self.assertNotIn("os.getenv", source)
        self.assertNotIn("Groq(", source)

    def test_candidate_states_and_status_counts_are_preserved(self):
        candidate_1 = state("candidate_1", "valid")
        candidate_2 = state("candidate_2", "invalid")
        candidate_3 = state("candidate_3", "failed")

        result = _build_orchestration_result(
            total_agents=3,
            candidates={
                "candidate_1": candidate_1,
                "candidate_2": candidate_2,
                "candidate_3": candidate_3,
            },
        )

        self.assertIs(result.candidates["candidate_1"], candidate_1)
        self.assertIs(result.candidates["candidate_2"], candidate_2)
        self.assertIs(result.candidates["candidate_3"], candidate_3)
        self.assertEqual(result.total_agents, 3)
        self.assertEqual(result.completed_agents, 3)
        self.assertEqual(result.valid_agents, 1)
        self.assertEqual(result.invalid_agents, 1)
        self.assertEqual(result.failed_agents, 1)

    def test_one_returned_failed_candidate_does_not_stop_remaining_agents(self):
        calls: list[str] = []
        candidates = {
            "candidate_1": state("candidate_1", "valid"),
            "candidate_2": state("candidate_2", "failed"),
            "candidate_3": state("candidate_3", "valid"),
        }

        def fake_worker(**kwargs):
            candidate_id = kwargs["config"].candidate_id
            calls.append(candidate_id)
            return deepcopy(candidates[candidate_id])

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=fake_worker):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=configs(),
            )

        self.assertEqual(calls, ["candidate_1", "candidate_2", "candidate_3"])
        self.assertEqual(result.valid_agents, 2)
        self.assertEqual(result.failed_agents, 1)

    def test_unexpected_agent_exception_is_isolated_and_recorded(self):
        calls: list[str] = []

        def fake_worker(**kwargs):
            candidate_id = kwargs["config"].candidate_id
            calls.append(candidate_id)
            if candidate_id == "candidate_2":
                raise RuntimeError("temporary provider outage with api-key-redacted")
            return state(candidate_id, "valid")

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=fake_worker):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=configs(),
            )

        self.assertEqual(calls, ["candidate_1", "candidate_2", "candidate_3"])
        failed = result.candidates["candidate_2"]
        self.assertEqual(failed.status, "failed")
        self.assertEqual(failed.provider_errors[0]["stage"], "agent")
        self.assertEqual(failed.provider_errors[0]["error_type"], "RuntimeError")
        self.assertIn("temporary provider outage", failed.provider_errors[0]["message"])
        self.assertEqual(result.valid_agents, 2)
        self.assertEqual(result.failed_agents, 1)

    def test_per_agent_metrics_remain_unchanged_and_totals_are_calculated(self):
        candidate_1 = state("candidate_1", "valid", model_calls=3, tokens=30, latency_ms=300.0)
        candidate_2 = state("candidate_2", "invalid", model_calls=2, tokens=20, latency_ms=200.0)
        candidate_3 = state("candidate_3", "failed", model_calls=1, tokens=None, latency_ms=100.0)

        result = _build_orchestration_result(
            total_agents=3,
            candidates={
                "candidate_1": candidate_1,
                "candidate_2": candidate_2,
                "candidate_3": candidate_3,
            },
        )

        self.assertEqual(result.candidates["candidate_1"].metrics.model_call_count, 3)
        self.assertEqual(result.candidates["candidate_2"].metrics.total_tokens, 20)
        self.assertIsNone(result.candidates["candidate_3"].metrics.total_tokens)
        self.assertEqual(result.total_model_calls, 6)
        self.assertEqual(result.total_tokens, 50)
        self.assertEqual(result.total_latency_ms, 600.0)

    def test_no_ranking_selection_expert_or_retry_surface_exists(self):
        result = _build_orchestration_result(
            total_agents=3,
            candidates={
                "candidate_1": state("candidate_1", "valid"),
                "candidate_2": state("candidate_2", "invalid"),
                "candidate_3": state("candidate_3", "failed"),
            },
        )

        self.assertFalse(hasattr(result, "best_candidate"))
        self.assertFalse(hasattr(result, "selected_candidate"))
        self.assertFalse(hasattr(result, "winner"))
        self.assertFalse(hasattr(result, "score"))
        self.assertFalse(hasattr(result, "expert_review"))

    def test_candidate_worker_is_called_once_without_semantic_retry(self):
        calls: list[tuple[str, str, list[str]]] = []

        def fake_worker(**kwargs):
            calls.append((
                kwargs["config"].candidate_id,
                kwargs["requirements"],
                kwargs["requirement_ids"],
            ))
            return state(kwargs["config"].candidate_id, "invalid")

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=fake_worker):
            run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
            )

        self.assertEqual(calls, [
            ("candidate_1", "Build system.", ["REQ-001"]),
            ("candidate_2", "Build system.", ["REQ-001"]),
            ("candidate_3", "Build system.", ["REQ-001"]),
        ])


if __name__ == "__main__":
    unittest.main()
