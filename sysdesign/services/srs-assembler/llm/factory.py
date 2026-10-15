import os
from pathlib import Path
from dotenv import load_dotenv
from .provider import LLMProvider, OpenRouterProvider

# Search upwards from this file to sysdesign or workspace root to load .env
_base = Path(__file__).resolve()
for parent in [_base.parent, _base.parents[1], _base.parents[2], _base.parents[3]]:
    env_file = parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
load_dotenv()


def get_llm_provider(provider_name: str = "openrouter") -> LLMProvider:
    provider = (provider_name or "openrouter").lower()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Please add it to your .env file."
            )
        return OpenRouterProvider(api_key=api_key)
    raise ValueError(f"Unsupported LLM provider: {provider_name}")
