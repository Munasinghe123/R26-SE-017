import os
import glob
import re

# We will recursively find all python files in services/
services_dir = "d:/01 R/Research Antigravity/01 R/services"

def refactor_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changed = False

    # 1. Replace langchain_groq -> langchain_openai
    if "langchain_groq" in content or "ChatGroq" in content:
        content = content.replace("from langchain_groq import ChatGroq", "from langchain_openai import ChatOpenAI\nimport os")
        # Replace ChatGroq(model_name="...", ...) -> ChatOpenAI(api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1", model="...", ...)
        # We can use regex to replace ChatGroq with ChatOpenAI and inject the api_key/base_url
        
        # Simple string replacement for the class name
        content = content.replace("ChatGroq(", "ChatOpenAI(api_key=os.getenv('OPENROUTER_API_KEY'), base_url='https://openrouter.ai/api/v1', ")
        
        # Replace model_name= with model=
        content = content.replace("model_name=", "model=")
        
        # Replace hardcoded models
        content = content.replace('"llama-3.3-70b-versatile"', '"meta-llama/llama-3.3-70b-instruct"')
        
        changed = True

    # 2. Replace groq python client with openai
    if "from groq import" in content or "import groq" in content or "Groq(" in content:
        content = content.replace("from groq import Groq", "from openai import OpenAI")
        content = content.replace("from groq import AsyncGroq", "from openai import AsyncOpenAI")
        content = content.replace("import groq", "import openai")
        
        content = content.replace("GROQ_API_KEY", "OPENROUTER_API_KEY")
        
        content = content.replace("Groq(api_key=", "OpenAI(base_url='https://openrouter.ai/api/v1', api_key=")
        content = content.replace("AsyncGroq(api_key=", "AsyncOpenAI(base_url='https://openrouter.ai/api/v1', api_key=")
        
        # Agent 3 specific
        content = content.replace("self.client = Groq(api_key=self.api_key)", "self.client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=self.api_key)")
        
        # Replace max_completion_tokens with max_tokens in completions.create
        content = content.replace("max_completion_tokens=", "max_tokens=")
        
        changed = True

    if changed:
        # Add import os if not there (for os.getenv)
        if "import os" not in content and "OPENROUTER_API_KEY" in content:
            content = "import os\n" + content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Refactored: {filepath}")

for root, dirs, files in os.walk(services_dir):
    # skip venv
    if ".venv" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            refactor_file(os.path.join(root, file))

# We also need to change agent2's config to load OPENROUTER_API_KEY
# Let's fix agent2 config
config_agent2 = "d:/01 R/Research Antigravity/01 R/services/agent2-hld/config.py"
if os.path.exists(config_agent2):
    with open(config_agent2, "r") as f:
        c = f.read()
    c = c.replace("GROQ_API_KEY = os.getenv(\"GROQ_API_KEY\")", "OPENROUTER_API_KEY = os.getenv(\"OPENROUTER_API_KEY\")")
    with open(config_agent2, "w") as f:
        f.write(c)

config_agent3 = "d:/01 R/Research Antigravity/01 R/services/agent3-lld/config/config.py"
if os.path.exists(config_agent3):
    with open(config_agent3, "r") as f:
        c = f.read()
    c = c.replace("GROQ_API_KEY = os.getenv(\"GROQ_API_KEY\")", "OPENROUTER_API_KEY = os.getenv(\"OPENROUTER_API_KEY\")")
    with open(config_agent3, "w") as f:
        f.write(c)

print("Done")
