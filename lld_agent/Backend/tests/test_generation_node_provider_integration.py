import os
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from graph import nodes
from llm.provider import LLMResponse


class FakeProvider:
    def complete(self, *, model, messages, temperature, max_tokens):
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.max_tokens = max_tokens
        return LLMResponse(
            content='{"class_diagram": {}, "sequence_diagrams": [], "er_diagram": {}}',
            provider="fake",
            model=model,
        )


class GenerationNodeProviderIntegrationTests(unittest.TestCase):
    def test_generate_node_uses_llm_response_content(self):
        original_provider = nodes.llm_provider
        fake_provider = FakeProvider()
        nodes.llm_provider = fake_provider
        try:
            result = nodes.generate_node({
                "requirements": "Build a small ordering system.",
                "requirement_ids": [],
                "extra_rules": "",
                "llm_response": "",
                "parsed_json": None,
                "validation_result": None,
                "iterations_used": 0,
                "max_iterations": 3,
                "is_successful": False,
            })
        finally:
            nodes.llm_provider = original_provider

        self.assertEqual(
            result["llm_response"],
            '{"class_diagram": {}, "sequence_diagrams": [], "er_diagram": {}}',
        )
        self.assertEqual(result["iterations_used"], 1)
        self.assertEqual(fake_provider.temperature, 0)
        self.assertEqual(fake_provider.max_tokens, 3500)


if __name__ == "__main__":
    unittest.main()
