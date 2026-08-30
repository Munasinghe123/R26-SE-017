import os

services_dir = 'd:/01 R/Research Antigravity/01 R/services'

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    if 'langchain_groq' in content or 'ChatGroq' in content:
        content = content.replace('from langchain_groq import ChatGroq', 'from langchain_openai import ChatOpenAI\nimport os')
        content = content.replace('ChatGroq(', 'ChatOpenAI(api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1", ')
        content = content.replace('model_name=', 'model=')
        content = content.replace('"llama-3.3-70b-versatile"', '"meta-llama/llama-3.3-70b-instruct"')
        changed = True

    if 'from groq import' in content or 'import groq' in content or 'Groq(' in content:
        content = content.replace('from groq import Groq', 'from openai import OpenAI')
        content = content.replace('from groq import AsyncGroq', 'from openai import AsyncOpenAI')
        content = content.replace('import groq', 'import openai')
        
        content = content.replace('GROQ_API_KEY', 'OPENROUTER_API_KEY')
        
        content = content.replace('Groq(api_key=', 'OpenAI(base_url="https://openrouter.ai/api/v1", api_key=')
        content = content.replace('AsyncGroq(api_key=', 'AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=')
        content = content.replace('self.client = Groq(api_key=self.api_key)', 'self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.api_key)')
        content = content.replace('max_completion_tokens=', 'max_tokens=')
        changed = True

    if changed:
        if 'import os' not in content and 'OPENROUTER_API_KEY' in content:
            content = 'import os\n' + content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Refactored: {filepath}')

for root, dirs, files in os.walk(services_dir):
    if 'venv' in root or '.venv' in root or '__pycache__' in root or 'node_modules' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            refactor_file(os.path.join(root, file))

print('Done')
