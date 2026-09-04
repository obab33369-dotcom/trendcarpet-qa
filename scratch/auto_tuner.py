import os
import sys
import re
import json
import time
import base64
import shutil
from io import BytesIO
from PIL import Image
import requests

# Reconfigure stdout/stderr to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

GEMINI_KEY_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
GROUND_TRUTH_PATH = os.path.join(WORKSPACE_DIR, "scratch", "gemini_ground_truth.json")

def load_gemini_key():
    if os.path.exists(GEMINI_KEY_PATH):
        with open(GEMINI_KEY_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == "GEMINI_API_KEY":
                        return v.strip().strip('"').strip("'")
    return None

GEMINI_API_KEY = load_gemini_key()
if not GEMINI_API_KEY:
    print("Error: Gemini API key not found!")
    sys.exit(1)

# Load Databases
def load_db(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        return []
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

batch1 = load_db("rooms_turboflow_batch1.json")
batch2 = load_db("rooms_turboflow_batch2.json")
full_catalog = load_db("rooms_turboflow_full_catalog.json")

# Test Products
test_products = {
    "MLM-502580-lightgrey": {
        "name": "Baddsoffa Texas Ljusgra (MLM-502580-lightgrey)",
        "refs": ["1397_bäddsoffa-lucca-grå-1-26U-wonder.png", "0108_bäddsoffa-texas-ljusgrå-1-26U-wonder.webp"],
        "ref_photo": os.path.join(PROJECT_DIR, "ftp_upload_cropped_full", "artiklar", "MLM-502580-lightgrey.jpg")
    },
    "DETROITST01": {
        "name": "Sangbord Detroit Valnot Svart (DETROITST01)",
        "refs": ["2093_sängbord-amster-ek-svart-1-26U-wonder.png"],
        "ref_photo": os.path.join(PROJECT_DIR, "ftp_upload_cropped_full", "artiklar", "DETROITST01.jpg")
    }
}

def normalize_ref(r):
    r = re.sub(r'^\d+_', '', r)
    r = re.sub(r'-1-26u-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-wonder$', '', r, flags=re.IGNORECASE)
    r = re.sub(r'-1$', '', r, flags=re.IGNORECASE)
    r = os.path.splitext(r)[0]
    return r.lower().replace("-", "").replace("_", "").replace(" ", "")

# Parse DBs
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
                    return True
        else:
            norm_db = normalize_ref(db_ref)
            for t_ref in target_refs:
                if normalize_ref(t_ref) == norm_db:
                    return True
    return False

b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

# Logic variants
def simulate_variant_1(sku):
    info = test_products[sku]
    target_refs = info["refs"]
    copied = set()
    for item in found_files:
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
        if prompt_data and refs_match(prompt_data["refs"], target_refs):
            copied.add(item["filename"])
    return copied

def simulate_variant_2(sku):
    info = test_products[sku]
    target_refs = info["refs"]
    copied = set()
    for item in found_files:
        prefix = item["prefix"]
        matched = False
        for db_name in ["batch1", "batch2", "full_catalog"]:
            prompt_data = db_prompts[db_name].get(prefix)
            if prompt_data and refs_match(prompt_data["refs"], target_refs):
                matched = True
                break
        if matched:
            copied.add(item["filename"])
    return copied

def simulate_variant_3(sku):
    info = test_products[sku]
    target_refs = info["refs"]
    copied = set()
    for item in found_files:
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
        if prompt_data and refs_match(prompt_data["refs"], target_refs):
            copied.add(item["filename"])
            continue
            
        if suffix is not None and suffix != prefix:
            prompt_data = db_prompts[db_name].get(suffix)
            if prompt_data and refs_match(prompt_data["refs"], target_refs):
                copied.add(item["filename"])
    return copied

def simulate_variant_4(sku):
    info = test_products[sku]
    target_refs = info["refs"]
    copied = set()
    for item in found_files:
        prefix = item["prefix"]
        suffix = item["suffix"]
        matched = False
        for db_name in ["batch1", "batch2", "full_catalog"]:
            prompt_data = db_prompts[db_name].get(prefix)
            if prompt_data and refs_match(prompt_data["refs"], target_refs):
                matched = True
                break
            if suffix is not None and suffix != prefix:
                prompt_data = db_prompts[db_name].get(suffix)
                if prompt_data and refs_match(prompt_data["refs"], target_refs):
                    matched = True
                    break
        if matched:
            copied.add(item["filename"])
    return copied

# Collect union of files
union_candidates = {}
all_union_files = {}
for sku, info in test_products.items():
    sets = [
        simulate_variant_1(sku),
        simulate_variant_2(sku),
        simulate_variant_3(sku),
        simulate_variant_4(sku)
    ]
    union_set = set()
    for s in sets:
        union_set = union_set.union(s)
    union_candidates[sku] = union_set
    for fn in union_set:
        for item in found_files:
            if item["filename"] == fn:
                all_union_files[fn] = {
                    "path": item["path"],
                    "sku": sku,
                    "ref_photo": info["ref_photo"]
                }
                break

# Build ground truth map (optimizing Gemini calls)
ground_truth = {}
known_texas_positives = [
    "033-architectural-digest-style-033 (1).png",
    "351-architectural-digest-style-103.png"
]

# Gemini API call helpers
def encode_image(img_path, max_size=600):
    try:
        img = Image.open(img_path)
        img_temp = img.copy()
        img_temp.thumbnail((max_size, max_size))
        buffered = BytesIO()
        img_temp.convert('RGB').save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image {img_path}: {e}")
        return None

def query_gemini_comparison(ref_base64, cand_base64, max_retries=5):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    prompt = """You are a quality control assistant for a furniture retailer.
You are given two images:
1. The FIRST image is the Reference Image showing a specific piece of furniture.
2. The SECOND image is the Interior Scene Image where that exact piece of furniture is supposed to be placed.
Determine if the EXACT piece of furniture shown in the Reference Image is present in the Interior Scene Image.
Respond in this exact JSON format:
{
  "present": true or false,
  "confidence": a float between 0.0 and 1.0,
  "reason": "Swedish explanation"
}
"""
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": ref_base64}},
                    {"inlineData": {"mimeType": "image/jpeg", "data": cand_base64}}
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
    }
    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                return json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'].strip())
            elif res.status_code == 429:
                time.sleep(5 * (attempt + 1))
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)
    return {"present": False, "reason": "API Failure", "confidence": 0.0}

print("\nResolving ground truth for union files...")
# Detroit bedside table candidates copied by strict diff (v3)
detroit_strict_copies = simulate_variant_3("DETROITST01")

for fn, info in all_union_files.items():
    sku = info["sku"]
    if sku == "MLM-502580-lightgrey":
        # We already verified all Texas files
        ground_truth[fn] = (fn in known_texas_positives)
    elif sku == "DETROITST01":
        # If it is not in the strict diff list, it belongs to another database / different product -> DISCARD
        if fn not in detroit_strict_copies:
            ground_truth[fn] = False
        else:
            # Query Gemini
            print(f"Calling Gemini for Detroit file {fn}...", end=" ", flush=True)
            ref_b64 = encode_image(info["ref_photo"])
            cand_b64 = encode_image(info["path"])
            if not ref_b64 or not cand_b64:
                print("Encoding Error")
                ground_truth[fn] = False
                continue
            res = query_gemini_comparison(ref_b64, cand_b64)
            present = res.get("present", False)
            print("KEEP" if present else "DISCARD")
            ground_truth[fn] = present
            time.sleep(1.0)

# Save ground truth to cache
with open(GROUND_TRUTH_PATH, 'w', encoding='utf-8') as f:
    json.dump(ground_truth, f, indent=2, ensure_ascii=False)
print("Saved ground truth cache.")

# Print scores
print("\n" + "=" * 60)
print("             EVALUATING SORTING LOGIC VARIANTS            ")
print("=" * 60)

variants = {
    "Variant 1: Strict Prefix-Only (Strict Diff DB)": simulate_variant_1,
    "Variant 2: Unified Prefix-Only (Search All DBs)": simulate_variant_2,
    "Variant 3: Suffix Fallback (Strict Diff DB)": simulate_variant_3,
    "Variant 4: Unified Suffix Fallback (Search All DBs)": simulate_variant_4
}

gt_positives = {sku: set() for sku in test_products}
for fn, info in all_union_files.items():
    if ground_truth.get(fn, False):
        gt_positives[info["sku"]].add(fn)

print("| Variant Name | Product | Copied | TP (Correct) | FP (Wrong) | FN (Missed) | Precision | Recall | F1 Score |")
print("|---|---|---|---|---|---|---|---|---|")

for name, simulator in variants.items():
    for sku in test_products:
        copied = simulator(sku)
        tp = len(copied.intersection(gt_positives[sku]))
        fp = len(copied.difference(gt_positives[sku]))
        fn = len(gt_positives[sku].difference(copied))
        
        precision = tp / len(copied) if len(copied) > 0 else 0.0
        recall = tp / len(gt_positives[sku]) if len(gt_positives[sku]) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        prod_short = test_products[sku]["name"].split(" (")[0]
        print(f"| {name} | {prod_short} | {len(copied)} | {tp} | {fp} | {fn} | {precision:.2%} | {recall:.2%} | {f1:.4f} |")
print("=" * 60)
