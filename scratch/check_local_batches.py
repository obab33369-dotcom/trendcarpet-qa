import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

expected_indices = [
    33, 34, 99, 100, 165, 166, 229, 230, 249, 250, 
    331, 332, 343, 344, 637, 638, 761, 762, 791, 792, 
    891, 892, 935, 936, 963, 964, 1241, 1242, 1369, 1370, 
    1437, 1438, 1539, 1540, 1551, 1552, 1845, 1846, 1973, 1974, 
    2041, 2042, 2061, 2062, 2099, 2100, 2145, 2146
]

local_dirs = [
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch1_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch2_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch3_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch4_images")
]

print("=== Scanning Local Batches for Texas Sofa Index prefixes ===")
found_by_index = {}
for d in local_dirs:
    if not os.path.exists(d):
        continue
    for root, dirs, files in os.walk(d):
        for f in files:
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            m = re.match(r"^(\d+)", f)
            if m:
                prefix = int(m.group(1))
                if prefix in expected_indices:
                    if prefix not in found_by_index:
                        found_by_index[prefix] = []
                    found_by_index[prefix].append({
                        "filename": f,
                        "path": os.path.join(root, f)
                    })

for idx in sorted(expected_indices):
    if idx in found_by_index:
        print(f"Index {idx}: Found {len(found_by_index[idx])} files locally:")
        for item in found_by_index[idx]:
            # Print relative path from WORKSPACE_DIR
            rel = os.path.relpath(item["path"], WORKSPACE_DIR)
            print(f"  - {rel}")
    else:
        print(f"Index {idx}: NOT found locally!")
