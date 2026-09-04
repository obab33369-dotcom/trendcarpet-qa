import os
import json
import re

PROJECT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

# 1. Load Databases
def load_db(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        return []
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

batch1 = load_db("rooms_turboflow_batch1.json")
batch2 = load_db("rooms_turboflow_batch2.json")

# Build target index sets
target_indices = {
    "batch1": set(),
    "batch2": set()
}

# Ref names
target_refs = ["1397_bäddsoffa-lucca-grå-1-26U-wonder.png", "0108_bäddsoffa-texas-ljusgrå-1-26U-wonder.webp"]

def normalize_ref(r):
    r = re.sub(r'^\d+_', '', r)
    r = re.sub(r'-1-26u-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-1$', '', r, flags=re.IGNORECASE)
    r = os.path.splitext(r)[0]
    return r.lower().replace("-", "").replace("_", "").replace(" ", "")

norm_targets = [normalize_ref(r) for r in target_refs]

def refs_match(db_refs, target_refs):
    for db_ref in db_refs:
        db_base = os.path.splitext(db_ref)[0]
        if db_base.isdigit():
            db_num = int(db_base)
            for t_ref in target_refs:
                m = re.match(r"^(\d+)", t_ref)
                if m and int(m.group(1)) == db_num:
                    return True, (db_ref == db_refs[0])
        else:
            norm_db = normalize_ref(db_ref)
            for t_ref in target_refs:
                if normalize_ref(t_ref) == norm_db:
                    return True, (db_ref == db_refs[0])
    return False, False

for item in batch1:
    prompt = item.get("prompt", "")
    refs = [r.strip() for r in item.get("image_references", "").split(";") if r.strip()]
    has_match, is_pri = refs_match(refs, target_refs)
    if has_match and is_pri:
        m = re.match(r"^(\d+)", prompt)
        if m:
            target_indices["batch1"].add(int(m.group(1)))

for item in batch2:
    prompt = item.get("prompt", "")
    refs = [r.strip() for r in item.get("image_references", "").split(";") if r.strip()]
    has_match, is_pri = refs_match(refs, target_refs)
    if has_match and is_pri:
        m = re.match(r"^(\d+)", prompt)
        if m:
            target_indices["batch2"].add(int(m.group(1)))

print("Expected Primary Indices:")
print("  Batch 1:", sorted(list(target_indices["batch1"])))
print("  Batch 2:", sorted(list(target_indices["batch2"])))

# Scan OneDrive pictures
render_sources = [
    os.path.join(PROJECT_DIR, "första omgången fyrkantiga"),
    PROJECT_DIR
]

def parse_filename_numbers(filename):
    base, _ = os.path.splitext(filename)
    base = re.sub(r'\s*\(\d+\)$', '', base)
    prefix = None
    m_lead = re.match(r'^(\d+)', base)
    if m_lead:
        prefix = int(m_lead.group(1))
    suffix = None
    m_style = re.search(r'-styl(?:e)?-(\d+)([a-z])?$', base, re.IGNORECASE)
    if m_style:
        suffix = int(m_style.group(1))
    return prefix, suffix

found_by_prefix = {}
b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

for src_dir in render_sources:
    if not os.path.exists(src_dir):
        continue
    for f in os.listdir(src_dir):
        if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
        if "architectural" not in f.lower() and "digest" not in f.lower() and "style" not in f.lower():
            continue
        prefix, suffix = parse_filename_numbers(f)
        if prefix is not None:
            found_by_prefix.setdefault(prefix, []).append((f, suffix))

print("\nExistence check for expected Batch 1 indices:")
b1_exist = 0
for idx in sorted(list(target_indices["batch1"])):
    files = found_by_prefix.get(idx, [])
    # Filter for batch1 (diff == 0)
    b1_files = []
    for fn, s in files:
        diff = idx - s if s is not None else None
        if diff == 0:
            b1_files.append(fn)
    if b1_files:
        print(f"  Index {idx}: Found {b1_files}")
        b1_exist += len(b1_files)
    else:
        # Check if index exists with any diff
        print(f"  Index {idx}: NOT found (All files with prefix: {[f[0] for f in files]})")

print(f"Total Batch 1 renders found: {b1_exist}")

print("\nExistence check for expected Batch 2 indices:")
b2_exist = 0
for idx in sorted(list(target_indices["batch2"])):
    files = found_by_prefix.get(idx, [])
    # Filter for batch2 (diff in b2_diffs and idx <= 692)
    b2_files = []
    for fn, s in files:
        diff = idx - s if s is not None else None
        if diff in b2_diffs and idx <= 692:
            b2_files.append(fn)
    if b2_files:
        print(f"  Index {idx}: Found {b2_files}")
        b2_exist += len(b2_files)
    else:
        print(f"  Index {idx}: NOT found (All files with prefix: {[f[0] for f in files]})")

print(f"Total Batch 2 renders found: {b2_exist}")
