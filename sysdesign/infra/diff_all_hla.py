import os

orig_dir = "E:/01 R/hla_agent"
migr_dir = "d:/01 R/Research Antigravity/01 R/services/agent2-hld"

for root, dirs, files in os.walk(orig_dir):
    if "venv" in root or "__pycache__" in root or ".git" in root:
        continue
    rel = os.path.relpath(root, orig_dir)
    target_root = os.path.join(migr_dir, rel)
    
    for f in files:
        orig_file = os.path.join(root, f)
        migr_file = os.path.join(target_root, f)
        
        if not os.path.exists(migr_file):
            print("Missing file:", os.path.join(rel, f))
        else:
            s_orig = os.path.getsize(orig_file)
            s_migr = os.path.getsize(migr_file)
            if abs(s_orig - s_migr) > 100 and f.endswith(".py"):
                print(f"Size mismatch in {os.path.join(rel, f)}: Orig={s_orig}b vs Migr={s_migr}b")
