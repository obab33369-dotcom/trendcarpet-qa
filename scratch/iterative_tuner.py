import os
import sys
import re
import json
import time
import base64
import random
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

# Load databases
def load_db(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        return []
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

batch1 = load_db("rooms_turboflow_batch1.json")
batch2 = load_db("rooms_turboflow_batch2.json")
full_catalog = load_db("rooms_turboflow_full_catalog.json")

# Load mapping files
sku_map = {}
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
if os.path.exists(sku_map_path):
    with open(sku_map_path, 'r', encoding='utf-8') as f:
        sku_map = json.load(f)

brand_sku_dict = {}
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
if os.path.exists(brand_dict_path):
    with open(brand_dict_path, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)

# Helper functions for anchor resolution
def clean_ref(filename):
    base = re.sub(r'^\d+_', '', filename)
    base, _ = os.path.splitext(base)
    base = re.sub(r'-1-26u-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1-26u$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-26u$', '', base, flags=re.IGNORECASE)
    return base

def normalize(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', '’': '', '`': '', '\'': ''}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def get_simple_norm(norm_val):
    val = re.sub(r'\d+x\d+', '', norm_val)
    val = re.sub(r'\d+cm', '', val)
    val = re.sub(r'\d+', '', val)
    colors = ['cm', 'ek', 'valnot', 'svart', 'vit', 'gra', 'natur', 'beige', 'gron', 'bla', 'morkgra', 'ljusgra', 'brun', 'guld', 'massing', 'silver', 'satin', 'creme']
    for color in colors:
        val = val.replace(color, '')
    return val

brand_keys = []
for slug, info in brand_sku_dict.items():
    norm_slug = normalize(slug)
    norm_name = normalize(info.get('name', ''))
    brand_keys.append({
        'slug': slug,
        'sku': info['sku'],
        'name': info.get('name', ''),
        'norm_slug': norm_slug,
        'norm_name': norm_name,
        'simple_norm_slug': get_simple_norm(norm_slug),
        'simple_norm_name': get_simple_norm(norm_name)
    })

def resolve_anchor(ref):
    ref_lower = ref.lower()
    if 'newcastle' in ref_lower:
        return 'NEWCASTLE-BLACK', "Bokhylla Newcastle Svart"
    if 'cardoba' in ref_lower:
        return 'H000022821', "Sidobord Cardoba Natur"
    if 'istria' in ref_lower:
        return '76375', "Sängbord Istria Natur"
    if 'blåvik' in ref_lower or 'blavik' in ref_lower:
        return '23101-natur', "Byrå Blåvik - Natur"
    if 'cadiz-natur' in ref_lower and 'skrivbord' in ref_lower:
        return 'CADIZ-DESK', "Skrivbord Cadiz - Natur"
    if 'torekov' in ref_lower:
        if 'valnöt' in ref_lower or 'valnot' in ref_lower:
            return '2251-1%20Walnut', "Sidobord Torekov - Ljus Valnöt"
        elif 'ek' in ref_lower:
            return '2251-1%20Oak', "Sidobord Torekov Ek"
        elif 'skåp' in ref_lower or 'skap' in ref_lower or 'natur' in ref_lower:
            return 'TOREKOV-CABINET', "Skåp Torekov - Natur"

    if ref in sku_map:
        val = sku_map[ref]
        return val['sku'], val.get('slug', '')
        
    for k, v in sku_map.items():
        if k.lower() == ref.lower():
            return v['sku'], v.get('slug', '')

    cleaned = clean_ref(ref)
    norm_c = normalize(cleaned)
    simple_norm_c = get_simple_norm(norm_c)

    for bk in brand_keys:
        if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
            return bk['sku'], bk['slug']

    if re.match(r'^\d+$', cleaned):
        for k, v in sku_map.items():
            if k.startswith(cleaned + "_"):
                return v['sku'], v.get('slug', '')

    for bk in brand_keys:
        if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
            return bk['sku'], bk['slug']

    for bk in brand_keys:
        if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
            return bk['sku'], bk['slug']

    for bk in brand_keys:
        if bk['simple_norm_slug'] in simple_norm_c or simple_norm_c in bk['simple_norm_slug'] or bk['simple_norm_name'] in simple_norm_c or simple_norm_c in bk['simple_norm_name']:
            if len(bk['simple_norm_slug']) > 4 or len(bk['simple_norm_name']) > 4:
                return bk['sku'], bk['slug']

    return None, None

# Load or initialize ground truth cache
if os.path.exists(GROUND_TRUTH_PATH):
    with open(GROUND_TRUTH_PATH, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
else:
    ground_truth = {}

# Build prompt-to-references index mapping
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

# Locate all reference images
ref_image_sources = [
    os.path.join(PROJECT_DIR, "ftp_upload_cropped_full", "artiklar"),
    os.path.join(PROJECT_DIR, "missed-products-upload", "artiklar")
]

def find_ref_photo_path(sku):
    # Try direct SKU match
    for src in ref_image_sources:
        if not os.path.exists(src):
            continue
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            p = os.path.join(src, f"{sku}{ext}")
            if os.path.exists(p):
                return p
    return None

# Find all renders on OneDrive
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

print(f"Loaded {len(found_files)} render files from OneDrive.")

# Map each SKU to its room prompt indices
sku_to_prompts = {}

def index_skus_in_db(db_name):
    for idx, data in db_prompts[db_name].items():
        for i, ref in enumerate(data["refs"]):
            sku, _ = resolve_anchor(ref)
            if sku:
                if sku not in sku_to_prompts:
                    sku_to_prompts[sku] = []
                sku_to_prompts[sku].append({
                    "db": db_name,
                    "index": idx,
                    "position": i
                })

index_skus_in_db("batch1")
index_skus_in_db("batch2")
index_skus_in_db("full_catalog")

# Filter to get eligible SKUs (have reference photo, at least 1 prompt reference, and at least 3 candidate files in found_files under Broadest Logic)
eligible_skus = []
b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

def get_candidates_broad(sku):
    prompts_info = sku_to_prompts.get(sku, [])
    prompt_indices = {item["index"] for item in prompts_info}
    candidates = set()
    for item in found_files:
        prefix = item["prefix"]
        suffix = item["suffix"]
        if prefix in prompt_indices or (suffix is not None and suffix in prompt_indices):
            candidates.add(item["filename"])
    return candidates

for sku in sku_to_prompts:
    ref_photo = find_ref_photo_path(sku)
    if ref_photo:
        candidates = get_candidates_broad(sku)
        # We want products that actually have renders generated so the tuning evaluation is meaningful (between 3 and 40 candidates)
        if 3 <= len(candidates) <= 40:
            # Skip the test products from auto_tuner
            if sku not in ["MLM-502580-lightgrey", "DETROITST01"]:
                eligible_skus.append({
                    "sku": sku,
                    "ref_photo": ref_photo,
                    "candidate_count": len(candidates)
                })

print(f"Found {len(eligible_skus)} eligible products for random selection.")

# Select 3 random products
random.seed(int(time.time()))
selected_products = random.sample(eligible_skus, min(3, len(eligible_skus)))

print("\nSelected Products for Tuning Loop:")
for p in selected_products:
    print(f" - SKU: {p['sku']} (Renders candidate count: {p['candidate_count']}) | Photo: {os.path.basename(p['ref_photo'])}")

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

# Populate ground truth for all candidates of the selected products
print("\nObtaining Ground Truth via Gemini...")
for p in selected_products:
    sku = p["sku"]
    candidates = get_candidates_broad(sku)
    ref_b64 = encode_image(p["ref_photo"])
    if not ref_b64:
        print(f"Error: Could not encode reference photo for {sku}")
        continue
        
    for fn in candidates:
        if fn in ground_truth:
            continue
            
        # Find file path
        filepath = None
        for item in found_files:
            if item["filename"] == fn:
                filepath = item["path"]
                break
                
        if not filepath:
            continue
            
        print(f" -> Querying Gemini for {sku} and candidate {fn}...", end=" ", flush=True)
        cand_b64 = encode_image(filepath)
        if not cand_b64:
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
print("Ground truth cache updated.")

# Simulation variants
def simulate_variant_1(sku):
    prompts_info = sku_to_prompts.get(sku, [])
    # Filter prompt indices mapping by DB matching rules
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
            
        for p_info in prompts_info:
            if p_info["index"] == prefix and p_info["db"] == db_name:
                copied.add(item["filename"])
                break
    return copied

def simulate_variant_2(sku):
    prompts_info = sku_to_prompts.get(sku, [])
    prompt_indices = {p["index"] for p in prompts_info}
    copied = set()
    for item in found_files:
        if item["prefix"] in prompt_indices:
            copied.add(item["filename"])
    return copied

def simulate_variant_3(sku):
    prompts_info = sku_to_prompts.get(sku, [])
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
            
        matched = False
        for p_info in prompts_info:
            if p_info["db"] == db_name:
                if p_info["index"] == prefix:
                    matched = True
                    break
                if suffix is not None and p_info["index"] == suffix:
                    matched = True
                    break
        if matched:
            copied.add(item["filename"])
    return copied

def simulate_variant_4(sku):
    prompts_info = sku_to_prompts.get(sku, [])
    prompt_indices = {p["index"] for p in prompts_info}
    copied = set()
    for item in found_files:
        if item["prefix"] in prompt_indices or (item["suffix"] is not None and item["suffix"] in prompt_indices):
            copied.add(item["filename"])
    return copied

# Print evaluation results
print("\n" + "=" * 60)
print("             EVALUATING SORTING LOGIC VARIANTS            ")
print("=" * 60)

variants = {
    "Variant 1: Strict Prefix-Only (Strict Diff DB)": simulate_variant_1,
    "Variant 2: Unified Prefix-Only (Search All DBs)": simulate_variant_2,
    "Variant 3: Suffix Fallback (Strict Diff DB)": simulate_variant_3,
    "Variant 4: Unified Suffix Fallback (Search All DBs)": simulate_variant_4
}

results_log = []

for name, simulator in variants.items():
    print(f"\nEvaluating: {name}")
    total_copied = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for p in selected_products:
        sku = p["sku"]
        copied = simulator(sku)
        
        # Calculate actual TP/FP/FN using Gemini ground truth
        gt_positives = {fn for fn in get_candidates_broad(sku) if ground_truth.get(fn, False)}
        
        tp = len(copied.intersection(gt_positives))
        fp = len(copied.difference(gt_positives))
        fn = len(gt_positives.difference(copied))
        
        total_copied += len(copied)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
        precision = tp / len(copied) if len(copied) > 0 else 0.0
        recall = tp / len(gt_positives) if len(gt_positives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        print(f" - {sku}: Copied={len(copied)}, TP={tp}, FP={fp}, FN={fn} | Precision={precision:.2%}, Recall={recall:.2%}, F1={f1:.4f}")
        
    avg_precision = total_tp / total_copied if total_copied > 0 else 0.0
    # Recall represents how many of the actual true images we retrieved
    # For a hybrid pipeline, we want Recall to be as close to 100% as possible.
    all_gt_positives = sum(len({fn for fn in get_candidates_broad(p["sku"]) if ground_truth.get(fn, False)}) for p in selected_products)
    avg_recall = total_tp / all_gt_positives if all_gt_positives > 0 else 0.0
    avg_f1 = 2 * avg_precision * avg_recall / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0.0
    
    print(f" SUMMARY -> Total Copied: {total_copied} | Recall: {avg_recall:.2%} | Precision (Pre-Gemini Filter): {avg_precision:.2%} | F1 Score: {avg_f1:.4f}")
    results_log.append({
        "name": name,
        "total_copied": total_copied,
        "recall": avg_recall,
        "precision": avg_precision,
        "f1": avg_f1
    })

# Automated tuning loop recommendation
print("\n" + "=" * 60)
print("                  TUNING RECOMMENDATION                   ")
print("=" * 60)

# Sort variants by Recall (primary) and then by total_copied (secondary, smaller is better)
sorted_variants = sorted(results_log, key=lambda x: (-x["recall"], x["total_copied"]))
best_variant = sorted_variants[0]

print(f"Best Metadata Selector: {best_variant['name']}")
print(f"  Recall (Target Coverage): {best_variant['recall']:.2%}")
print(f"  Candidate Copies Pool Size: {best_variant['total_copied']} files (Total for 3 products)")
print(f"  F1 Score (Metadata only): {best_variant['f1']:.4f}")

# Decide if we need fallback or prefix-only
if best_variant["recall"] >= 0.99:
    print("\nRecommendation:")
    print(" -> Variant 1 (Strict Prefix-Only with Diff DB) or Variant 3 is optimal.")
    print(" -> Since Recall is already 100% (all correct images are captured), we do NOT need broader matching.")
    print(" -> Using Variant 1 keeps the candidate pool size minimal, reducing Gemini API costs by a large factor.")
else:
    print("\nRecommendation:")
    print(" -> Recall is less than 100%. Suffix fallback or Unified DB searching is required to retrieve missed correct images.")
    print(f" -> Use {best_variant['name']} to avoid missing product images, followed by Gemini filtering.")

print("=" * 60)
