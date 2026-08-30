import os
import re

html_path = "E:/01 R/hla_agent/web/index.html"
js_path = "E:/01 R/hla_agent/web/app.js"
server_path = "E:/01 R/hla_agent/server.py"

print("=== HTML IDs & Headings ===")
if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    ids = re.findall(r'id=["\']([^"\']+)["\']', html)
    print("IDs found:", ids[:30])

print("\n=== JS Key Functions / Logic ===")
if os.path.exists(js_path):
    with open(js_path, "r", encoding="utf-8", errors="ignore") as f:
        js = f.read()
    funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)', js)
    const_funcs = re.findall(r'const\s+([a-zA-Z0-9_]+)\s*=\s*(?:function|\([^)]*\)\s*=>)', js)
    print("Functions found:", funcs + const_funcs)

print("\n=== Server Routes ===")
if os.path.exists(server_path):
    with open(server_path, "r", encoding="utf-8", errors="ignore") as f:
        srv = f.read()
    routes = re.findall(r'@app\.(?:get|post|put|delete)\(["\']([^"\']+)["\']', srv)
    print("API Routes:", routes)
