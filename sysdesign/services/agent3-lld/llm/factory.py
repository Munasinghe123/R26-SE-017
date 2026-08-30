from __future__ import annotations

from llm.groq_provider import GroqProvider
from llm.provider import LLMProvider


def get_llm_provider(provider: str) -> LLMProvider:
    normalized = (provider or "").strip().lower()
    if normalized in ("groq", "openai", "openrouter", "deepseek", "gemini", ""):
        return GroqProvider()
    return GroqProvider()
