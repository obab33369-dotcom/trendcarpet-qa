import os
import re
import datetime
import json
import shutil
import urllib.parse

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering")

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

    cleaned = clean_ref(ref)
    norm_c = normalize(cleaned)
    simple_norm_c = get_simple_norm(norm_c)

    for bk in brand_keys:
        if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
            return bk['sku'], bk['name']

    if re.match(r'^\d+$', cleaned):
        for k, v in sku_map.items():
            if k.startswith(cleaned + "_"):
                name = get_beautiful_name(v.get('slug', ''))
                for bk in brand_keys:
                    if bk['sku'] == v['sku'] and bk['name']:
                        name = bk['name']
                        break
                return v['sku'], name

    for bk in brand_keys:
        if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
            return bk['sku'], bk['name']

    for bk in brand_keys:
        if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
            return bk['sku'], bk['name']

    for bk in brand_keys:
        if bk['simple_norm_slug'] in simple_norm_c or simple_norm_c in bk['simple_norm_slug'] or bk['simple_norm_name'] in simple_norm_c or simple_norm_c in bk['simple_norm_name']:
            if len(bk['simple_norm_slug']) > 4 or len(bk['simple_norm_name']) > 4:
                return bk['sku'], bk['name']

    return None, get_beautiful_name(cleaned)

def rebuild_all():
    print("Loading databases...")
    batch1 = load_db("rooms_turboflow_batch1.json")
    batch2 = load_db("rooms_turboflow_batch2.json")
    full_catalog = load_db("rooms_turboflow_full_catalog.json")
    print(f"Loaded {len(batch1)} Batch 1, {len(batch2)} Batch 2, {len(full_catalog)} Full Catalog prompts.")

    dirs_to_scan = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    files_info = []
    for d in dirs_to_scan:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            path = os.path.join(d, f)
            try:
                stat = os.stat(path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files_info.append({
                    "filename": f,
                    "mtime": mtime,
                    "path": path,
                    "dir": os.path.basename(d)
                })
            except Exception:
                pass

    if not files_info:
        print("No files found to process.")
        return

    # Sort chronologically
    files_info.sort(key=lambda x: x["mtime"])
    
    # Group into clusters
    clusters = []
    current_cluster = [files_info[0]]
    for item in files_info[1:]:
        time_diff = (item["mtime"] - current_cluster[-1]["mtime"]).total_seconds() / 3600.0
        if time_diff > 2.0:
            clusters.append(current_cluster)
            current_cluster = [item]
        else:
            current_cluster.append(item)
    clusters.append(current_cluster)
    
    cluster_db_map = {
        0: ("Batch 2", batch2),
        1: ("Batch 1", batch1),
        2: ("Batch 1", batch1),
        3: ("Full Catalog", full_catalog),
        4: ("Full Catalog", full_catalog)
    }

    # Maps SKU -> { "name": str, "primaries": [], "secondaries": [] }
    product_images = {}

    print("Mapping all files to products...")
    for c_idx, cluster in enumerate(clusters):
        db_label, db = cluster_db_map[c_idx]
        
        for item in cluster:
            fn = item["filename"]
            m = re.match(r"^(\d+)", fn)
            if not m:
                continue
            prefix = int(m.group(1))
            
            if prefix in db:
                refs = db[prefix]["refs"]
                # Resolve each reference in the prompt
                for ref_idx, ref in enumerate(refs):
                    sku, name = resolve_anchor(ref)
                    if sku:
                        if sku not in product_images:
                            product_images[sku] = {
                                "name": name,
                                "primaries": [],
                                "secondaries": []
                            }
                        
                        # Save source file path
                        file_record = {
                            "filename": fn,
                            "src_path": item["path"],
                            "db": db_label,
                            "prefix": prefix
                        }
                        
                        if ref_idx == 0:
                            product_images[sku]["primaries"].append(file_record)
                        else:
                            product_images[sku]["secondaries"].append(file_record)

    print(f"\nResolved images for {len(product_images)} unique products.")

    # Rebuild folders
    print("Writing files to target folders...")
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    copied_total = 0
    
    for sku, data in product_images.items():
        name = data["name"]
        folder_title = f"{name} ({sku})"
        clean_title = clean_folder_name(folder_title)
        product_folder = os.path.join(TARGET_DIR, clean_title)
        
        # We only create folders if there are actual images to copy
        if not data["primaries"] and not data["secondaries"]:
            continue
            
        os.makedirs(product_folder, exist_ok=True)
        
        # Clear main folder files (excluding reserv and discarded_by_gemini)
        for item in os.listdir(product_folder):
            if item in ("reserv", "discarded_by_gemini"):
                continue
            item_path = os.path.join(product_folder, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception:
                pass
                
        # Clear/create reserv folder
        reserv_folder = os.path.join(product_folder, "reserv")
        if data["secondaries"]:
            os.makedirs(reserv_folder, exist_ok=True)
            for item in os.listdir(reserv_folder):
                item_path = os.path.join(reserv_folder, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception:
                    pass

        # Copy primary files
        # Deduplicate filenames (in case same prefix mapped twice, should not happen)
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

        # Copy secondary files
        seen_secondary = set()
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
        # Search in local reforma-original-images or OneDrive ftp_upload/artiklar
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
        
        # Fallback search if exact SKU file not found
        if not ref_copied:
            # Check if we can find any file matching the SKU in reforma-original-images
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

    print(f"\nFinished rebuilding all product folders. Copied a total of {copied_total} renders.")

if __name__ == "__main__":
    rebuild_all()
