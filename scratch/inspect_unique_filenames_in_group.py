import sys
import os
import hashlib

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from test_fixed_resolver import fixed_resolve_anchor

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
target_hash = "8af38ff3fd008f73513062dd90e7b9d5"

folders_to_scan = [
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch1_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch2_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch3_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch4_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "new_rugs"),
    os.path.join(WORKSPACE_DIR, "reforma-original-images")
]

for folder in folders_to_scan:
    if not os.path.exists(folder):
        continue
    for root, dirs, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                continue
            p = os.path.join(root, f)
            try:
                with open(p, 'rb') as fh:
                    md5 = hashlib.md5(fh.read()).hexdigest()
                if md5 == target_hash:
                    sku, name = fixed_resolve_anchor(f)
                    print(f"File: {f} | Path: {p} | Resolved to SKU: {sku} | Name: {name}")
            except Exception:
                pass
