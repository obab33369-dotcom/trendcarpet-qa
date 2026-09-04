import os
import hashlib
import collections

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
orig_dir = os.path.join(WORKSPACE_DIR, "reforma-original-images")

# Group original files by MD5
orig_md5_groups = collections.defaultdict(list)

if os.path.exists(orig_dir):
    for f in os.listdir(orig_dir):
        if not f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            continue
        path = os.path.join(orig_dir, f)
        try:
            with open(path, 'rb') as fh:
                md5 = hashlib.md5(fh.read()).hexdigest()
            orig_md5_groups[md5].append({
                "filename": f,
                "path": path,
                "size": os.path.getsize(path)
            })
        except Exception:
            pass

# Find duplicate images in original references that represent different SKUs
sku_dupes = 0
print("=== DUPLICATE ORIGINAL REFERENCES ===")
for md5, instances in orig_md5_groups.items():
    if len(instances) < 2:
        continue
    
    # Check if they are carpet SKUs (RG01, rug, matta)
    is_carpet = False
    for inst in instances:
        name = inst["filename"].lower()
        if "matta" in name or "rug" in name or name.startswith("rg01"):
            is_carpet = True
            break
            
    if not is_carpet:
        continue
        
    sku_dupes += 1
    print(f"\nHash: {md5} (Size: {instances[0]['size']} bytes)")
    print("These distinct product files are identical:")
    for inst in instances:
        print(f"  - {inst['filename']}")

print(f"\nTotal duplicate groups in original references: {sku_dupes}")
