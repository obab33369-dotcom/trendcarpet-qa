import os
import hashlib
import collections

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# Target folders to scan for reference images
folders_to_scan = [
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch1_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch2_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch3_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch4_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "new_rugs"),
    os.path.join(WORKSPACE_DIR, "reforma-original-images")
]

# Scan files and calculate MD5
md5_groups = collections.defaultdict(list)

print("Scanning folders for reference images...")
for folder in folders_to_scan:
    if not os.path.exists(folder):
        continue
    for root, dirs, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                continue
            path = os.path.join(root, f)
            try:
                size = os.path.getsize(path)
                # Read first and last megabyte to optimize hash calculation speed
                with open(path, 'rb') as fh:
                    data = fh.read()
                    md5 = hashlib.md5(data).hexdigest()
                md5_groups[md5].append({
                    "filename": f,
                    "path": path,
                    "size": size
                })
            except Exception as e:
                pass

print(f"Scanned {len(md5_groups)} unique image hashes.")

# Find duplicate images that represent different rugs
duplicate_rugs_found = 0

print("\n=== DUPLICATE IMAGE GROUPS FOR CARPETS ===")
for md5, instances in md5_groups.items():
    if len(instances) < 2:
        continue
        
    # Check if any instance in this group looks like a rug
    is_rug_group = False
    for inst in instances:
        name = inst["filename"].lower()
        if "matta" in name or "rug" in name or name.startswith("rg01"):
            is_rug_group = True
            break
            
    if not is_rug_group:
        continue
        
    # Filter out files that have the exact same filename (they are just copied to different folders)
    # We are interested in cases where the SAME image is saved under DIFFERENT names/SKUs
    unique_names = set(inst["filename"] for inst in instances)
    if len(unique_names) < 2:
        continue
        
    duplicate_rugs_found += 1
    print(f"\nHash: {md5} (Size: {instances[0]['size']} bytes)")
    print("This identical image was found under these different names:")
    for inst in instances:
        # Show relative path from workspace for clarity
        rel_path = os.path.relpath(inst["path"], WORKSPACE_DIR)
        print(f"  - Name: {inst['filename']}")
        print(f"    Path: {rel_path}")

print(f"\nDone! Found {duplicate_rugs_found} distinct image files that were reused under different carpet names.")
