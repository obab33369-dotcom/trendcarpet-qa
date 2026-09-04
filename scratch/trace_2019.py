import os
import re
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

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
                mapping[idx] = refs[0]
    return mapping

batch1_map = load_db("rooms_turboflow_batch1.json")
batch2_map = load_db("rooms_turboflow_batch2.json")
full_catalog_map = load_db("rooms_turboflow_full_catalog.json")

# Load SKU map
with open(os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json'), 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

# Load brand dict
with open(os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json'), 'r', encoding='utf-8') as f:
    brand_sku_dict = json.load(f)

brand_keys = []
for slug, info in brand_sku_dict.items():
    brand_keys.append({
        'slug': slug,
        'sku': info['sku'],
        'name': info.get('name', ''),
        'norm_slug': slug.lower().replace("-", ""),
        'norm_name': info.get('name', '').lower().replace("-", "")
    })

def resolve_anchor(ref):
    if ref in sku_map:
        val = sku_map[ref]
        return val['sku'], val.get('slug', '')
    return None, None

# Tracing
f = "2019-architectural-digest-styl-229.png"
suffix_pattern = re.compile(r"^(\d+)-architectural-digest-styl(?:e)?-(.+?)\.(?:png|jpg|jpeg|webp)$", re.IGNORECASE)
b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

m = suffix_pattern.match(f)
if m:
    lead_idx = int(m.group(1))
    style_part = m.group(2)
    m_style_digits = re.match(r"^(\d+)", style_part)
    if m_style_digits:
        style_num = int(m_style_digits.group(1))
        diff = lead_idx - style_num
        print(f"lead_idx={lead_idx}, style_num={style_num}, diff={diff}")
        if diff == 0:
            anchor = batch1_map.get(lead_idx)
            db = "batch1"
        elif diff in b2_diffs and lead_idx <= 692:
            anchor = batch2_map.get(lead_idx)
            db = "batch2"
        else:
            anchor = full_catalog_map.get(lead_idx)
            db = "full_catalog"
            
        print(f"Mapped db={db}, anchor={anchor}")
        if anchor:
            sku, name = resolve_anchor(anchor)
            print(f"Resolved SKU: {sku}, Name: {name}")
