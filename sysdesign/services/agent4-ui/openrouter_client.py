import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

class ChatOpenRouter(ChatOpenAI):
    def __init__(self, model: str = "qwen/qwen3-coder", temperature: float = 0.2, max_tokens: int = 1800, **kwargs):
        api_key = kwargs.pop("api_key", None) or os.getenv("OPENROUTER_API_KEY")
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

def get_openrouter_llm(model: str = "qwen/qwen3-coder", temperature: float = 0.2, max_tokens: int = 1800):
    return ChatOpenRouter(model=model, temperature=temperature, max_tokens=max_tokens)
