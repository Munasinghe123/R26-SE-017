import os
import re

lld_dir = "E:/01 R/LLD backend only/Backend"

print("=== Searching for Models, Expert Agent, and Generation in LLD ===")
for root, dirs, files in os.walk(lld_dir):
    if "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Check for model strings or config
            models = re.findall(r'(?:MODEL|model|GENERATION_MODEL|EXPERT_MODEL)[^\n=]*=\s*["\']([^"\']+)["\']', content)
            if models:
                print(f"File: {file} -> Models found: {models}")

print("\n=== Searching for Main Orchestrator / Pipeline Entrypoint in LLD ===")
for root, dirs, files in os.walk(lld_dir):
    if "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "def " in content or "class " in content:
                funcs = re.findall(r'def\s+([a-zA-Z0-9_]+)\(', content)
                print(f"File: {file} -> Functions: {funcs[:8]}")
