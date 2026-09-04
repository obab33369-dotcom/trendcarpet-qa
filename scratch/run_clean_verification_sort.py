import os
import sys
import json
import re
import shutil
import stat

# Directories and Paths
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

# Fresh verification target roots matching original structure but with -NEW suffix
CLEAN_FURNITURE_ROOT = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering-NEW")
CLEAN_CARPET_ROOT = os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering-NEW")
QUARANTINE_DIR = os.path.join(TURBOFLOW_ROOT, "_quarantine-NEW")

# Original reference search directories
REF_DIRS = [
    os.path.join(PICTURES_DIR, "Refoma white background fix"),
    os.path.join(PICTURES_DIR, "TEST TOPAZ"),
    os.path.join(PICTURES_DIR, "reforma_original_images_by_product")
]

# Load resolver files
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
furniture_catalog_path = os.path.join(WORKSPACE_DIR, 'scratch', 'furniture_catalog.json')
carpet_catalog_path = os.path.join(WORKSPACE_DIR, 'scratch', 'carpet_catalog.json')
prompt_db_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'rooms_turboflow_full_catalog.json')

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

with open(furniture_catalog_path, 'r', encoding='utf-8') as f:
    furniture_catalog = json.load(f)

with open(carpet_catalog_path, 'r', encoding='utf-8') as f:
    carpet_catalog = json.load(f)

# Combine catalogs for unified SKU details lookup
sku_catalog = {}
sku_catalog.update(furniture_catalog)
sku_catalog.update(carpet_catalog)

# Set of carpet SKUs to route them to the carpet approved root
carpet_skus = set(carpet_catalog.keys())

# Load redirection plans
carpet_redirection_path = os.path.join(WORKSPACE_DIR, "scratch", "carpet_redirection_plan.json")
furniture_redirection_path = os.path.join(WORKSPACE_DIR, "scratch", "furniture_redirection_plan.json")

carpet_redirections = {}
if os.path.exists(carpet_redirection_path):
    with open(carpet_redirection_path, "r", encoding="utf-8") as f:
        carpet_redirections = json.load(f)

furniture_redirections = {}
if os.path.exists(furniture_redirection_path):
    with open(furniture_redirection_path, "r", encoding="utf-8") as f:
        furniture_redirections = json.load(f)

# Combine redirection plans into a normalized lookup:
# normalized_plans[normalized_folder_name][normalized_filename] = (matched_sku, matched_name)
normalized_plans = {}

def normalize_fn(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', '’': '', '`': '', '\'': ''}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    # Remove extensions and copy numbers if present
    base, _ = os.path.splitext(text)
    base = re.sub(r'\s*\(\d+\)\s*$', '', base)
    base = re.sub(r'[-_]\s*copy\s*$', '', base)
    normalized = re.sub(r'[^a-z0-9]', '', base)
    return normalized

def build_normalized_redirections(plan_dict):
    for folder, files in plan_dict.items():
        norm_folder = normalize_fn(folder)
        if norm_folder not in normalized_plans:
            normalized_plans[norm_folder] = {}
        for fn, info in files.items():
            norm_fn = normalize_fn(fn)
            matched_sku = info.get("matched_sku")
            matched_name = info.get("matched_name")
            normalized_plans[norm_folder][norm_fn] = (matched_sku, matched_name)

build_normalized_redirections(carpet_redirections)
build_normalized_redirections(furniture_redirections)

# Normalize slugs for resolver
brand_keys = []
def norm_slug(name):
    return re.sub(r'[^a-z0-9]', '', name.lower().replace('ö', 'o').replace('ä', 'a').replace('å', 'a'))

def get_simple_norm(norm_val):
    val = re.sub(r'\d+x\d+', '', norm_val)
    val = re.sub(r'\d+cm', '', val)
    val = re.sub(r'\d+', '', val)
    colors = ['cm', 'ek', 'valnot', 'svart', 'vit', 'gra', 'natur', 'beige', 'gron', 'bla', 'morkgra', 'ljusgra', 'brun', 'guld', 'massing', 'silver', 'satin', 'creme']
    for color in colors:
        val = val.replace(color, '')
    return val

for slug, info in brand_sku_dict.items():
    norm_s = norm_slug(slug)
    norm_n = norm_slug(info.get('name', ''))
    brand_keys.append({
        'slug': slug,
        'sku': info['sku'],
        'name': info.get('name', ''),
        'norm_slug': norm_s,
        'norm_name': norm_n,
        'simple_norm_slug': get_simple_norm(norm_s),
        'simple_norm_name': get_simple_norm(norm_n)
    })

def clean_ref(filename):
    base = re.sub(r'^\d+_', '', filename)
    base, _ = os.path.splitext(base)
    base = re.sub(r'-1-26u-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1-26u$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-wonder$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-1$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-26u$', '', base, flags=re.IGNORECASE)
    return base

def get_beautiful_name(slug):
    return " ".join([w.capitalize() for w in slug.split('-') if w])

def normalize(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', '’': '', '`': '', '\'': ''}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def final_resolve_anchor(ref):
    ref_lower = ref.lower()
    
    # 1. Furniture overrides from rebuild_all_by_time.py
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
            
    # 2. Visual overrides for duplicate/mislabeled carpet source files
    if "2087_matta-seronis-svart-beige" in ref_lower:
        return "RG01-19", "Matta 'Aravelle' - Grå/Multi"
    if "2089_matta-sorvento-svart-beige" in ref_lower:
        return "RG01-499", "Matta 'Orlisse' - Brun"
    if "2104_matta-velenna-svart-beige" in ref_lower:
        return "RG01-64", "Matta 'Arvella' - Brun"
        
    is_carpet_file = "matta" in ref_lower or "rug" in ref_lower or "rg01" in ref_lower
    
    # 3. Try numeric prefix match (skip for carpets)
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
    
    # 4. Try direct SKU match
    cleaned = ref
    if cleaned.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
        cleaned = os.path.splitext(cleaned)[0]
    cleaned_base = clean_ref(ref)
    
    for bk in brand_keys:
        if bk['sku'].lower() == cleaned.lower() or bk['sku'].lower() == cleaned_base.lower():
            return bk['sku'], bk['name']
            
    # 5. Direct sku_map lookup
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
    
    # 6. Direct normalized match
    for bk in brand_keys:
        if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
            return bk['sku'], bk['name']
            
    # 7. Simple normalized match
    if simple_norm_c:
        for bk in brand_keys:
            if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
                return bk['sku'], bk['name']
                
    # 8. Substring match
    if len(norm_c) >= 4:
        for bk in brand_keys:
            if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
                return bk['sku'], bk['name']
                
    # 9. Simple substring match
    if len(simple_norm_c) >= 4:
        for bk in brand_keys:
            if bk['simple_norm_slug'] in simple_norm_c or simple_norm_c in bk['simple_norm_slug'] or bk['simple_norm_name'] in simple_norm_c or simple_norm_c in bk['simple_norm_name']:
                if len(bk['simple_norm_slug']) > 4 or len(bk['simple_norm_name']) > 4:
                    return bk['sku'], bk['name']
                    
    return None, get_beautiful_name(cleaned_base)

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def wipe_read_only_tree(path):
    if not os.path.exists(path):
        return
    for root, dirs, files in os.walk(path):
        for d in dirs:
            make_writable(os.path.join(root, d))
        for f in files:
            make_writable(os.path.join(root, f))
    try:
        shutil.rmtree(path)
    except Exception as e:
        print(f"Error cleaning {path}: {e}")

def find_reference_file_for_sku(sku, folder_name, original_ref_name=None):
    # 1. First search recursively for any file matching B's SKU
    sku_clean = sku.lower().strip()
    # Clean folder name: strip out parenthesized SKU and get words
    clean_name = folder_name.split(' (')[0].lower()
    # Replace Swedish characters and strip non-alphanumeric
    clean_name = re.sub(r'[^a-z0-9]', '', clean_name.replace('ö', 'o').replace('ä', 'a').replace('å', 'a'))
    
    for base_dir in REF_DIRS:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                f_lower = f.lower()
                # Direct SKU match in filename
                if sku_clean in f_lower:
                    return os.path.join(root, f)
                # Name match
                f_clean = re.sub(r'[^a-z0-9]', '', f_lower)
                if len(clean_name) >= 5 and (clean_name in f_clean or f_clean in clean_name):
                    return os.path.join(root, f)
                    
    # 2. Fallback to flat lookup of original_ref_name if provided
    if original_ref_name:
        ref_name_lower = original_ref_name.lower().strip()
        for base_dir in REF_DIRS:
            if not os.path.exists(base_dir):
                continue
            for f in os.listdir(base_dir):
                if f.lower().strip() == ref_name_lower:
                    return os.path.join(base_dir, f)
                f_base, _ = os.path.splitext(f.lower().strip())
                ref_base, _ = os.path.splitext(ref_name_lower)
                if f_base == ref_base:
                    return os.path.join(base_dir, f)
                    
    return None

def main():
    print("=== RUNNING FRESH VERIFICATION SORT (9463) ===")
    
    # Wipe target test directories first
    print("\nWiping test directories to ensure a 100% clean run...")
    wipe_read_only_tree(CLEAN_FURNITURE_ROOT)
    wipe_read_only_tree(CLEAN_CARPET_ROOT)
    wipe_read_only_tree(QUARANTINE_DIR)
    
    os.makedirs(CLEAN_FURNITURE_ROOT, exist_ok=True)
    os.makedirs(CLEAN_CARPET_ROOT, exist_ok=True)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    
    # 1. Load prompt database
    print(f"Loading database {prompt_db_path}...")
    with open(prompt_db_path, "r", encoding="utf-8") as f:
        prompt_data = json.load(f)
        
    db_by_index = {}
    for item in prompt_data:
        prompt_text = item.get("prompt", "")
        m = re.match(r"^(\d+)\s*-\s*", prompt_text)
        if m:
            idx = int(m.group(1))
            db_by_index[idx] = item
            
    print(f"Loaded {len(db_by_index)} prompt configurations from database.")
    
    # 2. Scan root folder for renders
    print(f"Scanning root directory {TURBOFLOW_ROOT} for files...")
    all_files = os.listdir(TURBOFLOW_ROOT)
    
    renders_to_process = []
    for f in all_files:
        path = os.path.join(TURBOFLOW_ROOT, f)
        if not os.path.isfile(path):
            continue
        m = re.match(r"^(\d+)", f)
        if m:
            idx = int(m.group(1))
            renders_to_process.append((idx, f, path))
            
    print(f"Found {len(renders_to_process)} render files in root directory to sort.")
    
    copied_count = 0
    ref_copied_count = 0
    quarantined_count = 0
    
    furniture_copied_count = 0
    carpet_copied_count = 0
    
    # Process each render file
    for idx, fname, src_path in sorted(renders_to_process, key=lambda x: x[0]):
        if idx not in db_by_index:
            quarantined_count += 1
            shutil.copy2(src_path, os.path.join(QUARANTINE_DIR, fname))
            continue
            
        db_entry = db_by_index[idx]
        image_refs_str = db_entry.get("image_references", "")
        image_refs = [r.strip() for r in image_refs_str.split(";") if r.strip()]
        
        if not image_refs:
            quarantined_count += 1
            shutil.copy2(src_path, os.path.join(QUARANTINE_DIR, fname))
            continue
            
        # Sorter maps image references:
        for ref_idx, ref in enumerate(image_refs):
            sku, beautiful_name = final_resolve_anchor(ref)
            is_primary = (ref_idx == 0)
            
            if not sku:
                continue
                
            if sku not in sku_catalog:
                continue
                
            catalog_entry = sku_catalog[sku]
            folder_name = catalog_entry["folder_name"]
            
            # Apply Redirection Override check
            norm_folder = normalize_fn(folder_name)
            norm_fname = normalize_fn(fname)
            
            target_sku = sku
            target_folder_name = folder_name
            
            if norm_folder in normalized_plans and norm_fname in normalized_plans[norm_folder]:
                override_sku, override_name = normalized_plans[norm_folder][norm_fname]
                if not override_sku:
                    # Mapped to NULL. Skipping sorting of this file to this category.
                    continue
                else:
                    target_sku = override_sku
                    if target_sku not in sku_catalog:
                        continue
                    target_catalog_entry = sku_catalog[target_sku]
                    target_folder_name = target_catalog_entry["folder_name"]
            
            # Determine target root
            if target_sku in carpet_skus:
                dest_root = CLEAN_CARPET_ROOT
                carpet_copied_count += 1
            else:
                dest_root = CLEAN_FURNITURE_ROOT
                furniture_copied_count += 1
                
            # Determine target directory
            if is_primary:
                target_dir = os.path.join(dest_root, target_folder_name)
            else:
                target_dir = os.path.join(dest_root, target_folder_name, "reserv")
                
            target_path = os.path.join(target_dir, fname)
            
            os.makedirs(target_dir, exist_ok=True)
            make_writable(target_dir)
            if os.path.exists(target_path):
                make_writable(target_path)
                os.remove(target_path)
            shutil.copy2(src_path, target_path)
            copied_count += 1
            
            # Handle reference photo
            ref_folder = os.path.join(dest_root, target_folder_name)
            _, ext = os.path.splitext(ref)
            ref_target_fn = f"00_REFERENCE_{target_sku}{ext}"
            ref_target_path = os.path.join(ref_folder, ref_target_fn)
            
            if not os.path.exists(ref_target_path):
                original_ref_path = find_reference_file_for_sku(target_sku, target_folder_name, ref)
                if original_ref_path and os.path.exists(original_ref_path):
                    os.makedirs(ref_folder, exist_ok=True)
                    make_writable(ref_folder)
                    shutil.copy2(original_ref_path, ref_target_path)
                    ref_copied_count += 1
                    
    print("\n" + "="*80)
    print("SUMMARY OF TEST KÖRNING:")
    print(f"  Total copies created: {copied_count}")
    print(f"    Furniture copies: {furniture_copied_count}")
    print(f"    Carpet copies: {carpet_copied_count}")
    print(f"  Reference photos copied: {ref_copied_count}")
    print(f"  Files quarantined: {quarantined_count}")
    print("\nTarget Directories:")
    print(f"  Furniture target: {CLEAN_FURNITURE_ROOT}")
    print(f"  Carpet target: {CLEAN_CARPET_ROOT}")
    print("="*80)

if __name__ == "__main__":
    main()
