import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig, CandidateMetrics, CandidateState
from graph.ensemble_graph import _merge_candidate_results, run_ensemble_graph
from Services.candidateService import CandidateService
from Services.diagramOrchestrator import OrchestrationResult, _build_orchestration_result


def configs() -> list[CandidateConfig]:
    return [
        CandidateConfig("candidate_1", "provider-1", "model-1", temperature=0.1, max_tokens=1001),
        CandidateConfig("candidate_2", "provider-2", "model-2", temperature=0.2, max_tokens=1002),
        CandidateConfig("candidate_3", "provider-3", "model-3", temperature=0.3, max_tokens=1003),
    ]


def state(
    candidate_id: str,
    status: str = "valid",
    name: str | None = None,
    calls: int = 3,
    tokens: int | None = 60,
    latency: float = 6.0,
) -> CandidateState:
    artifact_name = name or candidate_id.title().replace("_", "")
    return CandidateState(
        candidate_id=candidate_id,
        provider=f"provider-{candidate_id}",
        model=f"model-{candidate_id}",
        status=status,
        class_diagram={
            "classes": [{"name": artifact_name, "attributes": ["id"], "methods": ["save()"]}],
            "relationships": [],
        },
        er_diagram={
            "entities": [{"name": artifact_name, "attributes": ["id"], "primary_key": "id"}],
            "relationships": [],
        },
        sequence_diagrams=[{
            "name": f"Save {artifact_name}",
            "participants": [artifact_name],
            "messages": [],
        }],
        class_validation={"passed": status == "valid", "errors": [], "warnings": [], "total_checks": 1, "passed_checks": int(status == "valid")},
        er_validation={"passed": status == "valid", "errors": [], "warnings": [], "total_checks": 1, "passed_checks": int(status == "valid")},
        sequence_validation={"passed": status == "valid", "errors": [], "warnings": [], "total_checks": 1, "passed_checks": int(status == "valid")},
        final_ir={
            "class_diagram": {"classes": [{"name": artifact_name}], "relationships": []},
            "er_diagram": {"entities": [{"name": artifact_name}], "relationships": []},
            "sequence_diagrams": [{"name": f"Save {artifact_name}"}],
        } if status != "failed" else None,
        repair_metadata={"class": {"repair_attempts": 0}},
        metrics=CandidateMetrics(
            total_tokens=tokens,
            total_latency_ms=latency,
            model_call_count=calls,
        ),
    )


def assert_orchestration_equivalent(test_case, actual: OrchestrationResult, expected: OrchestrationResult):
    test_case.assertEqual(actual.total_agents, expected.total_agents)
    test_case.assertEqual(actual.completed_agents, expected.completed_agents)
    test_case.assertEqual(actual.valid_agents, expected.valid_agents)
    test_case.assertEqual(actual.invalid_agents, expected.invalid_agents)
    test_case.assertEqual(actual.failed_agents, expected.failed_agents)
    test_case.assertEqual(actual.total_model_calls, expected.total_model_calls)
    test_case.assertEqual(actual.total_tokens, expected.total_tokens)
    test_case.assertEqual(actual.total_latency_ms, expected.total_latency_ms)
    test_case.assertEqual(list(actual.candidates.keys()), list(expected.candidates.keys()))
    test_case.assertEqual(actual.candidates, expected.candidates)


class EnsembleLangGraphTests(unittest.TestCase):
    def test_all_three_candidates_succeed_with_existing_result_shape_and_order(self):
        candidates = {
            "candidate_1": state("candidate_1", name="Order", tokens=30, latency=300.0),
            "candidate_2": state("candidate_2", name="Invoice", tokens=40, latency=400.0),
            "candidate_3": state("candidate_3", name="Payment", tokens=50, latency=500.0),
        }

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=lambda **kwargs: deepcopy(candidates[kwargs["config"].candidate_id])):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
            )

        self.assertIsInstance(result, OrchestrationResult)
        self.assertEqual(list(result.candidates.keys()), ["candidate_1", "candidate_2", "candidate_3"])
        self.assertEqual(result.valid_agents, 3)
        self.assertEqual(result.total_model_calls, 9)
        self.assertEqual(result.total_tokens, 120)
        self.assertEqual(result.total_latency_ms, 1200.0)

    def test_ensemble_result_matches_preserved_diagram_orchestrator_for_mocked_outputs(self):
        candidates = {
            "candidate_1": state("candidate_1", "valid", tokens=30, latency=300.0),
            "candidate_2": state("candidate_2", "invalid", tokens=20, latency=200.0),
            "candidate_3": state("candidate_3", "failed", calls=1, tokens=None, latency=100.0),
        }
        expected = _build_orchestration_result(
            total_agents=3,
            candidates=deepcopy(candidates),
        )

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=lambda **kwargs: deepcopy(candidates[kwargs["config"].candidate_id])):
            actual = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
            )

        assert_orchestration_equivalent(self, actual, expected)

    def test_candidate_state_mutations_do_not_leak_between_results(self):
        shared_template = state("candidate_1", name="Shared")

        def fake_worker(**kwargs):
            candidate = deepcopy(shared_template)
            candidate.candidate_id = kwargs["config"].candidate_id
            candidate.class_diagram["classes"][0]["name"] = kwargs["config"].candidate_id
            candidate.repair_metadata["class"]["candidate_id"] = kwargs["config"].candidate_id
            candidate.metrics.model_call_count = int(kwargs["config"].candidate_id[-1])
            return candidate

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=fake_worker):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=configs(),
            )

        result.candidates["candidate_1"].class_diagram["classes"][0]["name"] = "Mutated"
        result.candidates["candidate_1"].repair_metadata["class"]["candidate_id"] = "mutated"
        result.candidates["candidate_1"].metrics.model_call_count = 99

        self.assertEqual(result.candidates["candidate_2"].class_diagram["classes"][0]["name"], "candidate_2")
        self.assertEqual(result.candidates["candidate_3"].repair_metadata["class"]["candidate_id"], "candidate_3")
        self.assertEqual(result.candidates["candidate_2"].metrics.model_call_count, 2)

    def test_one_failed_candidate_does_not_prevent_other_candidates(self):
        def fake_worker(**kwargs):
            if kwargs["config"].candidate_id == "candidate_2":
                return state("candidate_2", "failed", calls=1, tokens=None, latency=10.0)
            return state(kwargs["config"].candidate_id, "valid", calls=3, tokens=30, latency=30.0)

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=fake_worker):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=configs(),
            )

        self.assertEqual(result.valid_agents, 2)
        self.assertEqual(result.failed_agents, 1)
        self.assertEqual(result.candidates["candidate_1"].status, "valid")
        self.assertEqual(result.candidates["candidate_2"].status, "failed")
        self.assertEqual(result.candidates["candidate_3"].status, "valid")

    def test_multiple_and_all_failed_candidates_preserve_counts(self):
        for statuses, expected_failed in [
            ({"candidate_1": "failed", "candidate_2": "failed", "candidate_3": "valid"}, 2),
            ({"candidate_1": "failed", "candidate_2": "failed", "candidate_3": "failed"}, 3),
        ]:
            with self.subTest(statuses=statuses):
                with patch(
                    "graph.ensemble_graph.run_candidate_graph",
                    side_effect=lambda **kwargs: state(
                        kwargs["config"].candidate_id,
                        statuses[kwargs["config"].candidate_id],
                        calls=1,
                        tokens=None,
                        latency=1.0,
                    ),
                ):
                    result = run_ensemble_graph(
                        requirements="Build system.",
                        requirement_ids=[],
                        candidate_configs=configs(),
                    )

                self.assertEqual(result.failed_agents, expected_failed)
                self.assertEqual(result.completed_agents, 3)
                self.assertEqual(result.total_agents, 3)

    def test_aggregation_normalizes_to_configured_order_not_worker_return_order(self):
        reversed_configs = list(reversed(configs()))

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=lambda **kwargs: state(kwargs["config"].candidate_id)):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=reversed_configs,
            )

        self.assertEqual(list(result.candidates.keys()), ["candidate_3", "candidate_2", "candidate_1"])

    def test_reducer_merges_by_candidate_id_without_last_write_wins_loss(self):
        candidate_1 = state("candidate_1")
        candidate_2 = state("candidate_2")

        merged = _merge_candidate_results(
            {"candidate_1": candidate_1},
            {"candidate_2": candidate_2},
        )

        self.assertEqual(set(merged.keys()), {"candidate_1", "candidate_2"})
        self.assertIs(merged["candidate_1"], candidate_1)
        self.assertIs(merged["candidate_2"], candidate_2)

    def test_unexpected_worker_exception_is_recorded_as_failed_candidate(self):
        def fake_worker(**kwargs):
            if kwargs["config"].candidate_id == "candidate_2":
                raise RuntimeError("candidate worker exploded")
            return state(kwargs["config"].candidate_id)

        with patch("graph.ensemble_graph.run_candidate_graph", side_effect=fake_worker):
            result = run_ensemble_graph(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=configs(),
            )

        failed = result.candidates["candidate_2"]
        self.assertEqual(failed.status, "failed")
        self.assertEqual(failed.provider_errors[0]["stage"], "agent")
        self.assertEqual(failed.provider_errors[0]["error_type"], "RuntimeError")
        self.assertIn("candidate worker exploded", failed.provider_errors[0]["message"])
        self.assertEqual(result.valid_agents, 2)

    def test_candidate_service_delegates_to_ensemble_graph_and_preserves_return_type(self):
        expected = OrchestrationResult(
            candidates={"candidate_1": state("candidate_1")},
            total_agents=1,
            completed_agents=1,
            valid_agents=1,
            invalid_agents=0,
            failed_agents=0,
            total_model_calls=3,
            total_tokens=60,
            total_latency_ms=6.0,
        )

        with patch("Services.candidateService.run_ensemble_graph", return_value=expected) as ensemble:
            result = CandidateService.run_all_candidates_internal(
                requirements="Build system.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
                providers={},
            )

        ensemble.assert_called_once_with(
            requirements="Build system.",
            requirement_ids=["REQ-001"],
            candidate_configs=configs(),
            providers={},
        )
        self.assertIs(result, expected)


if __name__ == "__main__":
    unittest.main()
