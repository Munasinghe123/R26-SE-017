import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph.candidate import CandidateConfig, run_candidate  # noqa: E402
from llm.provider import LLMResponse  # noqa: E402


VALID_CLASS = (
    '{"class_diagram":{"classes":['
    '{"name":"Order","attributes":["id"],"methods":["createOrder()"]},'
    '{"name":"OrderRepository","attributes":["storage"],"methods":["saveOrder()"]}'
    '],"relationships":[{"source":"OrderRepository","target":"Order","type":"association","cardinality":"1"}]}}'
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
    def __init__(self):
        self.outputs = [VALID_CLASS, VALID_ER, VALID_SEQUENCE]
        self.calls = []

    def complete(self, *, model, messages, temperature, max_tokens):
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        return LLMResponse(
            content=self.outputs.pop(0),
            provider="fake",
            model=model,
        )


class CandidateProviderIntegrationTests(unittest.TestCase):
    def test_candidate_pipeline_uses_injected_provider_responses(self):
        provider = FakeProvider()
        config = CandidateConfig(
            candidate_id="candidate_1",
            provider="fake",
            model="model-x",
            temperature=0.2,
            max_tokens=777,
        )

        state = run_candidate(
            config=config,
            requirements="Build a small ordering system.",
            requirement_ids=["REQ-001"],
            provider=provider,
        )

        self.assertEqual(state.status, "valid")
        self.assertEqual(state.class_response, VALID_CLASS)
        self.assertEqual(state.er_response, VALID_ER)
        self.assertEqual(state.sequence_response, VALID_SEQUENCE)
        self.assertEqual(len(provider.calls), 3)
        self.assertEqual([call["model"] for call in provider.calls], ["model-x"] * 3)
        self.assertEqual([call["temperature"] for call in provider.calls], [0.2] * 3)
        self.assertEqual([call["max_tokens"] for call in provider.calls], [777] * 3)


if __name__ == "__main__":
    unittest.main()
