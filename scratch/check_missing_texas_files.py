import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

expected_indices = [
    33, 34, 99, 100, 165, 166, 229, 230, 249, 250, 
    331, 332, 343, 344, 637, 638, 761, 762, 791, 792, 
    891, 892, 935, 936, 963, 964, 1241, 1242, 1369, 1370, 
    1437, 1438, 1539, 1540, 1551, 1552, 1845, 1846, 1973, 1974, 
    2041, 2042, 2061, 2062, 2099, 2100, 2145, 2146
]

dirs_to_scan = [
    ONEDRIVE_DIR,
    os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
]

print("=== Scanning OneDrive for Texas Sofa Index prefixes ===")
found_by_index = {}
for d in dirs_to_scan:
    if not os.path.exists(d):
        continue
    for f in os.listdir(d):
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
                    "dir": os.path.basename(d)
                })

for idx in sorted(expected_indices):
    if idx in found_by_index:
        print(f"Index {idx}: Found {len(found_by_index[idx])} files:")
        for item in found_by_index[idx]:
            print(f"  - {item['filename']} (in folder '{item['dir']}')")
    else:
        print(f"Index {idx}: NOT found on disk!")
