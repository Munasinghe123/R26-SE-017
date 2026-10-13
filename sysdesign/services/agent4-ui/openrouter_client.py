from langchain_openai import ChatOpenAI
import config


class ChatOpenRouter(ChatOpenAI):
    def __init__(self, model: str = config.LLM_MODEL, temperature: float = config.LLM_TEMPERATURE,
                 max_tokens: int = config.PLANNER_MAX_TOKENS, **kwargs):
        api_key = kwargs.pop("api_key", None) or config.OPENROUTER_API_KEY
        super().__init__(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

def get_openrouter_llm(model: str = config.LLM_MODEL, temperature: float = config.LLM_TEMPERATURE,
                       max_tokens: int = config.PLANNER_MAX_TOKENS):
    return ChatOpenRouter(model=model, temperature=temperature, max_tokens=max_tokens)