import os
import re
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
PROJECT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

# Load DBs
def load_db(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mapping = {}
    for item in data:
        prompt = item.get('prompt', '')
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            idx = int(m.group(1))
            refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
            if refs:
                mapping[idx] = refs
    return mapping

batch1 = load_db("rooms_turboflow_batch1.json")
batch2 = load_db("rooms_turboflow_batch2.json")

# Sku refs
texas_refs = ["1397_bäddsoffa-lucca-grå-1-26U-wonder.png", "0108_bäddsoffa-texas-ljusgrå-1-26U-wonder.webp", "1397.png", "1397", "0108"]

def is_texas(refs):
    for r in refs:
        r_clean = r.lower().replace("", "å").replace("", "ä").replace("", "ö")
        if "1397" in r_clean or "0108" in r_clean or "texas-ljus" in r_clean or "lucca-gr" in r_clean:
            return True
    return False

# Find indices
b1_texas_indices = [idx for idx, refs in batch1.items() if is_texas(refs)]
b2_texas_indices = [idx for idx, refs in batch2.items() if is_texas(refs)]

print(f"Batch 1 Texas Indices: {b1_texas_indices}")
print(f"Batch 2 Texas Indices: {b2_texas_indices}")

# Load ground truth
gt_path = os.path.join(WORKSPACE_DIR, "scratch", "gemini_ground_truth.json")
with open(gt_path, 'r', encoding='utf-8') as f:
    ground_truth = json.load(f)

# Scan OneDrive
found_files = []
b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

for src_dir in [os.path.join(PROJECT_DIR, "första omgången fyrkantiga"), PROJECT_DIR]:
    if not os.path.exists(src_dir):
        continue
    for f in os.listdir(src_dir):
        if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
        m = re.match(r"^(\d+)", f)
        if m:
            prefix = int(m.group(1))
            m_style = re.search(r"-styl(?:e)?-(\d+)([a-z])?$", os.path.splitext(f)[0], re.IGNORECASE)
            suffix = int(m_style.group(1)) if m_style else None
            diff = prefix - suffix if suffix is not None else 0
            
            if diff == 0:
                db_name = "batch1"
                is_match = (prefix in b1_texas_indices)
            elif diff in b2_diffs and prefix <= 692:
                db_name = "batch2"
                is_match = (prefix in b2_texas_indices)
            else:
                db_name = "full_catalog"
                is_match = False
                
            if is_match:
                decision = ground_truth.get(f, "NOT_EVALUATED")
                found_files.append({
                    "filename": f,
                    "db": db_name,
                    "index": prefix,
                    "diff": diff,
                    "decision": decision
                })

print(f"\nFound {len(found_files)} files mapping to Texas Sofa:")
for item in found_files:
    print(f"File: {item['filename']} | DB: {item['db']} | Index: {item['index']} | Decision: {item['decision']}")
