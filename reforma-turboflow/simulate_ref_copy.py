import os
import json
import re
import urllib.parse

REFORMA_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PICS_SQUARE_DIR = os.path.join(PICS_DIR, "första omgången fyrkantiga")

CROP_SRC_1 = os.path.join(PICS_DIR, r"ftp_upload_cropped_full\artiklar")
CROP_SRC_2 = os.path.join(PICS_DIR, r"missed-products-upload\artiklar")

def load_db(filename):
    p = os.path.join(REFORMA_DIR, filename)
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
                mapping[idx] = refs[0]
    return mapping

batch1_map = load_db("rooms_turboflow_batch1.json")
batch2_map = load_db("rooms_turboflow_batch2.json")
full_catalog_map = load_db("rooms_turboflow_full_catalog.json")

sku_map_path = os.path.join(REFORMA_DIR, 'sku_map.json')
brand_dict_path = os.path.join(REFORMA_DIR, 'brand_sku_dict.json')
missed_path = os.path.join(PICS_DIR, 'missed_products.json')

with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_sku_dict = json.load(f)

missed_products = {}
if os.path.exists(missed_path):
    with open(missed_path, 'r', encoding='utf-8') as f:
        missed_products = json.load(f)

brand_keys = []
for slug, info in brand_sku_dict.items():
    norm_slug = lambda x: re.sub(r'[^a-z0-9]', '', x.lower().replace('ö', 'o').replace('ä', 'a').replace('å', 'a'))
    brand_keys.append({
        'slug': slug,
        'sku': info['sku'],
        'name': info.get('name', ''),
        'norm_slug': norm_slug(slug),
        'norm_name': norm_slug(info.get('name', ''))
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
    
    # Try fuzzy matching...
    norm_c = re.sub(r'[^a-z0-9]', '', ref_lower.replace('ö', 'o').replace('ä', 'a').replace('å', 'a'))
    for bk in brand_keys:
        if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
            return bk['sku'], bk['name']
            
    return None, ref

# Assign all files to folders
suffix_pattern = re.compile(r"^(\d+)-architectural-digest-styl(?:e)?-(.+?)\.(?:png|jpg|jpeg|webp)$", re.IGNORECASE)
files_main = [f for f in os.listdir(PICS_DIR) if os.path.isfile(os.path.join(PICS_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
files_square = [f for f in os.listdir(PICS_SQUARE_DIR) if os.path.isfile(os.path.join(PICS_SQUARE_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
all_files = files_main + files_square

active_skus = set()
b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

for f in all_files:
    m = suffix_pattern.match(f)
    if not m: continue
    lead_idx = int(m.group(1))
    style_part = m.group(2)
    m_style_digits = re.match(r"^(\d+)", style_part)
    if m_style_digits:
        style_num = int(m_style_digits.group(1))
        diff = lead_idx - style_num
        if diff == 0:
            anchor = batch1_map.get(lead_idx)
        elif diff in b2_diffs and lead_idx <= 692:
            anchor = batch2_map.get(lead_idx)
        else:
            anchor = full_catalog_map.get(lead_idx)
    else:
        anchor = full_catalog_map.get(lead_idx)
        
    if anchor:
        sku, name = resolve_anchor(anchor)
        if sku:
            active_skus.add(sku)

print(f"Total active unique SKUs: {len(active_skus)}")
missing = []
for sku in sorted(active_skus):
    unquoted_sku = urllib.parse.unquote(sku)
    p1 = os.path.join(CROP_SRC_1, f"{unquoted_sku}.jpg")
    p2 = os.path.join(CROP_SRC_1, f"{sku}.jpg")
    p3 = os.path.join(CROP_SRC_2, f"{unquoted_sku}.jpg")
    p4 = os.path.join(CROP_SRC_2, f"{sku}.jpg")
    
    found = False
    if sku == 'NEWCASTLE-BLACK':
        found = os.path.exists(os.path.join(REFORMA_DIR, r"batch1_images\2234_bokhylla-newcastle-165cm-svart-1-26U-wonder.png"))
    else:
        for path_cand in [p1, p2, p3, p4]:
            if os.path.exists(path_cand):
                found = True
                break
    if not found:
        missing.append(sku)

print(f"Total missing reference photos: {len(missing)}")
if missing:
    print("Missing SKUs:", missing)
