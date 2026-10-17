import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

services = [
    ("Orchestrator (port 8000)", "services/orchestrator", "main"),
    ("Agent 1 - Requirements (port 8001)", "services/agent1-requirements", "main"),
    ("Agent 2 - HLD (port 8002)", "services/agent2-hld", "server"),
    ("Agent 3 - LLD (port 8003)", "services/agent3-lld", "main"),
    ("Agent 4 - UI (port 8004)", "services/agent4-ui", "api"),
    ("SRS Assembler (port 8005)", "services/srs-assembler", "main"),
]

print("=" * 65)
print("SYS DESIGN SERVICES — LOCAL IMPORT & HEALTH CHECK")
print("=" * 65)

failed = 0
for name, rel_path, module in services:
    cwd = BASE / rel_path
    cmd = [sys.executable, "-c", f"import {module}; print('Loaded app successfully')"]
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if res.returncode == 0:
        print(f"[PASS] {name}")
    else:
        failed += 1
        print(f"[FAIL] {name}")
        err_lines = [l for l in res.stderr.strip().splitlines() if l.strip()]
        last_err = err_lines[-1] if err_lines else "Unknown error"
        print(f"       Error: {last_err}")

print("=" * 65)
if failed == 0:
    print("ALL 6 BACKEND SERVICES IMPORTED CLEANLY WITHOUT ERRORS!")
else:
    print(f"{failed} SERVICE(S) HAD ISSUES.")
print("=" * 65)
