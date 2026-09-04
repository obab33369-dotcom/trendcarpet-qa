import os
import hashlib
import collections
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
folders_to_scan = [
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch1_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch2_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch3_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "batch4_images"),
    os.path.join(WORKSPACE_DIR, "reforma-turboflow", "new_rugs"),
    os.path.join(WORKSPACE_DIR, "reforma-original-images")
]

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

def get_rug_family(filename):
    name = filename.lower()
    # Extract rug model family name, e.g. "seronis", "aravelle", "orlisse", "sorvento", "velenna", "ventaro", etc.
    # Look for "matta-FAMILYNAME" or just "matta FAMILYNAME" or SKU prefix
    m = re.search(r'matta-([a-z]+)', name)
    if m:
        return m.group(1)
    
    # Check if name contains any known family names
    families = ["seronis", "aravelle", "arabelle", "sorvento", "orlisse", "velenna", "ventaro", "taliana", "tireno", "valora", "savelle", "janjira", "rivetta", "seleren", "savena"]
    for fam in families:
        if fam in name:
            return fam
            
    # Try SKU based lookup
    sku_match = re.search(r'(rg\d+|rug\d+)', name)
    if sku_match:
        return sku_match.group(1)
        
    return name

print("=== CROSS-MODEL CARPET DUPES ===")
cross_model_count = 0

for md5, instances in md5_groups.items():
    if len(instances) < 2:
        continue
        
    # Get distinct filenames
    unique_files = list(set(inst["filename"] for inst in instances))
    if len(unique_files) < 2:
        continue
        
    # Get distinct rug families for these filenames
    families = set()
    for uf in unique_files:
        fam = get_rug_family(uf)
        families.add(fam)
        
    # If we have more than 1 rug family, it's a cross-model mismatch!
    if len(families) > 1:
        cross_model_count += 1
        print(f"\nHash: {md5}")
        print(f"  Rug families involved: {list(families)}")
        print("  Files:")
        for uf in unique_files:
            print(f"    - {uf}")

print(f"\nFound {cross_model_count} cross-model carpet duplicate groups.")
