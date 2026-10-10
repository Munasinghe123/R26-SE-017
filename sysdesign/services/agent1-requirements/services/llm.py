import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env searching up from local service to sysdesign and workspace root
_base = Path(__file__).resolve()
for parent in [_base.parent, _base.parents[1], _base.parents[2], _base.parents[3]]:
    env_file = parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)

load_dotenv()


def get_llm(model: str = None, temperature: float = 0):
    selected_model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")
    return ChatOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model=selected_model,
        temperature=temperature,
    )


llm = get_llm()

