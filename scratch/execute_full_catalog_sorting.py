import os
import re
import datetime
import json
import shutil
import urllib.parse

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")

def get_beautiful_name(slug):
    words = slug.split('-')
    capitalized_words = []
    for w in words:
        if not w:
            continue
        w_lower = w.lower()
        if w_lower in ('m', 's', 'l'):
            capitalized_words.append(w.upper())
        elif w_lower == 'tv':
            capitalized_words.append('TV')
        elif 'x' in w_lower and re.match(r'^\d+x\d+', w_lower):
            capitalized_words.append(w_lower)
        else:
            capitalized_words.append(w.capitalize())
    return " ".join(capitalized_words)

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

def clean_folder_name(name):
    return re.sub(r'[\\/*?:\'\"<>|]', '', name).strip()

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
            mapping[idx] = {
                "prompt": prompt,
                "refs": [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
            }
    return mapping

# Load mappings
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

# FIX: Override Lucca Sofa so it doesn't map to Texas Sofa
for k in list(sku_map.keys()):
    if "1397" in k:
        sku_map[k] = {
            'sku': '1397',
            'slug': 'baddsoffa-lucca-gra',
            'url': '',
            'current_images': []
        }

with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_sku_dict = json.load(f)

# Pre-normalize for resolving
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
    
    # 0. Visual overrides for duplicate/mislabeled carpet source files
    if "2087_matta-seronis-svart-beige" in ref_lower:
        return "RG01-19", "Matta 'Aravelle' - Grå/Multi"
    if "2089_matta-sorvento-svart-beige" in ref_lower:
        return "RG01-499", "Matta 'Orlisse' - Brun"
    if "2104_matta-velenna-svart-beige" in ref_lower:
        return "RG01-64", "Matta 'Arvella' - Brun"
        
    sku, name = _resolve_anchor_raw(ref)
    if sku == 'RG01-1':
        return 'RG01-19', "Matta 'Aravelle' - Grå/Multi"
    if sku == 'RG01-49':
        return 'RG01-499', "Matta 'Orlisse' - Brun"
    return sku, name

def _resolve_anchor_raw(ref):
    ref_lower = ref.lower()
    
    # Check if this is a carpet/rug file to avoid Batch 1 collisions on numeric prefix
    is_carpet_file = "matta" in ref_lower or "rug" in ref_lower or "rg01" in ref_lower
    
    # Try numeric prefix match first to handle encoding differences (e.g. byr vs byrå) (skip for carpets)
    m = re.match(r'^(\d+)_', ref)
    if m and not is_carpet_file:
        prefix = m.group(1)
        for k, v in sku_map.items():
            if k.startswith(prefix + "_"):
                name = get_beautiful_name(v.get('slug', ''))
                for bk in brand_keys:
                    if bk['sku'] == v['sku'] and bk['name']:
                        name = bk['name']
                        break
                return v['sku'], name

    # Try direct SKU match
    cleaned = ref
    if cleaned.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
        cleaned = os.path.splitext(cleaned)[0]
    cleaned_base = clean_ref(ref)
    
    for bk in brand_keys:
        if bk['sku'].lower() == cleaned.lower() or bk['sku'].lower() == cleaned_base.lower():
            return bk['sku'], bk['name']

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
            return '2251-1 Walnut', "Sidobord Torekov - Ljus Valnöt"
        elif 'ek' in ref_lower:
            return '2251-1 Oak', "Sidobord Torekov Ek"
        elif 'skåp' in ref_lower or 'skap' in ref_lower or 'natur' in ref_lower:
            return 'TOREKOV-CABINET', "Skåp Torekov - Natur"

    if ref in sku_map:
        val = sku_map[ref]
        name = get_beautiful_name(val.get('slug', ''))
        for bk in brand_keys:
            if bk['sku'] == val['sku'] and bk['name']:
                name = bk['name']
                break
        return val['sku'], name
        
    for k, v in sku_map.items():
        if k.lower() == ref.lower():
            name = get_beautiful_name(v.get('slug', ''))
            for bk in brand_keys:
                if bk['sku'] == v['sku'] and bk['name']:
                    name = bk['name']
                    break
            return v['sku'], name

    norm_c = normalize(cleaned_base)
    simple_norm_c = get_simple_norm(norm_c)

    for bk in brand_keys:
        if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
            return bk['sku'], bk['name']

    if re.match(r'^\d+$', cleaned_base):
        for k, v in sku_map.items():
            if k.startswith(cleaned_base + "_"):
                name = get_beautiful_name(v.get('slug', ''))
                for bk in brand_keys:
                    if bk['sku'] == v['sku'] and bk['name']:
                        name = bk['name']
                        break
                return v['sku'], name

    if simple_norm_c:
        for bk in brand_keys:
            if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
                return bk['sku'], bk['name']

    if len(norm_c) >= 4:
        for bk in brand_keys:
            if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
                return bk['sku'], bk['name']

    if len(simple_norm_c) >= 4:
        for bk in brand_keys:
            if bk['simple_norm_slug'] in simple_norm_c or simple_norm_c in bk['simple_norm_slug'] or bk['simple_norm_name'] in simple_norm_c or simple_norm_c in bk['simple_norm_name']:
                if len(bk['simple_norm_slug']) > 4 or len(bk['simple_norm_name']) > 4:
                    return bk['sku'], bk['name']

    return None, get_beautiful_name(cleaned_base)

def main():
    print("=== STARTING FULL CATALOG EXCLUSIVE REBUILD ===")
    
    # Load database
    full_catalog = load_db("rooms_turboflow_full_catalog.json")
    print(f"Loaded {len(full_catalog)} Full Catalog prompts.")
    
    dirs_to_scan = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    # 1. Filter raw files that belong strictly to the Full Catalog batch
    full_catalog_files = []
    
    for d in dirs_to_scan:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            m = re.match(r"^(\d+)", f)
            if not m:
                continue
            prefix = int(m.group(1))
            
            if 1 <= prefix <= 3340:
                path = os.path.join(d, f)
                try:
                    stat = os.stat(path)
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                    
                    # Full Catalog batch matching criteria:
                    # - File has "(1)" in the name (which resolved overlaps on June 2/3)
                    # - OR the file was modified on or after June 8th
                    is_full_catalog = False
                    if "(1)" in f or " (1)" in f:
                        is_full_catalog = True
                    elif mtime.date() >= datetime.date(2026, 6, 8):
                        is_full_catalog = True
                        
                    if is_full_catalog:
                        full_catalog_files.append({
                            "filename": f,
                            "prefix": prefix,
                            "path": path,
                            "mtime": mtime
                        })
                except Exception:
                    pass
                    
    print(f"Isolated {len(full_catalog_files)} files belonging to the Full Catalog run.")
    
    # 2. Map isolated files to product folders
    product_images = {}
    
    for item in full_catalog_files:
        prefix = item["prefix"]
        fn = item["filename"]
        
        if prefix in full_catalog:
            refs = full_catalog[prefix]["refs"]
            for ref_idx, ref in enumerate(refs):
                sku, name = resolve_anchor(ref)
                if sku:
                    if sku not in product_images:
                        product_images[sku] = {
                            "name": name,
                            "primaries": [],
                            "secondaries": []
                        }
                    
                    file_record = {
                        "filename": fn,
                        "src_path": item["path"]
                    }
                    
                    if ref_idx == 0:
                        product_images[sku]["primaries"].append(file_record)
                    else:
                        product_images[sku]["secondaries"].append(file_record)
                        
    print(f"Mapped files to {len(product_images)} unique products.")
    
    # 3. Create target folder structure and copy files
    if os.path.exists(TARGET_DIR):
        print(f"Target directory exists. Cleaning it: {TARGET_DIR}")
        try:
            shutil.rmtree(TARGET_DIR)
        except Exception as e:
            print(f"Error cleaning target directory: {e}")
            
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    copied_total = 0
    
    for sku, data in product_images.items():
        name = data["name"]
        folder_title = f"{name} ({sku})"
        clean_title = clean_folder_name(folder_title)
        product_folder = os.path.join(TARGET_DIR, clean_title)
        
        if not data["primaries"] and not data["secondaries"]:
            continue
            
        os.makedirs(product_folder, exist_ok=True)
        
        # Copy primaries
        seen_primary = set()
        for f in data["primaries"]:
            if f["filename"] not in seen_primary:
                seen_primary.add(f["filename"])
                dest = os.path.join(product_folder, f["filename"])
                try:
                    shutil.copy2(f["src_path"], dest)
                    copied_total += 1
                except Exception:
                    pass
                    
        # Copy secondaries (reserv)
        seen_secondary = set()
        if data["secondaries"]:
            reserv_folder = os.path.join(product_folder, "reserv")
            os.makedirs(reserv_folder, exist_ok=True)
            for f in data["secondaries"]:
                if f["filename"] not in seen_secondary:
                    seen_secondary.add(f["filename"])
                    dest = os.path.join(reserv_folder, f["filename"])
                    try:
                        shutil.copy2(f["src_path"], dest)
                        copied_total += 1
                    except Exception:
                        pass
                        
        # Copy reference photo
        unquoted_sku = urllib.parse.unquote(sku)
        ref_src_paths = [
            os.path.join(WORKSPACE_DIR, "reforma-original-images", f"{unquoted_sku}.jpg"),
            os.path.join(WORKSPACE_DIR, "reforma-original-images", f"{unquoted_sku}.png"),
            os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{unquoted_sku}.jpg"),
            os.path.join(ONEDRIVE_DIR, "ftp_upload", "artiklar", f"{unquoted_sku}.png")
        ]
        
        ref_copied = False
        for path in ref_src_paths:
            if os.path.exists(path):
                ext = os.path.splitext(path)[1]
                ref_dest = os.path.join(product_folder, f"00_REFERENCE_{unquoted_sku}{ext}")
                try:
                    shutil.copy2(path, ref_dest)
                    ref_copied = True
                    break
                except Exception:
                    pass
                    
        if not ref_copied:
            # Fallback scan in reforma-original-images
            orig_dir = os.path.join(WORKSPACE_DIR, "reforma-original-images")
            if os.path.exists(orig_dir):
                for f in os.listdir(orig_dir):
                    if unquoted_sku.lower() in f.lower():
                        ext = os.path.splitext(f)[1]
                        ref_dest = os.path.join(product_folder, f"00_REFERENCE_{unquoted_sku}{ext}")
                        try:
                            shutil.copy2(os.path.join(orig_dir, f), ref_dest)
                            break
                        except Exception:
                            pass
                            
    print(f"\nRebuild completed! Sorted {copied_total} renders into product folders inside 'Reforma-Full-Catalog-sortering'.")

if __name__ == "__main__":
    main()
