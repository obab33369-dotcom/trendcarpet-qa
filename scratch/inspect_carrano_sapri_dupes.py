import os
import hashlib
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from test_fixed_resolver import fixed_resolve_anchor

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
target_hash = "8af38ff3fd008f73513062dd90e7b9d5"

files_found = []
for root, dirs, files in os.walk(WORKSPACE_DIR):
    for f in files:
        if not f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            continue
        path = os.path.join(root, f)
        try:
            with open(path, 'rb') as fh:
                md5 = hashlib.md5(fh.read()).hexdigest()
            if md5 == target_hash:
                files_found.append(path)
        except Exception:
            pass

print(f"=== FILES WITH HASH {target_hash} ===")
for p in files_found:
    fn = os.path.basename(p)
    sku, name = fixed_resolve_anchor(fn)
    print(f"File: {fn}")
    print(f"  Path: {p}")
    print(f"  Resolved SKU: {sku} | Name: {name}")
    print("-" * 50)
