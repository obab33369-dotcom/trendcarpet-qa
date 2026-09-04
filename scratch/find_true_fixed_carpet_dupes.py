import os
import hashlib
import collections
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from test_fixed_resolver import fixed_resolve_anchor

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
folders_to_scan = [
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch1_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch2_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch3_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch4_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "new_rugs"),
    os.path.join(WORKSPACE_DIR, "reforma-original-images")
]

# Group by MD5
md5_groups = collections.defaultdict(list)

for folder in folders_to_scan:
    if not os.path.exists(folder):
        continue
    for root, dirs, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'rb') as fh:
                    md5 = hashlib.md5(fh.read()).hexdigest()
                md5_groups[md5].append({
                    "filename": f,
                    "path": path
                })
            except Exception:
                pass

print(f"Scanned {len(md5_groups)} groups. Checking for different carpet SKUs with identical images...")

true_rug_mismatches = 0

for md5, instances in md5_groups.items():
    if len(instances) < 2:
        continue
        
    unique_filenames = list(set(inst["filename"] for inst in instances))
    if len(unique_filenames) < 2:
        continue
        
    sku_to_files = collections.defaultdict(list)
    for uf in unique_filenames:
        sku, name = fixed_resolve_anchor(uf)
        if sku:
            sku_to_files[sku].append((uf, name))
            
    if len(sku_to_files) > 1:
        # Check if it's a carpet
        is_carpet = False
        for sku, files_info in sku_to_files.items():
            if sku.startswith("RG01") or any("matta" in f[0].lower() or "rug" in f[0].lower() for f in files_info):
                is_carpet = True
                break
                
        if not is_carpet:
            continue
            
        sku_list = list(sku_to_files.keys())
        names_list = []
        for sku in sku_list:
            for f, name in sku_to_files[sku]:
                names_list.append(name.split('-')[0].replace("Matta", "").strip().lower())
        
        unique_names = set(names_list)
        if len(unique_names) > 1:
            true_rug_mismatches += 1
            print(f"\n[MISMATCH DETECTED] Hash: {md5}")
            print("Identical image file used for different carpet products:")
            for sku, files_info in sku_to_files.items():
                print(f"  * SKU: {sku}")
                for uf, name in files_info:
                    print(f"    - File: {uf}")
                    print(f"      Resolved Product Name: {name}")
            print("-" * 50)

print(f"\nFound {true_rug_mismatches} true cross-product design mismatches.")
