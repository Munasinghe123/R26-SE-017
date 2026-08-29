import os
import shutil

src_root = "E:/01 R/hla_agent"
dst_root = "d:/01 R/Research Antigravity/01 R/services/agent2-hld"

files_to_copy = [
    "output/diagram_evaluator.py",
    "output/diagram_workflow.py",
    "output/llm_diagram_gen.py",
    "output/side_by_side_diff.py",
    "output/report.py",
    "prompt/builder.py",
    "config.py",
    "main.py",
    "server.py",
]

for item in files_to_copy:
    s = os.path.join(src_root, item)
    d = os.path.join(dst_root, item)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    if os.path.exists(s):
        shutil.copy2(s, d)
        print(f"Copied: {item}")
    else:
        print(f"NOT FOUND: {s}")

print("Copy completed!")
