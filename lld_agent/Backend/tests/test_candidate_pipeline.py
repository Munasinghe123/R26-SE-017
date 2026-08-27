import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig, run_candidate
from llm.provider import LLMResponse


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
INVALID_ER = (
    '{"er_diagram":{"entities":[{"name":"Order","attributes":["id"],"primary_key":""}],"relationships":[]}}'
)
VALID_SEQUENCE = (
    '{"sequence_diagrams":[{"name":"Create Order","description":"Create order flow",'
    '"participants":["Order","OrderRepository"],'
    '"messages":[{"from":"Order","to":"OrderRepository","message":"saveOrder()"}]}]}'
)
INVALID_SEQUENCE = (
    '{"sequence_diagrams":[{"name":"Create Order","description":"Create order flow",'
    '"participants":["Order","OrderRepository"],'
    '"messages":[{"from":"Order","to":"OrderRepository","message":"missingMethod()"}]}]}'
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


def candidate_config():
    return CandidateConfig(
        candidate_id="candidate_x",
        provider="fake",
        model="model-x",
        temperature=0.1,
        max_tokens=1234,
    )


class CandidatePipelineTests(unittest.TestCase):
    def test_candidate_config_stores_provider_and_model(self):
        config = candidate_config()
        self.assertEqual(config.candidate_id, "candidate_x")
        self.assertEqual(config.provider, "fake")
        self.assertEqual(config.model, "model-x")
        self.assertEqual(config.temperature, 0.1)
        self.assertEqual(config.max_tokens, 1234)

    def test_runner_calls_class_er_sequence_in_order(self):
        provider = FakeProvider()
        state = run_candidate(candidate_config(), "Build ordering.", ["REQ-001"], provider)

        self.assertEqual(state.status, "valid")
        self.assertEqual(len(provider.calls), 3)
        system_prompts = [call["messages"][0]["content"] for call in provider.calls]
        self.assertIn("class diagram", system_prompts[0].lower())
        self.assertIn("er diagram", system_prompts[1].lower())
        self.assertIn("sequence diagram", system_prompts[2].lower())

    def test_er_generation_receives_same_candidate_class_diagram(self):
        provider = FakeProvider()
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        er_prompt = provider.calls[1]["messages"][1]["content"]
        self.assertIn('"class_diagram"', er_prompt)
        self.assertIn('"OrderRepository"', er_prompt)
        self.assertEqual(state.class_diagram["classes"][0]["name"], "Order")

    def test_sequence_generation_receives_same_candidate_class_and_er_diagrams(self):
        provider = FakeProvider()
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        sequence_prompt = provider.calls[2]["messages"][1]["content"]
        self.assertIn('"class_diagram"', sequence_prompt)
        self.assertIn('"er_diagram"', sequence_prompt)
        self.assertIn('"OrderRepository"', sequence_prompt)
        self.assertIn('"primary_key": "id"', sequence_prompt)
        self.assertEqual(state.er_diagram["entities"][0]["name"], "Order")

    def test_class_validation_failure_does_not_trigger_regeneration(self):
        provider = FakeProvider([INVALID_CLASS, VALID_ER, VALID_SEQUENCE])
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(len(provider.calls), 3)
        self.assertEqual(state.status, "invalid")
        self.assertFalse(state.class_validation["passed"])
        self.assertIsNotNone(state.class_diagram)

    def test_er_validation_failure_does_not_trigger_regeneration(self):
        provider = FakeProvider([VALID_CLASS, INVALID_ER, VALID_SEQUENCE])
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(len(provider.calls), 3)
        self.assertEqual(state.status, "invalid")
        self.assertFalse(state.er_validation["passed"])
        self.assertIsNotNone(state.er_diagram)

    def test_sequence_validation_failure_does_not_trigger_regeneration(self):
        provider = FakeProvider([VALID_CLASS, VALID_ER, INVALID_SEQUENCE])
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(len(provider.calls), 3)
        self.assertEqual(state.status, "invalid")
        self.assertFalse(state.sequence_validation["passed"])
        self.assertIsNotNone(state.sequence_diagrams)

    def test_parsed_but_invalid_output_is_retained(self):
        provider = FakeProvider([INVALID_CLASS, INVALID_ER, INVALID_SEQUENCE])
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(state.status, "invalid")
        self.assertIsNotNone(state.class_diagram)
        self.assertIsNotNone(state.er_diagram)
        self.assertIsNotNone(state.sequence_diagrams)
        self.assertIsNotNone(state.final_ir)

    def test_malformed_class_output_prevents_dependent_generation(self):
        provider = FakeProvider(["not json", VALID_ER, VALID_SEQUENCE])
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(state.status, "failed")
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(state.parse_errors[0]["stage"], "class")
        self.assertEqual(state.class_response, "not json")
        self.assertIsNone(state.er_diagram)

    def test_malformed_er_output_prevents_sequence_generation(self):
        provider = FakeProvider([VALID_CLASS, "not json", VALID_SEQUENCE])
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(state.status, "failed")
        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(state.parse_errors[0]["stage"], "er")
        self.assertEqual(state.er_response, "not json")
        self.assertIsNone(state.sequence_diagrams)

    def test_provider_failure_marks_candidate_failed(self):
        provider = FakeProvider(error_on_call=2)
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(state.status, "failed")
        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(state.provider_errors[0]["stage"], "er")
        self.assertEqual(state.provider_errors[0]["error_type"], "RuntimeError")

    def test_metrics_aggregate_across_three_stage_calls(self):
        provider = FakeProvider()
        state = run_candidate(candidate_config(), "Build ordering.", [], provider)

        self.assertEqual(state.metrics.model_call_count, 3)
        self.assertEqual(state.metrics.total_tokens, 66)
        self.assertEqual(state.metrics.total_latency_ms, 600.0)
        self.assertEqual(state.metrics.stages["class"].provider, "fake")
        self.assertEqual(state.metrics.stages["er"].model, "model-x")
        self.assertEqual(state.metrics.stages["sequence"].model_call_count, 1)


if __name__ == "__main__":
    unittest.main()
