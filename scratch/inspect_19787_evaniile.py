import os
import hashlib
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from test_fixed_resolver import fixed_resolve_anchor, brand_sku_dict, sku_map

# Find all occurrences of 19787.jpg in folders
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
folders_to_scan = [
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch1_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch2_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch3_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch4_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "new_rugs"),
    os.path.join(WORKSPACE_DIR, "reforma-original-images")
]

print("=== OCCURRENCES OF 19787.JPG ===")
for folder in folders_to_scan:
    if not os.path.exists(folder):
        continue
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f == "19787.jpg":
                p = os.path.join(root, f)
                with open(p, 'rb') as fh:
                    md5 = hashlib.md5(fh.read()).hexdigest()
                sku, name = fixed_resolve_anchor(f)
                print(f"Path: {p}")
                print(f"  MD5: {md5}")
                print(f"  Resolved to SKU: {sku} | Name: {name}")

# Check sku_map.json for 19787
print("\n=== checking sku_map for 19787 ===")
for k, v in sku_map.items():
    if "19787" in k:
        print(f"  {k} -> {v}")

# Check brand_sku_dict for 19787 or RG01-12
print("\n=== checking brand_sku_dict ===")
for k, v in brand_sku_dict.items():
    if v.get('sku') == '19787' or v.get('sku') == 'RG01-12':
        print(f"  {k} -> {v}")
