import re

with open("E:/01 R/hla_agent/server.py", "r", encoding="utf-8", errors="ignore") as f1:
    s1 = f1.read()
with open("d:/01 R/Research Antigravity/01 R/services/agent2-hld/server.py", "r", encoding="utf-8", errors="ignore") as f2:
    s2 = f2.read()

r1 = set(re.findall(r'@app\.(?:get|post|put|delete)\(["\']([^"\']+)["\']', s1))
r2 = set(re.findall(r'@app\.(?:get|post|put|delete)\(["\']([^"\']+)["\']', s2))

print("Routes in Original but missing in Migrated:")
for r in sorted(r1 - r2):
    print("  -", r)
