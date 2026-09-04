import os
import csv
import json
import glob
import re
import sys

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

project_dir = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
onedrive_pictures_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

# 1. Read all required images
required_images = set()
for csv_file in glob.glob(os.path.join(project_dir, "turboflow_tracking_log_full_catalog_batch*.csv")):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            refs = row.get('References Utilized', '')
            for ref in refs.split(';'):
                ref = ref.strip()
                if ref: required_images.add(ref)

# 2. Re-run local mapping to find which are currently missing
search_dirs = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ",
    r"C:\Users\AndronikLindgren\reforma_automation\reforma_arkiv",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\test_furniture",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\new_rugs",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\test_rugs"
]
if os.path.exists(onedrive_pictures_dir):
    for entry in os.listdir(onedrive_pictures_dir):
        if entry.lower().startswith("turboflow_batch"):
            full_path = os.path.join(onedrive_pictures_dir, entry)
            if os.path.isdir(full_path):
                search_dirs.append(full_path)

local_index = {}
for sd in search_dirs:
    if os.path.exists(sd):
        for r, d, files in os.walk(sd):
            if "batch" in r.lower() and "_images" in r.lower(): continue
            for f in files:
                if f.endswith(('.png', '.webp', '.jpg', '.jpeg')):
                    local_index[f.lower()] = os.path.join(r, f)

def normalize(s):
    s = s.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e'}
    for c, r in repl.items():
        if c: s = s.replace(c, r)
    s = re.sub(r'^\d+[_-]', '', s)
    s = re.sub(r'\.(jpg|jpeg|png|webp)$', '', s)
    s = re.sub(r'[^a-z0-9]', '', s)
    s = re.sub(r'(26uwonder|wonder|26u)$', '', s)
    return s

local_norm_map = {}
for k, v in local_index.items():
    local_norm_map[normalize(k)] = v

missing_norms = {}
for img in required_images:
    match = local_index.get(img.lower())
    if not match:
        norm = normalize(img)
        match = local_norm_map.get(norm)
        if not match:
            # Check starts-with prefix
            for knorm, kv in local_norm_map.items():
                if knorm.startswith(norm) or norm.startswith(knorm):
                    match = kv
                    break
    if not match:
        missing_norms[normalize(img)] = img

print(f"Total missing: {len(missing_norms)}")

# 3. Scan the rest of OneDrive pictures folder, avoiding large known done folders to be super fast
found_matches = {}
if os.path.exists(onedrive_pictures_dir) and missing_norms:
    print("Scanning OneDrive pictures...")
    for root, dirs, files in os.walk(onedrive_pictures_dir):
        # Skip done folders and local batch folders to be fast and secure
        root_lower = root.lower()
        if "turboflow\\sorterat" in root_lower or "batch" in root_lower or "test topaz" in root_lower:
            continue
            
        for f in files:
            if f.endswith(('.png', '.webp', '.jpg', '.jpeg')):
                norm_f = normalize(f)
                
                # Check for direct normalized match
                if norm_f in missing_norms:
                    orig = missing_norms[norm_f]
                    found_matches[orig] = os.path.join(root, f)
                    continue
                    
                # Check for prefix match
                for m_norm, orig in list(missing_norms.items()):
                    if norm_f.startswith(m_norm) or m_norm.startswith(norm_f):
                        found_matches[orig] = os.path.join(root, f)
                        break

print(f"Found {len(found_matches)} matches via full scan!")
for orig, path in found_matches.items():
    try:
        print(f"MATCH: {orig} -> {path}")
    except:
        pass

# Save found matches to a JSON file so build_image_folders.py can read and copy them directly!
with open("found_extra_matches.json", "w", encoding="utf-8") as f:
    json.dump(found_matches, f, ensure_ascii=False, indent=2)
print("Saved extra matches to found_extra_matches.json")
