import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("GROQ_API_KEY", "test-key")

from llm.factory import get_llm_provider
from llm.groq_provider import GroqProvider
from llm.provider import LLMResponse


class FakeCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        self.last_kwargs = kwargs
        return outcome


class FakeClient:
    def __init__(self, outcomes):
        self.completions = FakeCompletions(outcomes)
        self.chat = SimpleNamespace(completions=self.completions)


class FakeRateLimitError(Exception):
    status_code = 429


def make_response(content="{}", usage=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ],
        usage=usage,
    )


class LLMProviderTests(unittest.TestCase):
    def test_factory_resolves_groq(self):
        provider = get_llm_provider("groq")
        self.assertIsInstance(provider, GroqProvider)

    def test_factory_rejects_unsupported_provider(self):
        with self.assertRaisesRegex(ValueError, "Unsupported LLM provider"):
            get_llm_provider("missing-provider")

    def test_groq_provider_returns_llm_response(self):
        client = FakeClient([make_response(content='{"ok": true}')])
        provider = GroqProvider(client=client)

        response = provider.complete(
            model="test-model",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0,
            max_tokens=100,
        )

        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.provider, "groq")
        self.assertEqual(response.model, "test-model")
        self.assertEqual(response.content, '{"ok": true}')
        self.assertIsNotNone(response.latency_ms)
        self.assertEqual(client.completions.last_kwargs["max_completion_tokens"], 100)

    def test_groq_provider_copies_token_usage_when_available(self):
        usage = SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=7,
            total_tokens=18,
        )
        client = FakeClient([make_response(content="{}", usage=usage)])
        provider = GroqProvider(client=client)

        response = provider.complete(
            model="token-model",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0,
            max_tokens=100,
        )

        self.assertEqual(response.input_tokens, 11)
        self.assertEqual(response.output_tokens, 7)
        self.assertEqual(response.total_tokens, 18)
        self.assertEqual(response.raw_usage["prompt_tokens"], 11)

    def test_groq_provider_retries_rate_limits_then_succeeds(self):
        client = FakeClient([
            FakeRateLimitError("try again in 0s"),
            FakeRateLimitError("try again in 0s"),
            make_response(content='{"ok": true}'),
        ])
        provider = GroqProvider(client=client)

        with patch("llm.groq_provider.time.sleep") as sleep:
            response = provider.complete(
                model="retry-model",
                messages=[{"role": "user", "content": "hello"}],
                temperature=0,
                max_tokens=100,
            )

        self.assertEqual(response.content, '{"ok": true}')
        self.assertEqual(client.completions.calls, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_groq_provider_retry_behavior_is_bounded(self):
        client = FakeClient([
            FakeRateLimitError("try again in 0s"),
            FakeRateLimitError("try again in 0s"),
            FakeRateLimitError("try again in 0s"),
        ])
        provider = GroqProvider(client=client)

        with patch("llm.groq_provider.time.sleep"):
            with self.assertRaises(FakeRateLimitError):
                provider.complete(
                    model="retry-model",
                    messages=[{"role": "user", "content": "hello"}],
                    temperature=0,
                    max_tokens=100,
                )

        self.assertEqual(client.completions.calls, 3)


if __name__ == "__main__":
    unittest.main()
