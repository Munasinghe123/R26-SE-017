"""
HLA Agent — OpenRouter Provider

Single unified LLM provider for all models via OpenRouter API.
Uses OpenAI-compatible endpoint (https://openrouter.ai/api/v1).

Models are configured via environment variables:
    OPENROUTER_MODEL_1, OPENROUTER_MODEL_2, OPENROUTER_MODEL_3
"""

import os
import logging
from openai import OpenAI

from providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider — routes to any model via single API."""

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Get a key at https://openrouter.ai"
            )
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    @property
    def provider_name(self) -> str:
        return "OpenRouter"

    def generate(self, prompt: str, model: str, options: dict) -> str:
        """Generate architecture via OpenRouter API."""
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert software architect. Respond ONLY with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=options.get("temperature", 0.1),
            max_tokens=options.get("max_tokens", 4000),
            seed=options.get("seed", None),
        )
        return response.choices[0].message.content.strip()

    def list_models(self) -> list[str]:
        """List available OpenRouter models."""
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            logger.error(f"Failed to list OpenRouter models: {e}")
            return []

    def check_available(self, models: list[str]) -> dict[str, bool]:
        """Check model availability — if API key is set, assume available."""
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            return {m: False for m in models}
        return {m: True for m in models}
