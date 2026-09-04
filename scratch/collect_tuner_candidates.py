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

test_products = {
    "102576": {
        "name": "3-sitssoffa Milly - Beige (102576)",
        "refs": ["1786_3-sitssoffa-milly-beige-1-26U-wonder.png"]
    },
    "MLM-502580-lightgrey": {
        "name": "Baddsoffa Texas Ljusgra (MLM-502580-lightgrey)",
        "refs": ["1397_bäddsoffa-lucca-grå-1-26U-wonder.png", "0108_bäddsoffa-texas-ljusgrå-1-26U-wonder.webp"]
    },
    "WS-18001": {
        "name": "Matsalsstol Industri Järn (WS-18001)",
        "refs": ["1346_matsalsstol-industri-järn-1-26U-wonder.png"]
    },
    "DETROITST01": {
        "name": "Sangbord Detroit Valnot Svart (DETROITST01)",
        "refs": ["2093_sängbord-amster-ek-svart-1-26U-wonder.png"]
    }
}

def normalize_ref(r):
    r = re.sub(r'^\d+_', '', r)
    r = re.sub(r'-1-26u-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-1$', '', r, flags=re.IGNORECASE)
    r = os.path.splitext(r)[0]
    return r.lower().replace("-", "").replace("_", "").replace(" ", "")

# Parse DBs into indexed structures
db_prompts = {
    "batch1": {},
    "batch2": {},
    "full_catalog": {}
}

def parse_db(db, name):
    for item in db:
        prompt = item.get("prompt", "")
        img_refs = item.get("image_references", "")
        refs = [r.strip() for r in img_refs.split(";") if r.strip()]
        m = re.match(r"^(\d+)\s*-", prompt)
        if m:
            idx = int(m.group(1))
            db_prompts[name][idx] = {
                "refs": refs,
                "prompt": prompt
            }

parse_db(batch1, "batch1")
parse_db(batch2, "batch2")
parse_db(full_catalog, "full_catalog")

# Load OneDrive candidate files
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

found_files = []
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
            found_files.append({
                "path": os.path.join(src_dir, f),
                "filename": f,
                "prefix": prefix,
                "suffix": suffix
            })

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

b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

def run_variant_b(sku):
    info = test_products[sku]
    target_refs = info["refs"]
    copied = set()
    for item in found_files:
        fn = item["filename"]
        prefix = item["prefix"]
        suffix = item["suffix"]
        
        diff = prefix - suffix if suffix is not None else 0
        if diff == 0:
            db_name = "batch1"
        elif diff in b2_diffs and prefix <= 692:
            db_name = "batch2"
        else:
            db_name = "full_catalog"
            
        prompt_data = db_prompts[db_name].get(prefix)
        if prompt_data:
            has_match, _ = refs_match(prompt_data["refs"], target_refs)
            if has_match:
                copied.add(item["path"])
    return copied

def run_variant_a(sku):
    info = test_products[sku]
    target_refs = info["refs"]
    copied = set()
    for item in found_files:
        fn = item["filename"]
        prefix = item["prefix"]
        suffix = item["suffix"]
        path = item["path"]
        
        if "första omgången fyrkantiga" not in path:
            import datetime
            mtime = os.path.getmtime(path)
            dt = datetime.datetime.fromtimestamp(mtime)
            if dt < datetime.datetime(2026, 6, 8):
                continue
                
        diff = prefix - suffix if suffix is not None else 0
        if diff == 0:
            anchor_data = db_prompts["batch1"].get(prefix)
        elif diff in b2_diffs and prefix <= 692:
            anchor_data = db_prompts["batch2"].get(prefix)
        else:
            anchor_data = db_prompts["full_catalog"].get(prefix)
            
        if not anchor_data:
            anchor_data = db_prompts["full_catalog"].get(prefix) or db_prompts["batch1"].get(prefix)
            
        if anchor_data:
            has_match, _ = refs_match(anchor_data["refs"], target_refs)
            if has_match:
                copied.add(path)
                continue
                
        if suffix is not None and suffix != prefix:
            if diff == 0:
                anchor_data = db_prompts["batch1"].get(suffix)
            elif diff in b2_diffs and prefix <= 692:
                anchor_data = db_prompts["batch2"].get(suffix)
            else:
                anchor_data = db_prompts["full_catalog"].get(suffix)
                
            if anchor_data:
                has_match, _ = refs_match(anchor_data["refs"], target_refs)
                if has_match:
                    copied.add(path)
    return copied

# Collect Union
union_candidates = {sku: set() for sku in test_products}
for sku in test_products:
    set_a = run_variant_a(sku)
    set_b = run_variant_b(sku)
    union_candidates[sku] = set_a.union(set_b)
    print(f"Product {sku}:")
    print(f"  Variant A copies: {len(set_a)}")
    print(f"  Variant B copies: {len(set_b)}")
    print(f"  Union copies:     {len(union_candidates[sku])}")

total_union = sum(len(s) for s in union_candidates.values())
print(f"\nTotal unique files to verify across all 4 products: {total_union}")
