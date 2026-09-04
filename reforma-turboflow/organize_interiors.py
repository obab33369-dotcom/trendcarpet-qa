import os
import sys
import json
import shutil
import re
import urllib.parse

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
REFORMA_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
BRAIN_SCRATCH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\scratch"

PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PICS_SQUARE_DIR = os.path.join(PICS_DIR, "första omgången fyrkantiga")
TARGET_DIR = os.path.join(PICS_DIR, "Reforma-interiörer-26-06")

CROP_SRC_1 = os.path.join(PICS_DIR, r"ftp_upload_cropped_full\artiklar")
CROP_SRC_2 = os.path.join(PICS_DIR, r"missed-products-upload\artiklar")

# Databases
DATABASES = [
    "rooms_turboflow.json",
    "rooms_turboflow_batch1.json"
]

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
    # Remove invalid characters for Windows folders
    return re.sub(r'[\\/*?:\'\"<>|]', '', name).strip()

def main():
    print("==================================================")
    print("      ORGANIZING ROOM RENDERS BY FURNITURE        ")
    print("==================================================")

    # 1. Load Room Databases
    def load_db(filename):
        p = os.path.join(REFORMA_DIR, filename)
        if not os.path.exists(p):
            return {}
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
    print(f"[OK] Loaded {len(batch1_map)} Batch 1, {len(batch2_map)} Batch 2, and {len(full_catalog_map)} Full Catalog mappings.")

    # 2. Load Mapping Databases
    sku_map_path = os.path.join(REFORMA_DIR, 'sku_map.json')
    brand_dict_path = os.path.join(REFORMA_DIR, 'brand_sku_dict.json')
    pipeline_path = os.path.join(BRAIN_SCRATCH, 'pipeline_mappings.json')
    missed_path = os.path.join(PICS_DIR, 'missed_products.json')

    sku_map = {}
    if os.path.exists(sku_map_path):
        with open(sku_map_path, 'r', encoding='utf-8') as f:
            sku_map = json.load(f)

    brand_sku_dict = {}
    if os.path.exists(brand_dict_path):
        with open(brand_dict_path, 'r', encoding='utf-8') as f:
            brand_sku_dict = json.load(f)

    pipeline_mappings = []
    if os.path.exists(pipeline_path):
        with open(pipeline_path, 'r', encoding='utf-8') as f:
            pipeline_mappings = json.load(f)
    pipeline_slugs = {item['product']: item['sku'] for item in pipeline_mappings}

    missed_products = {}
    if os.path.exists(missed_path):
        with open(missed_path, 'r', encoding='utf-8') as f:
            missed_products = json.load(f)

    # 3. Pre-normalize names for fuzzy matching
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

    pipeline_keys = []
    for slug, sku in pipeline_slugs.items():
        norm_val = normalize(slug)
        pipeline_keys.append({
            'slug': slug,
            'sku': sku,
            'norm': norm_val,
            'simple_norm': get_simple_norm(norm_val)
        })

    missed_keys = []
    for slug, sku in missed_products.items():
        norm_slug = normalize(slug)
        missed_keys.append({
            'slug': slug,
            'sku': sku,
            'norm': norm_slug,
            'simple_norm': get_simple_norm(norm_slug)
        })

    # Helper function to resolve SKU & Name
    def resolve_anchor(ref):
        # A. Check manual overrides first
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

        # B. Direct matches in sku_map
        if ref in sku_map:
            val = sku_map[ref]
            name = get_beautiful_name(val.get('slug', ''))
            # Try to get more beautiful name from brand_sku_dict if possible
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

        # C. Direct check in missed_products
        if cleaned in missed_products:
            return missed_products[cleaned], get_beautiful_name(cleaned)
        for mk in missed_keys:
            if mk['norm'] == norm_c:
                return mk['sku'], get_beautiful_name(mk['slug'])

        # D. Match pipeline_mappings
        for pk in pipeline_keys:
            if pk['norm'] == norm_c:
                return pk['sku'], get_beautiful_name(pk['slug'])

        # E. Match brand_sku_dict (slug/name exact)
        for bk in brand_keys:
            if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
                return bk['sku'], bk['name']

        # E2. Check prefix mapping for numeric refs (like 1777 -> 1777_matbord...)
        if re.match(r'^\d+$', cleaned):
            for k, v in sku_map.items():
                if k.startswith(cleaned + "_"):
                    name = get_beautiful_name(v.get('slug', ''))
                    for bk in brand_keys:
                        if bk['sku'] == v['sku'] and bk['name']:
                            name = bk['name']
                            break
                    return v['sku'], name

        # F. Match simple norms
        for mk in missed_keys:
            if mk['simple_norm'] == simple_norm_c:
                return mk['sku'], get_beautiful_name(mk['slug'])
        for pk in pipeline_keys:
            if pk['simple_norm'] == simple_norm_c:
                return pk['sku'], get_beautiful_name(pk['slug'])
        for bk in brand_keys:
            if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
                return bk['sku'], bk['name']

        # G. Substring matching
        for mk in missed_keys:
            if mk['norm'] in norm_c or norm_c in mk['norm']:
                return mk['sku'], get_beautiful_name(mk['slug'])
        for pk in pipeline_keys:
            if pk['norm'] in norm_c or norm_c in pk['norm']:
                return pk['sku'], get_beautiful_name(pk['slug'])
        for bk in brand_keys:
            if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
                return bk['sku'], bk['name']

        # H. Simple norm substring matches
        for mk in missed_keys:
            if mk['simple_norm'] in simple_norm_c or simple_norm_c in mk['simple_norm']:
                if len(mk['simple_norm']) > 4:
                    return mk['sku'], get_beautiful_name(mk['slug'])
        for pk in pipeline_keys:
            if pk['simple_norm'] in simple_norm_c or simple_norm_c in pk['simple_norm']:
                if len(pk['simple_norm']) > 4:
                    return pk['sku'], get_beautiful_name(pk['slug'])
        for bk in brand_keys:
            if bk['simple_norm_slug'] in simple_norm_c or simple_norm_c in bk['simple_norm_slug'] or bk['simple_norm_name'] in simple_norm_c or simple_norm_c in bk['simple_norm_name']:
                if len(bk['simple_norm_slug']) > 4 or len(bk['simple_norm_name']) > 4:
                    return bk['sku'], bk['name']

        # I. Fallback
        return None, get_beautiful_name(cleaned)

    # Create target main directory
    os.makedirs(TARGET_DIR, exist_ok=True)

    # 4. Scan and sort images
    print("\n📸 Scanning render images in Square & Main directories...")
    
    render_dirs = [
        (PICS_SQUARE_DIR, "Square (Första omgången fyrkantiga)"),
        (PICS_DIR, "Main (turboflow)")
    ]

    copied_renders = 0
    copied_refs = set()
    active_folders = {} # maps subfolder path to (SKU, CleanName)
    skipped_files = []

    suffix_pattern = re.compile(r"^(\d+)-architectural-digest-styl(?:e)?-(.+?)\.(?:png|jpg|jpeg|webp)$", re.IGNORECASE)

    for src_dir, dir_label in render_dirs:
        if not os.path.exists(src_dir):
            print(f"⚠️ Warning: Directory '{dir_label}' not found at: {src_dir}")
            continue
            
        files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        print(f"   Found {len(files)} renders in '{dir_label}' folder.")
        
        # Date filter for Main staging folder to only process new files (from June 8th onwards)
        if src_dir == PICS_DIR:
            import datetime
            cutoff_date = datetime.datetime(2026, 6, 8)
            filtered_files = []
            for f in files:
                filepath = os.path.join(src_dir, f)
                mtime = os.path.getmtime(filepath)
                dt = datetime.datetime.fromtimestamp(mtime)
                if dt >= cutoff_date:
                    filtered_files.append(f)
            files = filtered_files
            print(f"   Filtered to {len(files)} new renders (modified on/after June 8th) in '{dir_label}' folder.")
        
        b2_diffs = [46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593]

        for f in files:
            m = suffix_pattern.match(f)
            if not m:
                m_simple = re.match(r"^(\d+)", f)
                if not m_simple:
                    continue
                lead_idx = int(m_simple.group(1))
                anchor = full_catalog_map.get(lead_idx) or batch1_map.get(lead_idx)
                db_used = "Fallback (Full/Batch1)"
            else:
                lead_idx = int(m.group(1))
                style_part = m.group(2)
                m_style_digits = re.match(r"^(\d+)", style_part)
                if m_style_digits:
                    style_num = int(m_style_digits.group(1))
                    diff = lead_idx - style_num
                    if diff == 0:
                        anchor = batch1_map.get(lead_idx)
                        db_used = "Batch 1"
                    elif diff in b2_diffs and lead_idx <= 692:
                        anchor = batch2_map.get(lead_idx)
                        db_used = "Batch 2"
                    else:
                        anchor = full_catalog_map.get(lead_idx)
                        db_used = "Full Catalog"
                else:
                    anchor = full_catalog_map.get(lead_idx)
                    db_used = "Full Catalog"
            
            if not anchor:
                anchor = full_catalog_map.get(lead_idx) or batch1_map.get(lead_idx)
                if not anchor:
                    skipped_files.append((f, f"No room anchor defined for index {lead_idx}"))
                    continue
                
            sku, name = resolve_anchor(anchor)
            if not sku:
                skipped_files.append((f, f"Could not resolve SKU for anchor '{anchor}'"))
                continue
                
            # Create folder name: "Name (SKU)"
            folder_title = f"{name} ({sku})"
            clean_title = clean_folder_name(folder_title)
            subfolder_path = os.path.join(TARGET_DIR, clean_title)
            
            os.makedirs(subfolder_path, exist_ok=True)
            active_folders[subfolder_path] = (sku, name)
            
            src_file = os.path.join(src_dir, f)
            dest_file = os.path.join(subfolder_path, f)
            
            try:
                shutil.copy2(src_file, dest_file)
                copied_renders += 1
            except Exception as e:
                print(f"❌ Error copying {f} to folder '{clean_title}': {e}")

    # 5. Copy comparison reference photos
    print("\n📦 Copying comparison reference photos...")
    copied_ref_photos = 0
    missing_refs = []

    for folder_path, (sku, name) in active_folders.items():
        ref_dest_name = f"00_REFERENCE_{sku}.jpg"
        # URL unquote SKU to handle things like %20 correctly
        unquoted_sku = urllib.parse.unquote(sku)
        
        # Determine source path
        ref_src_path = None
        
        if sku == 'NEWCASTLE-BLACK':
            # Newcastle fallback from project batch1_images
            ref_src_path = os.path.join(REFORMA_DIR, r"batch1_images\2234_bokhylla-newcastle-165cm-svart-1-26U-wonder.png")
            ref_dest_name = "00_REFERENCE_NEWCASTLE-BLACK.png"
        else:
            # Check Crop Source 1 first
            p1 = os.path.join(CROP_SRC_1, f"{unquoted_sku}.jpg")
            p2 = os.path.join(CROP_SRC_1, f"{sku}.jpg") # try original sku string
            
            # Check Crop Source 2 second
            p3 = os.path.join(CROP_SRC_2, f"{unquoted_sku}.jpg")
            p4 = os.path.join(CROP_SRC_2, f"{sku}.jpg")
            
            for path_cand in [p1, p2, p3, p4]:
                if os.path.exists(path_cand):
                    ref_src_path = path_cand
                    break
                    
        if ref_src_path and os.path.exists(ref_src_path):
            dest_path = os.path.join(folder_path, ref_dest_name)
            try:
                shutil.copy2(ref_src_path, dest_path)
                copied_ref_photos += 1
                copied_refs.add(sku)
            except Exception as e:
                print(f"❌ Error copying reference photo {ref_src_path}: {e}")
        else:
            missing_refs.append((sku, name, folder_path))

    # Print summary
    print("\n==================================================")
    print("                SORTING COMPLETED!                ")
    print("==================================================")
    print(f"📂 Target Directory: {TARGET_DIR}")
    print(f"🗂️ Unique furniture folders created: {len(active_folders)}")
    print(f"📝 Total render instances copied: {copied_renders}")
    print(f"🖼️ Reference photos copied: {copied_ref_photos}")
    print(f"⚠️ Skipped files: {len(skipped_files)}")
    if skipped_files:
        print("   First 10 skipped files:")
        for fn, reason in skipped_files[:10]:
            print(f"     • {fn}: {reason}")
            
    if missing_refs:
        print(f"\n⚠️ Missing reference photos for {len(missing_refs)} products:")
        for sku, name, path in missing_refs[:20]:
            print(f"     • SKU: {sku} | Name: {name}")
    print("==================================================")

if __name__ == '__main__':
    main()
