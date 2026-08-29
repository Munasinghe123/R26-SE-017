import os
import shutil

src_root = "E:/01 R/LLD backend only/Backend"
dst_root = "d:/01 R/Research Antigravity/01 R/services/agent3-lld"

for root, dirs, files in os.walk(src_root):
    if "__pycache__" in root:
        continue
    rel = os.path.relpath(root, src_root)
    target_dir = os.path.join(dst_root, rel)
    os.makedirs(target_dir, exist_ok=True)
    
    for f in files:
        if f.endswith(".py"):
            s_file = os.path.join(root, f)
            d_file = os.path.join(target_dir, f)
            shutil.copy2(s_file, d_file)
            print(f"Copied: {os.path.join(rel, f)}")

print("LLD Backend restoration completed!")
