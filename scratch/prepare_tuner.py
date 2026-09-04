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
full_catalog = load_db("rooms_turboflow_full_catalog.json")

# 2. Test Products definitions
test_products = {
    "102576": {
        "name": "3-sitssoffa Milly - Beige (102576)",
        "refs": ["1786_3-sitssoffa-milly-beige-1-26U-wonder.png"]
    },
    "MLM-502580-lightgrey": {
        "name": "Baddsoffa Texas Ljusgra (MLM-502580-lightgrey)",
        "refs": ["1397_bäddsoffa-lucca-grå-1-26U-wonder.png", "0108_bäddsoffa-texas-ljusgrå-1-26U-wonder.webp"]
    },
    "H000021092": {
        "name": "Sidobord Moliden Natur (H000021092)",
        "refs": [
            "2100_sidobord-dala-natur-1-26U-wonder.png",
            "2143_sidobord-cardoba-natur-1-26U-wonder.png",
            "1188_sidobord-moliden-natur-1-26U-wonder.webp"
        ]
    }
}

def normalize_ref(r):
    r = re.sub(r'^\d+_', '', r)
    r = re.sub(r'-1-26u-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-1$', '', r, flags=re.IGNORECASE)
    r = os.path.splitext(r)[0]
    return r.lower().replace("-", "").replace("_", "").replace(" ", "")

# Normalize refs for test products
for sku, info in test_products.items():
    info["norm_refs"] = [normalize_ref(r) for r in info["refs"]]

def refs_match(db_refs, target_refs):
    for db_ref in db_refs:
        db_base = os.path.splitext(db_ref)[0]
        if db_base.isdigit():
            db_num = int(db_base)
            for t_ref in target_refs:
                m = re.match(r"^(\d+)", t_ref)
                if m and int(m.group(1)) == db_num:
                    return True
        else:
            norm_db = normalize_ref(db_ref)
            for t_ref in target_refs:
                if normalize_ref(t_ref) == norm_db:
                    return True
    return False

# Find all prompt indices where these products are mentioned in ANY database
expected_indices = {}
for sku in test_products:
    expected_indices[sku] = {
        "batch1": set(),
        "batch2": set(),
        "full_catalog": set()
    }

def collect_indices(db, db_name):
    for item in db:
        prompt = item.get("prompt", "")
        img_refs = item.get("image_references", "")
        refs = [r.strip() for r in img_refs.split(";") if r.strip()]
        m = re.match(r"^(\d+)\s*-", prompt)
        if m:
            idx = int(m.group(1))
            for sku, info in test_products.items():
                if refs_match(refs, info["refs"]):
                    expected_indices[sku][db_name].add(idx)

collect_indices(batch1, "batch1")
collect_indices(batch2, "batch2")
collect_indices(full_catalog, "full_catalog")

for sku, info in test_products.items():
    print(f"\nProduct: {info['name']}")
    print(f"  Batch 1 Expected Indices: {sorted(list(expected_indices[sku]['batch1']))}")
    print(f"  Batch 2 Expected Indices: {sorted(list(expected_indices[sku]['batch2']))}")
    print(f"  Full Catalog Expected Indices: {sorted(list(expected_indices[sku]['full_catalog']))}")

# Scan OneDrive files
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

all_files = []
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
            all_files.append({
                "path": os.path.join(src_dir, f),
                "filename": f,
                "prefix": prefix,
                "suffix": suffix
            })

print(f"\nTotal files in source folders: {len(all_files)}")

# Filter candidate files for our test products (any file where prefix or suffix matches an expected index)
candidates = {sku: [] for sku in test_products}
all_unique_candidates = set()

for item in all_files:
    prefix = item["prefix"]
    suffix = item["suffix"]
    
    for sku in test_products:
        # Check if prefix or suffix matches any expected index for this SKU
        is_candidate = False
        for db_name in ["batch1", "batch2", "full_catalog"]:
            indices = expected_indices[sku][db_name]
            if prefix in indices or (suffix is not None and suffix in indices):
                is_candidate = True
                break
        if is_candidate:
            candidates[sku].append(item)
            all_unique_candidates.add(item["path"])

for sku, info in test_products.items():
    print(f"Product {sku}: found {len(candidates[sku])} candidate files.")
print(f"Total unique candidate files across all 3 test products: {len(all_unique_candidates)}")
