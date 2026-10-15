import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig, CandidateState
from graph.diagram_agent import CandidateDiagramAgent
from llm.provider import LLMResponse
from Services.candidateService import CandidateService
from Services.diagramOrchestrator import OrchestrationResult


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


def sequence_output(name: str) -> str:
    return (
        '{"sequence_diagrams":[{"name":"Save '
        f'{name}","description":"Save flow","participants":["{name}","{name}Repository"],'
        f'"messages":[{{"from":"{name}","to":"{name}Repository","message":"save{name}()"}}]}}]}}'
    )


class FakeProvider:
    def __init__(self, name: str, error_on_call: int | None = None):
        self.name = name
        self.outputs = [class_output(name), er_output(name), sequence_output(name)]
        self.error_on_call = error_on_call
        self.calls = []

    def complete(self, *, model, messages, temperature, max_tokens):
        call_number = len(self.calls) + 1
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
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


def configs() -> list[CandidateConfig]:
    return [
        CandidateConfig("candidate_1", "provider-1", "model-1", temperature=0.1, max_tokens=1001),
        CandidateConfig("candidate_2", "provider-2", "model-2", temperature=0.2, max_tokens=1002),
        CandidateConfig("candidate_3", "provider-3", "model-3", temperature=0.3, max_tokens=1003),
    ]


def prompt_input_after(prompt: str, marker: str) -> str:
    return prompt.split(marker, 1)[1] if marker in prompt else prompt


class CandidateMultiAgentInternalTests(unittest.TestCase):
    def test_three_candidate_configs_are_loaded_from_indexed_config(self):
        with patch("Services.candidateService.app_config.CANDIDATE_1_PROVIDER", "provider-1"), \
             patch("Services.candidateService.app_config.CANDIDATE_1_MODEL", "model-1"), \
             patch("Services.candidateService.app_config.CANDIDATE_1_TEMPERATURE", 0.1), \
             patch("Services.candidateService.app_config.CANDIDATE_1_MAX_TOKENS", 1001), \
             patch("Services.candidateService.app_config.CANDIDATE_2_PROVIDER", "provider-2"), \
             patch("Services.candidateService.app_config.CANDIDATE_2_MODEL", "model-2"), \
             patch("Services.candidateService.app_config.CANDIDATE_2_TEMPERATURE", 0.2), \
             patch("Services.candidateService.app_config.CANDIDATE_2_MAX_TOKENS", 1002), \
             patch("Services.candidateService.app_config.CANDIDATE_3_PROVIDER", "provider-3"), \
             patch("Services.candidateService.app_config.CANDIDATE_3_MODEL", "model-3"), \
             patch("Services.candidateService.app_config.CANDIDATE_3_TEMPERATURE", 0.3), \
             patch("Services.candidateService.app_config.CANDIDATE_3_MAX_TOKENS", 1003):
            loaded = CandidateService.get_candidate_configs()

        self.assertEqual([config.candidate_id for config in loaded], [
            "candidate_1",
            "candidate_2",
            "candidate_3",
        ])
        self.assertEqual([config.provider for config in loaded], ["provider-1", "provider-2", "provider-3"])
        self.assertEqual([config.model for config in loaded], ["model-1", "model-2", "model-3"])
        self.assertEqual([config.temperature for config in loaded], [0.1, 0.2, 0.3])
        self.assertEqual([config.max_tokens for config in loaded], [1001, 1002, 1003])

    def test_invalid_candidate_config_index_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported candidate number"):
            CandidateService.get_candidate_config(4)

    def test_three_agents_can_be_constructed_from_configs_with_injected_providers(self):
        providers = {
            "candidate_1": FakeProvider("Order"),
            "candidate_2": FakeProvider("Invoice"),
            "candidate_3": FakeProvider("Payment"),
        }

        agents = [
            CandidateService.build_candidate_agent(config, providers[config.candidate_id])
            for config in configs()
        ]

        self.assertEqual(len(agents), 3)
        self.assertTrue(all(type(agent) is CandidateDiagramAgent for agent in agents))
        self.assertEqual([agent.config.model for agent in agents], ["model-1", "model-2", "model-3"])
        self.assertIs(agents[0].provider, providers["candidate_1"])
        self.assertIs(agents[1].provider, providers["candidate_2"])
        self.assertIs(agents[2].provider, providers["candidate_3"])

    def test_run_all_candidates_delegates_to_ensemble_graph_with_configs_in_order(self):
        expected_states = {
            "candidate_1": CandidateState("candidate_1", "provider-1", "model-1", status="valid"),
            "candidate_2": CandidateState("candidate_2", "provider-2", "model-2", status="valid"),
            "candidate_3": CandidateState("candidate_3", "provider-3", "model-3", status="valid"),
        }
        expected_result = OrchestrationResult(
            candidates=expected_states,
            total_agents=3,
            completed_agents=3,
            valid_agents=3,
            invalid_agents=0,
            failed_agents=0,
            total_model_calls=0,
            total_tokens=None,
            total_latency_ms=None,
        )

        with patch("Services.candidateService.run_ensemble_graph", return_value=expected_result) as ensemble:
            results = CandidateService.run_all_candidates_internal(
                requirements="Build system.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
            )

        self.assertIsInstance(results, OrchestrationResult)
        self.assertEqual(list(results.candidates.keys()), ["candidate_1", "candidate_2", "candidate_3"])
        ensemble.assert_called_once_with(
            requirements="Build system.",
            requirement_ids=["REQ-001"],
            candidate_configs=configs(),
            providers={},
        )

    def test_run_all_candidates_delegates_execution_to_ensemble_graph(self):
        expected_result = OrchestrationResult(
            candidates={},
            total_agents=0,
            completed_agents=0,
            valid_agents=0,
            invalid_agents=0,
            failed_agents=0,
            total_model_calls=0,
            total_tokens=None,
            total_latency_ms=None,
        )

        with patch("Services.candidateService.run_ensemble_graph", return_value=expected_result) as ensemble:
            result = CandidateService.run_all_candidates_internal(
                requirements="Build system.",
                requirement_ids=["REQ-001"],
                candidate_configs=configs(),
            )

        ensemble.assert_called_once_with(
            requirements="Build system.",
            requirement_ids=["REQ-001"],
            candidate_configs=configs(),
            providers={},
        )
        self.assertIs(result, expected_result)

    def test_run_all_candidates_returns_independent_candidate_states(self):
        providers = {
            "candidate_1": FakeProvider("Order"),
            "candidate_2": FakeProvider("Invoice"),
            "candidate_3": FakeProvider("Payment"),
        }

        results = CandidateService.run_all_candidates_internal(
            requirements="Build system.",
            requirement_ids=["REQ-001"],
            candidate_configs=configs(),
            providers=providers,
        )

        self.assertEqual(list(results.candidates.keys()), ["candidate_1", "candidate_2", "candidate_3"])
        self.assertTrue(all(isinstance(state, CandidateState) for state in results.candidates.values()))
        self.assertIsNot(results.candidates["candidate_1"], results.candidates["candidate_2"])
        self.assertIsNot(results.candidates["candidate_2"], results.candidates["candidate_3"])
        self.assertEqual(results.candidates["candidate_1"].class_diagram["classes"][0]["name"], "Order")
        self.assertEqual(results.candidates["candidate_2"].class_diagram["classes"][0]["name"], "Invoice")
        self.assertEqual(results.candidates["candidate_3"].class_diagram["classes"][0]["name"], "Payment")
        self.assertEqual(results.candidates["candidate_1"].metrics.model_call_count, 3)
        self.assertEqual(results.candidates["candidate_2"].metrics.model_call_count, 3)
        self.assertEqual(results.candidates["candidate_3"].metrics.model_call_count, 3)

    def test_candidate_artifacts_do_not_leak_between_agent_prompts(self):
        providers = {
            "candidate_1": FakeProvider("Order"),
            "candidate_2": FakeProvider("Invoice"),
            "candidate_3": FakeProvider("Payment"),
        }

        CandidateService.run_all_candidates_internal(
            requirements="Build system.",
            requirement_ids=[],
            candidate_configs=configs(),
            providers=providers,
        )

        candidate_2_er_prompt = providers["candidate_2"].calls[1]["messages"][1]["content"]
        candidate_3_sequence_prompt = providers["candidate_3"].calls[2]["messages"][1]["content"]
        candidate_2_er_input = prompt_input_after(candidate_2_er_prompt, "VALIDATED CLASS DIAGRAM:")
        candidate_3_sequence_input = prompt_input_after(candidate_3_sequence_prompt, "INPUT")

        self.assertIn('"Invoice"', candidate_2_er_input)
        self.assertNotIn('"Order","attributes"', candidate_2_er_input)
        self.assertIn('"Payment"', candidate_3_sequence_input)
        self.assertNotIn('"Order","attributes"', candidate_3_sequence_input)
        self.assertNotIn('"Invoice","attributes"', candidate_3_sequence_input)

    def test_er_and_sequence_generation_use_only_same_candidate_artifacts(self):
        providers = {
            "candidate_1": FakeProvider("Order"),
            "candidate_2": FakeProvider("Invoice"),
            "candidate_3": FakeProvider("Payment"),
        }

        CandidateService.run_all_candidates_internal(
            requirements="Build system.",
            requirement_ids=[],
            candidate_configs=configs(),
            providers=providers,
        )

        for candidate_id, expected_name in [
            ("candidate_1", "Order"),
            ("candidate_2", "Invoice"),
            ("candidate_3", "Payment"),
        ]:
            er_prompt = providers[candidate_id].calls[1]["messages"][1]["content"]
            sequence_prompt = providers[candidate_id].calls[2]["messages"][1]["content"]
            self.assertIn('"class_diagram"', er_prompt)
            self.assertIn(f'"{expected_name}"', er_prompt)
            self.assertIn('"class_diagram"', sequence_prompt)
            self.assertIn('"er_diagram"', sequence_prompt)
            self.assertIn(f'"{expected_name}"', sequence_prompt)

    def test_candidate_2_failure_does_not_prevent_candidate_3_from_running(self):
        providers = {
            "candidate_1": FakeProvider("Order"),
            "candidate_2": FakeProvider("Invoice", error_on_call=1),
            "candidate_3": FakeProvider("Payment"),
        }

        results = CandidateService.run_all_candidates_internal(
            requirements="Build system.",
            requirement_ids=[],
            candidate_configs=configs(),
            providers=providers,
        )

        self.assertEqual(results.candidates["candidate_1"].status, "valid")
        self.assertEqual(results.candidates["candidate_2"].status, "failed")
        self.assertEqual(results.candidates["candidate_2"].provider_errors[0]["stage"], "class")
        self.assertEqual(results.candidates["candidate_3"].status, "valid")
        self.assertEqual(len(providers["candidate_3"].calls), 3)

    def test_parsed_but_invalid_candidates_remain_present(self):
        invalid_provider = FakeProvider("Invoice")
        invalid_class = (
            '{"class_diagram":{"classes":[{"name":"Invoice","attributes":[],"methods":[]}],'
            '"relationships":[]}}'
        )
        invalid_provider.outputs = [
            invalid_class,
            invalid_class,
            invalid_class,
            er_output("Invoice"),
            sequence_output("Invoice"),
        ]
        providers = {
            "candidate_1": FakeProvider("Order"),
            "candidate_2": invalid_provider,
            "candidate_3": FakeProvider("Payment"),
        }

        results = CandidateService.run_all_candidates_internal(
            requirements="Build system.",
            requirement_ids=[],
            candidate_configs=configs(),
            providers=providers,
        )

        self.assertEqual(results.candidates["candidate_2"].status, "invalid")
        self.assertIsNotNone(results.candidates["candidate_2"].class_diagram)
        self.assertIsNotNone(results.candidates["candidate_2"].final_ir)
        self.assertIn("candidate_2", results.candidates)

    def test_run_all_candidates_does_not_select_or_call_expert_or_repair(self):
        providers = {
            "candidate_1": FakeProvider("Order"),
            "candidate_2": FakeProvider("Invoice"),
            "candidate_3": FakeProvider("Payment"),
        }

        with patch("Services.candidateService.get_llm_provider") as provider_factory:
            results = CandidateService.run_all_candidates_internal(
                requirements="Build system.",
                requirement_ids=[],
                candidate_configs=configs(),
                providers=providers,
            )

        provider_factory.assert_not_called()
        self.assertIsInstance(results, OrchestrationResult)
        self.assertFalse(hasattr(results, "selected_candidate_id"))
        self.assertFalse(hasattr(results, "best"))
        self.assertEqual([len(provider.calls) for provider in providers.values()], [3, 3, 3])


if __name__ == "__main__":
    unittest.main()
