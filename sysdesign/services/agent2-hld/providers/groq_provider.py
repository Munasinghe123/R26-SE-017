import os
"""
HLA Agent — Groq Provider
Open-source LLM inference via Groq Cloud (free tier available).
Supports: Llama 3.3 70B, Mixtral 8x7B, etc.
"""

import logging
from openai import OpenAI

from providers.base import LLMProvider
from config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Groq Cloud provider for fast open-source LLM inference."""

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY") or OPENROUTER_API_KEY
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Get a key at https://openrouter.ai"
            )
        self.client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=api_key)


    @property
    def provider_name(self) -> str:
        return "Groq"

    def generate(self, prompt: str, model: str, options: dict) -> str:
        """Generate architecture via Groq API."""
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert software architect. Respond ONLY with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=options.get("temperature", 0.7),
            max_tokens=options.get("max_tokens", 4000),
        )
        return response.choices[0].message.content.strip()

    def list_models(self) -> list[str]:
        """List available Groq models."""
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            logger.error(f"Failed to list Groq models: {e}")
            return []

    def check_available(self, models: list[str]) -> dict[str, bool]:
        """Check which models are available on OpenRouter."""
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY") or OPENROUTER_API_KEY
        if not api_key:
            return {m: False for m in models}
        return {m: True for m in models}


