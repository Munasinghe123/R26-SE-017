from __future__ import annotations

from llm.groq_provider import GroqProvider
from llm.provider import LLMProvider


def get_llm_provider(provider: str) -> LLMProvider:
    normalized = (provider or "").strip().lower()
    if normalized == "groq":
        return GroqProvider()
    raise ValueError(f"Unsupported LLM provider: {provider}")
