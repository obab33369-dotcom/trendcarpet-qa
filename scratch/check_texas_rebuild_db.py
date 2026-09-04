import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def normalize_ref(r):
    r = re.sub(r'^\d+_', '', r)
    r = re.sub(r'-1-26u-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-1$', '', r, flags=re.IGNORECASE)
    r = os.path.splitext(r)[0]
    return r.lower().replace('-', '').replace('_', '').replace(' ', '')

# Let's find what the SKU MLM-502580-lightgrey maps to in sku_map.json
sku_map_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "sku_map.json")
with open(sku_map_path, 'r', encoding='latin-1') as f:
    sku_map = json.load(f)

target_sku = "MLM-502580-lightgrey"
ref_filenames = [k for k, v in sku_map.items() if v.get("sku") == target_sku]
print("Reference filenames from sku_map (latin-1):", ref_filenames)

norm_target_refs = [normalize_ref(fn) for fn in ref_filenames]
print("Normalized target refs:", norm_target_refs)

for db_name in ['rooms_turboflow_batch1.json', 'rooms_turboflow_batch2.json', 'rooms_turboflow_full_catalog.json']:
    path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', db_name)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='latin-1') as f:
        data = json.load(f)
    
    matches_found = 0
    for item in data:
        prompt = item.get('prompt', '')
        img_refs = item.get('image_references', '')
        refs = [r.strip() for r in img_refs.split(';') if r.strip()]
        for ref in refs:
            norm_ref = normalize_ref(ref)
            if norm_ref in norm_target_refs:
                m = re.match(r'^(\d+)', prompt)
                prefix = m.group(1) if m else 'None'
                is_primary = (normalize_ref(refs[0]) == norm_ref)
                print(f"{db_name}: Found match at prompt index {prefix}. Primary? {is_primary}. Ref in DB: {ref}")
                matches_found += 1
    if matches_found == 0:
        print(f"{db_name}: No matches found.")
