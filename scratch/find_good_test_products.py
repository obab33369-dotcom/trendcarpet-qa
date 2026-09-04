import os
import json
import re

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
full_catalog = load_db("rooms_turboflow_full_catalog.json")

# Load sku_map
sku_map_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "sku_map.json")
with open(sku_map_path, 'r', encoding='latin-1') as f:
    sku_map = json.load(f)

# Count total prompt occurrences for each SKU in sku_map
sku_counts = {}

def normalize_ref(r):
    r = re.sub(r'^\d+_', '', r)
    r = re.sub(r'-1-26u-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-1$', '', r, flags=re.IGNORECASE)
    r = os.path.splitext(r)[0]
    return r.lower().replace("-", "").replace("_", "").replace(" ", "")

def refs_match(db_refs, target_ref):
    for db_ref in db_refs:
        db_base = os.path.splitext(db_ref)[0]
        if db_base.isdigit():
            db_num = int(db_base)
            m = re.match(r"^(\d+)", target_ref)
            if m and int(m.group(1)) == db_num:
                return True
        else:
            if normalize_ref(db_ref) == normalize_ref(target_ref):
                return True
    return False

# Initialize counts
for k, v in sku_map.items():
    sku = v.get("sku")
    if sku:
        sku_counts[sku] = {
            "name": v.get("slug"),
            "ref_key": k,
            "count": 0
        }

for db in [batch1, batch2, full_catalog]:
    for item in db:
        refs = [r.strip() for r in item.get("image_references", "").split(";") if r.strip()]
        for sku, info in sku_counts.items():
            if refs_match(refs, info["ref_key"]):
                info["count"] += 1

# Sort products by prompt occurrences
sorted_products = sorted(sku_counts.items(), key=lambda x: x[1]["count"])
print("Products with low non-zero occurrences (1 to 20 occurrences):")
low_occ = [p for p in sorted_products if 1 <= p[1]["count"] <= 20]
for sku, info in low_occ[:15]:
    print(f"  SKU: {sku} | Slug: {info['name']} | Count: {info['count']} | Ref: {info['ref_key']}")
