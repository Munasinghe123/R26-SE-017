import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig, CandidateState
from llm.provider import LLMResponse
from Services.candidateService import CandidateService
from Services.umlService import UMLService


VALID_CLASS = (
    '{"class_diagram":{"classes":['
    '{"name":"Order","attributes":["id"],"methods":["createOrder()"]},'
    '{"name":"OrderRepository","attributes":["storage"],"methods":["saveOrder()"]}'
    '],"relationships":[{"source":"OrderRepository","target":"Order","type":"association","cardinality":"1"}]}}'
)
INVALID_CLASS = (
    '{"class_diagram":{"classes":[{"name":"Order","attributes":[],"methods":[]}],"relationships":[]}}'
)
VALID_ER = (
    '{"er_diagram":{"entities":['
    '{"name":"Order","attributes":["id"],"primary_key":"id"}'
    '],"relationships":[]}}'
)
VALID_SEQUENCE = (
    '{"sequence_diagrams":[{"name":"Create Order","description":"Create order flow",'
    '"participants":["Order","OrderRepository"],'
    '"messages":[{"from":"Order","to":"OrderRepository","message":"saveOrder()"}]}]}'
)


class FakeProvider:
    def __init__(self, outputs=None, error_on_call=None):
        self.outputs = list(outputs or [VALID_CLASS, VALID_ER, VALID_SEQUENCE])
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
            raise RuntimeError("provider unavailable")
        return LLMResponse(
            content=self.outputs.pop(0),
            provider="fake",
            model=model,
            input_tokens=call_number,
            output_tokens=call_number + 10,
            total_tokens=call_number + 20,
            latency_ms=float(call_number * 100),
        )


class CandidateServiceTests(unittest.TestCase):
    def test_candidate_1_config_is_loaded_from_config(self):
        with patch("Services.candidateService.app_config.CANDIDATE_1_PROVIDER", "fake-provider"), \
             patch("Services.candidateService.app_config.CANDIDATE_1_MODEL", "fake-model"), \
             patch("Services.candidateService.app_config.CANDIDATE_1_TEMPERATURE", 0.3), \
             patch("Services.candidateService.app_config.CANDIDATE_1_MAX_TOKENS", 2222):
            config = CandidateService.get_candidate_1_config()

        self.assertEqual(config.candidate_id, "candidate_1")
        self.assertEqual(config.provider, "fake-provider")
        self.assertEqual(config.model, "fake-model")
        self.assertEqual(config.temperature, 0.3)
        self.assertEqual(config.max_tokens, 2222)

    def test_provider_factory_receives_candidate_1_provider(self):
        fake_provider = FakeProvider()
        with patch("Services.candidateService.get_llm_provider", return_value=fake_provider) as factory:
            state = CandidateService.run_candidate_internal(
                requirements="Build ordering.",
                requirement_ids=["REQ-001"],
                candidate_config=CandidateConfig(
                    candidate_id="candidate_1",
                    provider="configured-provider",
                    model="configured-model",
                ),
            )

        factory.assert_called_once_with("configured-provider")
        self.assertEqual(state.status, "valid")

    def test_candidate_runner_receives_candidate_1_model_config(self):
        fake_provider = FakeProvider()
        state = CandidateService.run_candidate_internal(
            requirements="Build ordering.",
            requirement_ids=[],
            candidate_config=CandidateConfig(
                candidate_id="candidate_1",
                provider="fake",
                model="configured-model",
                temperature=0.4,
                max_tokens=987,
            ),
            provider=fake_provider,
        )

        self.assertEqual(state.status, "valid")
        self.assertEqual([call["model"] for call in fake_provider.calls], ["configured-model"] * 3)
        self.assertEqual([call["temperature"] for call in fake_provider.calls], [0.4] * 3)
        self.assertEqual([call["max_tokens"] for call in fake_provider.calls], [987] * 3)

    def test_internal_orchestration_executes_complete_candidate_pipeline(self):
        fake_provider = FakeProvider()
        state = CandidateService.run_candidate_internal(
            requirements="Build ordering.",
            requirement_ids=["REQ-001"],
            candidate_config=CandidateConfig("candidate_1", "fake", "model-x"),
            provider=fake_provider,
        )

        self.assertEqual(state.status, "valid")
        self.assertEqual(len(fake_provider.calls), 3)
        self.assertIsNotNone(state.class_diagram)
        self.assertIsNotNone(state.er_diagram)
        self.assertIsNotNone(state.sequence_diagrams)
        self.assertIsNotNone(state.final_ir)

    def test_candidate_state_is_returned_preserved(self):
        fake_provider = FakeProvider()
        state = CandidateService.run_candidate_internal(
            requirements="Build ordering.",
            candidate_config=CandidateConfig("candidate_1", "fake", "model-x"),
            provider=fake_provider,
        )

        self.assertIsInstance(state, CandidateState)
        self.assertEqual(state.candidate_id, "candidate_1")
        self.assertEqual(state.provider, "fake")
        self.assertEqual(state.model, "model-x")
        self.assertIn("class_diagram", state.final_ir)

    def test_candidate_metrics_survive_orchestration(self):
        fake_provider = FakeProvider()
        state = CandidateService.run_candidate_internal(
            requirements="Build ordering.",
            candidate_config=CandidateConfig("candidate_1", "fake", "model-x"),
            provider=fake_provider,
        )

        self.assertEqual(state.metrics.model_call_count, 3)
        self.assertEqual(state.metrics.total_tokens, 66)
        self.assertEqual(state.metrics.total_latency_ms, 600.0)
        self.assertEqual(set(state.metrics.stages.keys()), {"class", "er", "sequence"})

    def test_invalid_candidate_state_is_returned_normally(self):
        fake_provider = FakeProvider([INVALID_CLASS, VALID_ER, VALID_SEQUENCE])
        state = CandidateService.run_candidate_internal(
            requirements="Build ordering.",
            candidate_config=CandidateConfig("candidate_1", "fake", "model-x"),
            provider=fake_provider,
        )

        self.assertEqual(state.status, "invalid")
        self.assertFalse(state.class_validation["passed"])
        self.assertIsNotNone(state.class_diagram)
        self.assertEqual(len(fake_provider.calls), 3)

    def test_failed_candidate_state_is_represented(self):
        fake_provider = FakeProvider(error_on_call=1)
        state = CandidateService.run_candidate_internal(
            requirements="Build ordering.",
            candidate_config=CandidateConfig("candidate_1", "fake", "model-x"),
            provider=fake_provider,
        )

        self.assertEqual(state.status, "failed")
        self.assertEqual(state.provider_errors[0]["stage"], "class")
        self.assertEqual(len(fake_provider.calls), 1)

    def test_candidate_config_does_not_change_generation_config(self):
        with patch("Services.candidateService.app_config.CANDIDATE_1_PROVIDER", "fake-provider"), \
             patch("Services.candidateService.app_config.CANDIDATE_1_MODEL", "fake-model"):
            config = CandidateService.get_candidate_1_config()

        self.assertEqual(config.provider, "fake-provider")

        import config.config as app_config
        self.assertEqual(app_config.GENERATION_PROVIDER, "groq")
        self.assertEqual(app_config.GENERATION_MODEL_1, "llama-3.3-70b-versatile")

    def test_uml_service_internal_entrypoint_delegates_without_public_flow(self):
        fake_state = CandidateState(
            candidate_id="candidate_1",
            provider="fake",
            model="fake-model",
            status="valid",
        )
        with patch(
            "Services.umlService.CandidateService.run_candidate_internal",
            return_value=fake_state,
        ) as run_internal:
            state = UMLService.generate_candidate_internal("Build ordering.", ["REQ-001"])

        run_internal.assert_called_once_with(
            requirements="Build ordering.",
            requirement_ids=["REQ-001"],
        )
        self.assertIs(state, fake_state)


if __name__ == "__main__":
    unittest.main()
