import os
import sys
import json
import re
import shutil
import stat
from concurrent.futures import ThreadPoolExecutor, as_completed

# Directories and Paths
WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
TURBOFLOW_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
PICTURES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

CLEAN_FURNITURE_ROOT = os.path.join(TURBOFLOW_ROOT, "Reforma-Full-Catalog-sortering")
CLEAN_CARPET_ROOT = os.path.join(TURBOFLOW_ROOT, "Reforma-Mattor-sortering")
QUARANTINE_DIR = os.path.join(TURBOFLOW_ROOT, "_quarantine")

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
normalized_plans = {}

def normalize_fn(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', '’': '', '`': '', '\'': ''}
    for char, rep in repl.items():
        text = text.replace(char, rep)
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
    
    # 1. Furniture overrides
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
    
    # 1. Try numeric prefix match
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

    # 2. Try direct SKU match
    cleaned = ref
    if cleaned.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
        cleaned = os.path.splitext(cleaned)[0]
    cleaned_base = clean_ref(ref)
    
    for bk in brand_keys:
        if bk['sku'].lower() == cleaned.lower() or bk['sku'].lower() == cleaned_base.lower():
            return bk['sku'], bk['name']

    # 3. Direct sku_map lookup
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

    # 4. Direct normalized match
    for bk in brand_keys:
        if bk['norm_slug'] == norm_c or bk['norm_name'] == norm_c:
            return bk['sku'], bk['name']

    # 5. Simple normalized match
    if simple_norm_c:
        for bk in brand_keys:
            if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
                return bk['sku'], bk['name']

    # 6. Substring match
    if len(norm_c) >= 4:
        for bk in brand_keys:
            if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
                return bk['sku'], bk['name']

    # 7. Simple substring match
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

# In-memory reference cache
ref_cache = []

def build_ref_cache():
    global ref_cache
    ref_cache = []
    print("Scanning reference directories to build cache...")
    for base_dir in REF_DIRS:
        if not os.path.exists(base_dir):
            print(f"Warning: Reference directory does not exist: {base_dir}")
            continue
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                f_lower = f.lower()
                f_clean = re.sub(r'[^a-z0-9]', '', f_lower)
                ref_cache.append((os.path.join(root, f), f_lower, f_clean))
    print(f"Cached {len(ref_cache)} reference files.")

def find_reference_file_cached(sku, folder_name, original_ref_name=None):
    sku_clean = sku.lower().strip()
    clean_name = folder_name.split(' (')[0].lower()
    clean_name = re.sub(r'[^a-z0-9]', '', clean_name.replace('ö', 'o').replace('ä', 'a').replace('å', 'a'))
    
    # 1. Exact SKU match with boundary check
    for full_path, f_lower, f_clean in ref_cache:
        basename = os.path.basename(full_path).lower()
        if sku_clean in basename:
            if re.search(r'(?:\b|[^a-zA-Z0-9])' + re.escape(sku_clean) + r'(?:\b|[^a-zA-Z0-9])', basename):
                return full_path

    # 2. Substring SKU match
    for full_path, f_lower, f_clean in ref_cache:
        basename = os.path.basename(full_path).lower()
        if sku_clean in basename:
            return full_path

    # 3. Clean folder name match
    if len(clean_name) >= 5:
        for full_path, f_lower, f_clean in ref_cache:
            if clean_name in f_clean or f_clean in clean_name:
                return full_path
                
    # 4. Original ref name fallback
    if original_ref_name:
        ref_name_lower = original_ref_name.lower().strip()
        ref_base, _ = os.path.splitext(ref_name_lower)
        for full_path, f_lower, f_clean in ref_cache:
            f_name = os.path.basename(full_path).lower().strip()
            if f_name == ref_name_lower:
                return full_path
            f_b, _ = os.path.splitext(f_name)
            if f_b == ref_base:
                return full_path
                
    return None

def wipe_contents(path):
    if not os.path.exists(path):
        return
    print(f"Wiping contents of: {path}...")
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        make_writable(item_path)
        if os.path.isdir(item_path):
            for root, dirs, files in os.walk(item_path):
                for d in dirs:
                    make_writable(os.path.join(root, d))
                for f in files:
                    make_writable(os.path.join(root, f))
            try:
                shutil.rmtree(item_path)
            except Exception as e:
                print(f"Error deleting folder {item_path}: {e}")
        else:
            try:
                os.remove(item_path)
            except Exception as e:
                print(f"Error removing file {item_path}: {e}")

def get_folder_base_name(folder_name):
    base = re.sub(r'\s*\([^)]+\)\s*$', '', folder_name)
    base = re.sub(r'([a-zåäö])([A-ZÅÄÖ])', r'\1-\2', base)
    cleaned = []
    for char in base:
        if char.isalnum() or char in '-_':
            cleaned.append(char)
        else:
            cleaned.append('-')
    base = "".join(cleaned)
    base = re.sub(r'-+', '-', base)
    return base.strip('-')

def get_renamed_fname(folder_name, original_fname):
    base_name = get_folder_base_name(folder_name)
    base, ext = os.path.splitext(original_fname)
    base = re.sub(r'\s*\(\d+\)\s*$', '', base)
    base = re.sub(r'[-_]\s*copy\s*$', '', base, flags=re.IGNORECASE)
    
    first_m = re.match(r'^(\d+)', base)
    last_m = re.search(r'(\d+)$', base)
    if first_m and last_m:
        first_num = first_m.group(1)
        last_num = last_m.group(1)
        return f"{base_name}-{first_num}-{last_num}{ext}"
    else:
        clean_orig = re.sub(r'[\s\-_/\\|]+', '-', base)
        return f"{base_name}-{clean_orig.strip('-')}{ext}"

def process_product_folder(dest_root, folder_name, folder_data, dry_run):
    copied_renders = 0
    copied_refs = 0
    errors = []
    
    target_dir = os.path.join(dest_root, folder_name)
    reserv_dir = os.path.join(target_dir, "reserv")
    
    ops = []
    
    # Check if we should move reservs up: if there are no primaries
    should_move_reserv_up = len(folder_data['primaries']) == 0
    
    # Primaries
    for src_path, fname in folder_data['primaries']:
        new_fname = get_renamed_fname(folder_name, fname)
        dest_path = os.path.join(target_dir, new_fname)
        ops.append((src_path, dest_path, False))
        
    # Reservs
    for src_path, fname in folder_data['reservs']:
        new_fname = get_renamed_fname(folder_name, fname)
        if should_move_reserv_up:
            dest_path = os.path.join(target_dir, new_fname)
        else:
            dest_path = os.path.join(reserv_dir, new_fname)
        ops.append((src_path, dest_path, False))
        
    # References
    for target_sku, ref in folder_data['references']:
        _, ext = os.path.splitext(ref)
        ref_target_fn = f"00_REFERENCE_{target_sku}{ext}"
        ref_target_path = os.path.join(target_dir, ref_target_fn)
        
        original_ref_path = find_reference_file_cached(target_sku, folder_name, ref)
        if original_ref_path and os.path.exists(original_ref_path):
            ops.append((original_ref_path, ref_target_path, True))
        else:
            errors.append(f"Could not find reference photo for SKU {target_sku} ({ref}) in cache.")
            
    if not dry_run:
        try:
            if folder_data['primaries'] or folder_data['references'] or should_move_reserv_up:
                os.makedirs(target_dir, exist_ok=True)
                make_writable(target_dir)
            if folder_data['reservs'] and not should_move_reserv_up:
                os.makedirs(reserv_dir, exist_ok=True)
                make_writable(reserv_dir)
                
            for src, dest, is_ref in ops:
                success = False
                last_err = None
                for attempt in range(3):
                    try:
                        if os.path.exists(dest):
                            make_writable(dest)
                            os.remove(dest)
                        shutil.copy2(src, dest)
                        success = True
                        break
                    except Exception as e:
                        last_err = e
                        import time
                        time.sleep(0.5)
                        
                if success:
                    if is_ref:
                        copied_refs += 1
                    else:
                        copied_renders += 1
                else:
                    errors.append(f"Failed to copy {os.path.basename(src)} to {os.path.basename(dest)}: {last_err}")
        except Exception as e:
            errors.append(f"Folder processing error for {folder_name}: {e}")
    else:
        for src, dest, is_ref in ops:
            if is_ref:
                copied_refs += 1
            else:
                copied_renders += 1
                
    return copied_renders, copied_refs, errors

def main():
    dry_run = "--run" not in sys.argv
    if dry_run:
        print("="*80)
        print("DRY-RUN MODE ACTIVE. To execute real file operations, run:")
        print("  python scratch/execute_safe_deterministic_sort.py --run")
        print("="*80)
    else:
        print("="*80)
        print("RUNNING LIVE DETERMINISTIC SORT AND REFERENCE COPY OPERATIONS...")
        print("="*80)

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
            
    print(f"Loaded {len(db_by_index)} prompt configurations.")

    # 2. Build Reference Cache
    build_ref_cache()

    # 3. Scan root folder for renders
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
            
    print(f"Found {len(renders_to_process)} render files in root directory.")
    
    # 4. Map files to product folder targets
    product_folders = {}
    quarantine_tasks = []
    
    for idx, fname, src_path in sorted(renders_to_process, key=lambda x: x[0]):
        if idx not in db_by_index:
            quarantine_tasks.append((src_path, fname))
            continue
            
        db_entry = db_by_index[idx]
        image_refs_str = db_entry.get("image_references", "")
        image_refs = [r.strip() for r in image_refs_str.split(";") if r.strip()]
        
        if not image_refs:
            quarantine_tasks.append((src_path, fname))
            continue
            
        for ref_idx, ref in enumerate(image_refs):
            sku, beautiful_name = final_resolve_anchor(ref)
            is_primary = (ref_idx == 0)
            
            if not sku:
                continue
            if sku not in sku_catalog:
                continue
                
            catalog_entry = sku_catalog[sku]
            folder_name = catalog_entry["folder_name"]
            
            norm_folder = normalize_fn(folder_name)
            norm_fname = normalize_fn(fname)
            
            target_sku = sku
            target_folder_name = folder_name
            
            if norm_folder in normalized_plans and norm_fname in normalized_plans[norm_folder]:
                override_sku, override_name = normalized_plans[norm_folder][norm_fname]
                if not override_sku:
                    continue
                else:
                    target_sku = override_sku
                    if target_sku not in sku_catalog:
                        continue
                    target_catalog_entry = sku_catalog[target_sku]
                    target_folder_name = target_catalog_entry["folder_name"]
            
            # Determine target root (all products go to furniture root per user request)
            dest_root = CLEAN_FURNITURE_ROOT
                
            folder_key = (dest_root, target_folder_name)
            if folder_key not in product_folders:
                product_folders[folder_key] = {
                    'primaries': set(),
                    'reservs': set(),
                    'references': set()
                }
                
            if is_primary:
                product_folders[folder_key]['primaries'].add((src_path, fname))
            else:
                product_folders[folder_key]['reservs'].add((src_path, fname))
                
            product_folders[folder_key]['references'].add((target_sku, ref))

    # 5. Wipe contents if not dry run
    if not dry_run:
        wipe_contents(CLEAN_FURNITURE_ROOT)
        wipe_contents(CLEAN_CARPET_ROOT)

    # 6. Parallelize folder operations
    copied_renders = 0
    copied_refs = 0
    quarantined_count = 0
    all_errors = []
    
    print(f"Submitting {len(product_folders)} product folders to ThreadPoolExecutor...")
    
    # Use 12 parallel threads to balance disk IO, network hydration, and sync
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {}
        for (dest_root, folder_name), folder_data in product_folders.items():
            f = executor.submit(process_product_folder, dest_root, folder_name, folder_data, dry_run)
            futures[f] = folder_name
            
        for future in as_completed(futures):
            folder_name = futures[future]
            try:
                renders, refs, errors = future.result()
                copied_renders += renders
                copied_refs += refs
                if errors:
                    all_errors.extend(errors)
                    print(f"  Folder {folder_name} finished with errors.")
            except Exception as e:
                all_errors.append(f"Thread execution error for {folder_name}: {e}")
                print(f"  Folder {folder_name} crashed: {e}")

    # 7. Process quarantine tasks
    if quarantine_tasks:
        print(f"Processing {len(quarantine_tasks)} quarantine tasks...")
        if not dry_run:
            os.makedirs(QUARANTINE_DIR, exist_ok=True)
            make_writable(QUARANTINE_DIR)
        for src_path, fname in quarantine_tasks:
            dest_path = os.path.join(QUARANTINE_DIR, fname)
            if not dry_run:
                try:
                    if os.path.exists(dest_path):
                        make_writable(dest_path)
                        os.remove(dest_path)
                    shutil.copy2(src_path, dest_path)
                    quarantined_count += 1
                except Exception as e:
                    all_errors.append(f"Failed to copy quarantine file {fname}: {e}")
            else:
                quarantined_count += 1

    print("\n" + "="*80)
    print("SUMMARY OF OPERATIONS:")
    print(f"  Renders copied: {copied_renders}")
    print(f"  Reference photos copied: {copied_refs}")
    print(f"  Files quarantined: {quarantined_count}")
    if all_errors:
        print(f"  Total Errors encountered: {len(all_errors)}")
        print("  Error details:")
        for err in all_errors[:20]: # Print first 20 errors
            print(f"    - {err}")
        if len(all_errors) > 20:
            print(f"    - ... and {len(all_errors)-20} more errors.")
    else:
        print("  No errors occurred!")
    print("="*80)

if __name__ == "__main__":
    main()
