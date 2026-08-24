import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY_TWO"),
    temperature=0,
    reasoning_effort="low",
    max_completion_tokens=4096
)

print("========== LLM INITIALIZATION ==========")
print("Model:", llm.model_name)
print("LLM type:", type(llm))
print("========================================")