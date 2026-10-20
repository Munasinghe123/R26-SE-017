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
        timeout_val = float(os.getenv("OPENROUTER_TIMEOUT", "75.0"))
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=timeout_val,
        )

    @property
    def provider_name(self) -> str:
        return "OpenRouter"

    def generate(self, prompt: str, model: str, options: dict) -> str:
        """Generate architecture via OpenRouter API with automated model fallbacks."""
        from config import MODEL_FALLBACKS
        timeout_val = options.get("timeout", float(os.getenv("OPENROUTER_TIMEOUT", "75.0")))
        
        fallbacks = MODEL_FALLBACKS.get(model, [])
        model_chain = [model] + [fb for fb in fallbacks if fb != model]

        system_prompt = options.get(
            "system_prompt",
            "You are an expert software architect. Respond ONLY with valid JSON."
        )

        last_error = None
        for current_model in model_chain:
            try:
                extra_models = [current_model] + [m for m in model_chain if m != current_model]
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=options.get("temperature", 0.1),
                    max_tokens=options.get("max_tokens", 4000),
                    seed=options.get("seed", None),
                    timeout=timeout_val,
                    extra_body={"models": extra_models} if len(extra_models) > 1 else None,
                )
                content = response.choices[0].message.content.strip()
                if content:
                    return content
            except Exception as exc:
                last_error = exc
                logger.warning(
                    f"[OpenRouter] Model {current_model} call failed ({exc}). "
                    f"Attempting fallback in chain: {model_chain}..."
                )
                continue

        if last_error:
            raise last_error
        return ""

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
