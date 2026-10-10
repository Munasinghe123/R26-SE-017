"""
HLA Agent — Provider Factory (Simplified)

Single OpenRouter provider for all models.
"""

import logging
from providers.base import LLMProvider

logger = logging.getLogger(__name__)

# Cached singleton
_provider_instance: LLMProvider | None = None


def get_provider(provider_name: str | None = None) -> LLMProvider:
    """Get the OpenRouter provider instance (singleton).

    Args:
        provider_name: Ignored — only OpenRouter is supported.

    Returns:
        OpenRouterProvider instance
    """
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    from providers.openrouter_provider import OpenRouterProvider

    _provider_instance = OpenRouterProvider()
    logger.info(f"Initialized LLM provider: {_provider_instance.provider_name}")
    return _provider_instance


def get_provider_for_model(model_name: str) -> LLMProvider:
    """Get provider for any model — always returns OpenRouter."""
    return get_provider()


def get_provider_name() -> str:
    """Get the provider name."""
    return "openrouter"


__all__ = ["get_provider", "get_provider_for_model", "get_provider_name", "LLMProvider"]
