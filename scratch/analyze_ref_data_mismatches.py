import json
import os
import re
import hashlib

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
prompt_db_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'rooms_turboflow_full_catalog.json')
orig_dir = os.path.join(WORKSPACE_DIR, "reforma-original-images")
topaz_dir = os.path.join(PICTURES_DIR, "TEST TOPAZ")

# Load DB
with open(prompt_db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

# Build MD5 database of original images
def get_md5(path):
    if not os.path.exists(path):
        return None
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

orig_hashes = {}
if os.path.exists(orig_dir):
    for f in os.listdir(orig_dir):
        path = os.path.join(orig_dir, f)
        if os.path.isfile(path) and f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
            orig_hashes[get_md5(path)] = f

# We want to import resolve_anchor
import sys
sys.path.append(os.path.join(WORKSPACE_DIR, 'scratch'))
from execute_full_catalog_sorting import resolve_anchor

# Gather all unique carpet references in DB
carpet_refs = set()
for item in db:
    refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
    for ref in refs:
        ref_lower = ref.lower()
        if "matta" in ref_lower or "rug" in ref_lower or "rg01" in ref_lower or "jute" in ref_lower or "pet" in ref_lower:
            carpet_refs.add(ref)

# Trace each reference
print(f"Tracing {len(carpet_refs)} unique carpet references found in the database:\n")
print(f"{'DB Ref Name':<45} | {'Resolved SKU':<12} | {'Resolved Name':<30} | {'Actual Image File':<20}")
print("-" * 125)

for ref in sorted(list(carpet_refs)):
    # 1. Resolve SKU and name
    sku, name = resolve_anchor(ref)
    
    # 2. Find file on OneDrive and get MD5
    ref_path = None
    # Search in TEST TOPAZ first (as it contains all the Topaz-processed ref files)
    topaz_path = os.path.join(topaz_dir, ref)
    if os.path.exists(topaz_path):
        ref_path = topaz_path
    else:
        # Search other directories
        for root, dirs, files in os.walk(PICTURES_DIR):
            if ref in files:
                ref_path = os.path.join(root, ref)
                break
                
    actual_img = "NOT FOUND ON DISK"
    if ref_path:
        md5 = get_md5(ref_path)
        actual_img = orig_hashes.get(md5, "NO MATCHING ORIG IMAGE")
        
    print(f"{ref:<45} | {str(sku):<12} | {str(name)[:30]:<30} | {actual_img:<20}")
