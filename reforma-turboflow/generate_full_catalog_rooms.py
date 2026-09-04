import os
import sys
import json
import csv
import re
from typing import Dict, Any, List, Tuple

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\furniture_db.json"
EXPORT_JSON_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_full_catalog.json"
CSV_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\turboflow_ready_full_catalog.csv"
FLAT_JSON_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\turboflow_ready_full_catalog.json"
TXT_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\turboflow_ready_full_catalog.txt"
PROMPTS_ONLY_EXPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\prompts_only_full_catalog.txt"
TRACKING_LOG_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\turboflow_tracking_log_full_catalog.csv"

CAT_KEY = 'typ_av_m\u00f6bel'
WOOD_KEY = 'tr\u00e4slag'
MAT_KEY = 'tyg_material'
TONE_KEY = 'f\u00e4rgton'
STYLE_KEY = 'stil_estetik'

def clean_str(s: str) -> str:
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
    for c, r in repl.items():
        s = s.replace(c, r)
    return s.lower()

def normalize_strict(s: str) -> str:
    s = s.lower().strip()
    s = os.path.splitext(s)[0]
    
    prev = ""
    while s != prev:
        prev = s
        s = re.sub(r'^\d+[_-]', '', s)
        
    s = re.sub(r'-\d+-\w+-wonder$', '', s)
    s = re.sub(r'-\d+-\w+$', '', s)
    s = re.sub(r'-\d+$', '', s)
    s = re.sub(r'-wonder$', '', s)
    s = re.sub(r'-26u$', '', s)
    
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'o', 'Ä': 'a', 'Å': 'a',
        'é': 'e', 'pinnstol': 'stol', 'fatolj': 'fotolj',
        'fåtölj': 'fotolj', 'fõtõlj': 'fotolj', 'fötölj': 'fotolj'
    }
    for char, rep in replacements.items():
        s = s.replace(char, rep)
    s = re.sub(r'[^a-z0-9]', '', s)
    return s



# Load exclusions
try:
    with open('exclude_list.json', 'r', encoding='utf-8') as f:
        exclude_list = set(json.load(f))
except:
    exclude_list = set()

def should_skip_item(filename: str) -> bool:
    if filename in exclude_list:
        return True

    fname = filename.lower()
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    cleaned_fname = clean_str(fname)
    for kw in skip_keywords:
        if kw in fname or clean_str(kw) in cleaned_fname:
            return True
    return False

def get_rug_description(rug_item: Dict, with_form: bool = False) -> str:
    rug_name = clean_tag_to_name(rug_item["filename"])
    rug_mat = rug_item.get("metadata", {}).get(MAT_KEY, "").strip().lower()
    
    mat_map = {
        "ull": "wool",
        "bomull": "cotton",
        "jute": "jute",
        "viskos": "viscose",
        "polyester": "polyester",
        "polypropen": "polypropylene",
        "syntet": "synthetic",
        "textil": "textile"
    }
    
    eng_mat = ""
    if rug_mat and rug_mat != "inget" and rug_mat != "textil":
        eng_mat = mat_map.get(rug_mat, rug_mat)
        
    form_desc = ""
    if with_form:
        rug_form = rug_item.get("metadata", {}).get("form", "").strip().lower()
        if not rug_form:
            if any(x in rug_item["filename"].lower() for x in ["runt", "rund", "cirkel", "cirkular", "round"]):
                rug_form = "round"
            else:
                rug_form = "rectangular"
        else:
            rug_form = "round" if rug_form == "rund" else "rectangular"
        form_desc = f"{rug_form} "
        
    if eng_mat:
        return f"matching {eng_mat} rug ({rug_name})" if not with_form else f"matching real {form_desc}{eng_mat} area rug ({rug_name})"
    else:
        return f"matching rug ({rug_name})" if not with_form else f"matching real {form_desc}area rug ({rug_name})"

def get_short_tag(filename: str) -> str:
    """
    Generates the exact Turboflow autotag based on the filename,
    simulating UTF-8 bytes read as CP1252 with ASCII-only sanitization and 20-character truncation.
    """
    fn_bytes = filename.encode('utf-8')
    fn_corrupted = fn_bytes.decode('cp1252', errors='ignore').lower()
    base, _ = os.path.splitext(fn_corrupted)
    cleaned = ''.join(c if re.match(r'[a-z0-9_-]', c) else '-' for c in base)
    collapsed = re.sub(r'-+', '-', cleaned)
    truncated = collapsed[:20].strip('-')
    return f"@{truncated}"

def clean_swedish_chars(text: str) -> str:
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text

def clean_tag_to_name(filename: str, include_dimensions: bool = False) -> str:
    base, _ = os.path.splitext(filename)
    base = re.sub(r'^\d+__*', '', base)
    base = re.sub(r'^\d+_', '', base)
    base = re.sub(r'-\d+-\w+-wonder$', '', base)
    base = re.sub(r'-\d+$', '', base)
    base = base.replace("-", " ").replace("_", " ").title()
    return clean_swedish_chars(base)

def get_item_category(filename: str, item: Dict) -> str:
    fname = filename.lower()
    cat_meta = item.get("metadata", {}).get(CAT_KEY, "").strip().lower()
    
    if "taklampa" in fname:
        return "pendant_lamp"
    elif "golvlampa" in fname:
        return "floor_lamp"
    elif "bordslampa" in fname or "lampa" in fname:
        return "table_lamp"
    
    if cat_meta == "matta" or "matta" in fname:
        return "rug"
        
    if "skrivbordsstol" in fname:
        return "desk_chair"
        
    if "barstol" in fname or ("bar" in fname and "stol" in fname):
        return "barstool"
    elif "barbord" in fname:
        return "bartable"
        
    if "f\u00e5t\u00f6lj" in fname or "fatolj" in fname:
        return "armchair"
    elif "b\u00e4ddsoffa" in fname or "soffa" in fname:
        return "sofa"
    elif "soffbord" in fname:
        return "coffeetable"
    elif "s\u00e4ngbord" in fname or "sangbord" in fname:
        return "bedside_table"
    elif "skrivbord" in fname:
        return "desk"
    elif "klaffbord" in fname or "matbord" in fname:
        return "dining_table"
    elif "bord" in fname:
        if "avlastningsbord" in fname or "sidobord" in fname or "sideboard" in fname:
            return "sideboard"
        return "dining_table"
        
    if "tv-b\u00e4nk" in fname or "tv-b\u00f6nk" in fname or "mediab\u00e4nk" in fname:
        return "tv_bench"
    elif "b\u00e4nk" in fname or "bank" in fname:
        return "bench"
    elif "bokhylla" in fname:
        return "bookcase"
    elif "byr\u00e5" in fname:
        return "dresser"
    elif "skosk\u00e5p" in fname:
        return "shoe_cabinet"
    elif "sk\u00e5p" in fname or "sk\u00e4nk" in fname or "sideboard" in fname or "sidobord" in fname or "avlastningsbord" in fname:
        return "cabinet"
        
    if cat_meta == "stol" or "stol" in fname or "pinnstol" in fname or "karmstol" in fname:
        return "dining_chair"
        
    if cat_meta == "f\u00f6rvaring" or cat_meta == "frvaring" or "hylla" in fname:
        return "cabinet"
        
    if cat_meta == "stol":
        return "dining_chair"
    elif cat_meta == "bord":
        return "dining_table"
    elif cat_meta == "matta":
        return "rug"
    return "other"

def woods_harmonize(w1: str, w2: str) -> bool:
    if not w1 or not w2: return True
    w1, w2 = w1.strip().lower(), w2.strip().lower()
    if w1 == w2: return True
    if w1 == 'inget' or w2 == 'inget':
        return True
    neutrals = {'svart metall', 'marmor', 'vit', 'svart ek', 'svart', 'metall'}
    if w1 in neutrals or w2 in neutrals:
        return True
    light_woods = {'ek', 'ask', 'natur', 'ljus ek', 'vitlaserad ek'}
    dark_woods = {'valnöt', 'mörkbrun', 'mörk ek', 'brunt trä'}
    if w1 in light_woods and w2 in light_woods:
        return True
    if w1 in dark_woods and w2 in dark_woods:
        return True
    if w1 == 'furu' and w2 in dark_woods:
        return False
    if w2 == 'furu' and w1 in dark_woods:
        return False
    if w1 == 'furu' or w2 == 'furu':
        return True
    return False
    if w2 == 'furu' and w1 in dark_woods:
        return False
    if w1 == 'furu' or w2 == 'furu':
        return True
    return False

usage_counts = {}
current_allowed_items = {}

def recount_usages(packages, db):
    for k in db.keys():
        usage_counts[k] = 0
    for pkg in packages:
        for slot, item in pkg.items():
            if slot not in ['room_type', 'relax_level', 'seed'] and item is not None:
                fn = item['filename']
                usage_counts[fn] = usage_counts.get(fn, 0) + 1

def find_matching_companion(cats_to_search, items_by_cat, unfeatured_ids, exclude_ids, anchor_item, relax_level, allowed_ids=None):
    candidates = []
    for cat in cats_to_search:
        candidates.extend(items_by_cat.get(cat, []))
    import random
    random.shuffle(candidates)

        
    anchor_style = anchor_item["metadata"].get(STYLE_KEY)
    anchor_tone = anchor_item["metadata"].get(TONE_KEY)
    anchor_wood = anchor_item["metadata"].get(WOOD_KEY)
    
    # Sort candidates prioritizing: unfeatured first, then lowest usage count first
    def sort_key(x):
        is_unfeatured = x["filename"] in unfeatured_ids
        usage = usage_counts.get(x["filename"], 0)
        return (0 if is_unfeatured else 1, usage, x["filename"])
        
    sorted_candidates = sorted(candidates, key=sort_key)
    
    for item in sorted_candidates:
        if item["filename"] in exclude_ids:
            continue
            
        # Rolling window filters for all companion categories
        item_cat = get_item_category(item["filename"], item)
        allowed = allowed_ids if allowed_ids is not None else current_allowed_items.get(item_cat)
        if allowed is not None and item["filename"] not in allowed:
            continue
            
        is_unfeatured = item["filename"] in unfeatured_ids
        
        # Extract metadata
        i_style = item["metadata"].get(STYLE_KEY)
        i_tone = item["metadata"].get(TONE_KEY)
        i_wood = item["metadata"].get(WOOD_KEY)
        
        # Match variables
        style_ok = i_style == anchor_style
        tone_ok = i_tone == anchor_tone
        wood_ok = woods_harmonize(anchor_wood, i_wood)
        
        # Shape constraint for rugs
        if "rug" in cats_to_search and relax_level < 8:
            anchor_cat = get_item_category(anchor_item["filename"], anchor_item)
            if anchor_cat in ["dining_table", "coffeetable"]:
                is_table_round = any(x in anchor_item["filename"].lower() for x in ["runt", "rund", "cirkel", "cirkular", "round"])
                rug_form = item["metadata"].get("form", "").strip().lower()
                is_rug_round = rug_form == "rund" or any(x in item["filename"].lower() for x in ["runt", "rund", "cirkel", "cirkular", "round"])
                if is_table_round != is_rug_round:
                    continue
        
        # 10 relaxation levels:
        if relax_level == 0:
            if is_unfeatured and style_ok and tone_ok and wood_ok:
                return item
        elif relax_level == 1:
            if style_ok and tone_ok and wood_ok:
                return item
        elif relax_level == 2:
            if is_unfeatured and style_ok and wood_ok:
                return item
        elif relax_level == 3:
            if style_ok and wood_ok:
                return item
        elif relax_level == 4:
            if is_unfeatured and tone_ok and wood_ok:
                return item
        elif relax_level == 5:
            if tone_ok and wood_ok:
                return item
        elif relax_level == 6:
            if is_unfeatured and wood_ok:
                return item
        elif relax_level == 7:
            if wood_ok:
                return item
        elif relax_level == 8:
            if is_unfeatured:
                return item
        elif relax_level == 9:
            return item
            
    return None

def fill_empty_slots(pkg, items_by_cat, unfeatured_ids, allowed_rug_ids=None):
    room_type = pkg["room_type"]
    anchor_item = pkg["seed"]
    
    slots_by_room = {
        "dining": [],
        "living_seating": [
            ("sofa", ["sofa"]),
            ("armchair", ["armchair"])
        ],
        "living_storage": [
            ("armchair", ["armchair"]),
            ("rug", ["rug"])
        ],
        "office": [
            ("desk_chair", ["desk_chair", "dining_chair", "armchair"])
        ],
        "bedroom": [
            ("bed", ["sofa"]),
            ("rug", ["rug"])
        ],
        "bar": [
            ("bartable", ["bartable", "dining_table"]),
            ("rug", ["rug"])
        ]
    }
    
    if room_type not in slots_by_room:
        return
        
    slots = slots_by_room[room_type]
    for slot_name, cats in slots:
        if pkg.get(slot_name) is None:
            for relax in range(10):
                exclude = {item["filename"] for slot, item in pkg.items() if slot not in ["room_type", "relax_level", "seed"] and item is not None}
                exclude.add(anchor_item["filename"])
                comp = find_matching_companion(cats, items_by_cat, unfeatured_ids, exclude, anchor_item, relax, allowed_rug_ids)
                if comp:
                    pkg[slot_name] = comp
                    break

def join_background_elements(elements: List[str], close_up: bool) -> str:
    if not elements:
        return ""
    prefix = "In the soft-focus background, " if close_up else "In the background, "
    suffix = " is softly visible" if close_up else " is visible"
    plural_suffix = " are softly visible" if close_up else " are visible"
    
    if len(elements) == 1:
        return f"{prefix}{elements[0]}{suffix}."
    elif len(elements) == 2:
        return f"{prefix}{elements[0]} and {elements[1]}{plural_suffix}."
    else:
        joined = ", ".join(elements[:-1]) + f", and {elements[-1]}"
        return f"{prefix}{joined}{plural_suffix}."

def main():
    global current_allowed_items
    print("==================================================")
    print("       STARTING BATCH 1 CURATION ENGINE           ")
    print("==================================================")
    print("Loading entire catalog...")
    with open('brand_sku_dict.json', 'r', encoding='utf-8') as f:
        brand_db = json.load(f)
    
    # We actually need the rich metadata from furniture_db and furniture_db_batch2
    db = {}
    for db_file in ['furniture_db.json', 'furniture_db_batch2.json', 'furniture_db_batch3.json']:
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                temp_db = json.load(f)
                for k, v in temp_db.items():
                    db[k] = v
        except Exception as e:
            print('Could not load', db_file)
            
    # If any brand items are missing, add them
    existing_normalized = set()
    for key, item in db.items():
        existing_normalized.add(normalize_strict(key))
        existing_normalized.add(normalize_strict(clean_tag_to_name(key)))
        if item.get('metadata') and item['metadata'].get('title'):
            existing_normalized.add(normalize_strict(item['metadata']['title']))

    for k, v in brand_db.items():
        norm_k = normalize_strict(k)
        norm_name = normalize_strict(v.get('name', '')) if v.get('name') else ''
        
        is_existing = (norm_k in existing_normalized) or (norm_name and norm_name in existing_normalized)
        if not is_existing:
            db[k] = {'metadata': {}, 'url': v.get('url'), 'filename': k}
            existing_normalized.add(norm_k)
            if norm_name:
                existing_normalized.add(norm_name)
            
    # Build a physical image file index from active/search folders
    search_dirs = [
        r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ",
        r"C:\Users\AndronikLindgren\reforma_automation\reforma_arkiv",
        r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\test_furniture",
        r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\new_rugs",
        r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\test_rugs",
        r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\downloaded_missing_images"
    ]
    onedrive_pictures_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
    if os.path.exists(onedrive_pictures_dir):
        for entry in os.listdir(onedrive_pictures_dir):
            if entry.lower().startswith("turboflow_batch"):
                full_path = os.path.join(onedrive_pictures_dir, entry)
                if os.path.isdir(full_path):
                    search_dirs.append(full_path)

    image_index = {}
    for search_dir in search_dirs:
        if not os.path.exists(search_dir): continue
        for root, dirs, files in os.walk(search_dir):
            if "batch" in root.lower() and "_images" in root.lower(): continue
            for file in files:
                if file.endswith(('.png', '.webp', '.jpg', '.jpeg')):
                    if file not in image_index:
                        image_index[file] = os.path.join(root, file)
    image_index_lower = {k.lower(): v for k, v in image_index.items()}

    # Load sku_map.json
    sku_map_path = os.path.join(r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow", "sku_map.json")
    slug_to_filenames = {}
    sku_to_filenames = {}
    if os.path.exists(sku_map_path):
        try:
            with open(sku_map_path, 'r', encoding='utf-8') as f:
                sku_map = json.load(f)
            for filename, info in sku_map.items():
                slug = info.get('slug')
                sku = info.get('sku')
                if slug:
                    slug_to_filenames.setdefault(slug.lower(), []).append(filename)
                if sku:
                    sku_to_filenames.setdefault(sku.lower(), []).append(filename)
        except Exception as e:
            print("Warning: Failed to load sku_map.json:", e)

    # Resolve each key in db to its actual physical filename if present
    resolved_db = {}
    resolved_count = 0
    for k, v in db.items():
        resolved_name = k
        match_src = image_index.get(k) or image_index_lower.get(k.lower())
        if not match_src:
            mapped_files = slug_to_filenames.get(k.lower()) or sku_to_filenames.get(k.lower())
            if mapped_files:
                for mapped_file in mapped_files:
                    if mapped_file in image_index:
                        match_src = image_index[mapped_file]
                        break
                    base_mapped = os.path.splitext(mapped_file)[0]
                    for ext in ['.png', '.webp', '.jpg', '.jpeg']:
                        alt_name = base_mapped + ext
                        if alt_name in image_index:
                            match_src = image_index[alt_name]
                            break
                    if match_src:
                        break
        
        if not match_src:
            norm_k = normalize_strict(k)
            for img_name in image_index:
                if norm_k == normalize_strict(img_name):
                    match_src = image_index[img_name]
                    break
                    
        if match_src:
            resolved_name = os.path.basename(match_src)
            if resolved_name != k:
                resolved_count += 1
                
        v["filename"] = resolved_name
        resolved_db[resolved_name] = v
    db = resolved_db
    print(f"Resolved {resolved_count} database keys to physical filenames using disk index and sku_map.")
            
    def get_base_slug(filename):
        base = re.sub(r'^\d+[_-]', '', filename)
        base = re.sub(r'\.(jpg|jpeg|png|webp)$', '', base, flags=re.IGNORECASE)
        base = re.sub(r'-\d+-\w+-wonder$', '', base)
        base = re.sub(r'-\d+$', '', base)
        return base
        
    def get_num(fname):
        m = re.search(r'-(\d+)(?:-\w+-wonder)?\.[a-z]+$', fname, flags=re.IGNORECASE)
        if m:
            return int(m.group(1))
        return 0

    grouped_db = {}
    for k in db:
        base = get_base_slug(k)
        grouped_db.setdefault(base, []).append(k)

    primary_db = {}
    for base, keys in grouped_db.items():
        def get_id_prefix(fname):
            m = re.match(r'^(\d+)_', fname)
            if m:
                return int(m.group(1))
            return 0
        best_key = sorted(keys, key=lambda x: (get_num(x), -get_id_prefix(x), x.lower()))[0]
        primary_db[best_key] = db[best_key]
        
    def norm(s):
        return s.replace('', '').encode('ascii', 'ignore').decode('ascii').lower()
        
    ex_norm = {norm(item) for item in exclude_list}

    print(f"Reduced {len(db)} total variants to {len(primary_db)} primary products.")
    
    # Now filter the primary products using should_skip_item and done_titles
    done_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"
    done_titles = set()
    if os.path.exists(done_dir):
        for name in os.listdir(done_dir):
            if os.path.isdir(os.path.join(done_dir, name)):
                done_titles.add(norm(name))
                
    filtered_db = {}
    for k, v in primary_db.items():
        if norm(k) in ex_norm:
            continue
        title = clean_tag_to_name(k)
        if norm(title) not in done_titles:
            filtered_db[k] = v
            
    print(f"Filtered out {len(primary_db) - len(filtered_db)} products that were excluded or already generated.")
    db = filtered_db
        
    # Initialize usage counts
    for k in db.keys():
        usage_counts[k] = 0
    
    # Load all items that appeared in the 1150 generated images to exclude them from the companion pool
    used_in_generated_norm = set()
    turboflow_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
    master_yesterday_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\turboflow_ready_yesterday.json"
    
    if os.path.exists(turboflow_dir) and os.path.exists(master_yesterday_path):
        try:
            generated_indices = set()
            for filename in os.listdir(turboflow_dir):
                if filename.endswith(".png"):
                    m = re.match(r"^(\d+)-architectural", filename)
                    if m:
                        n = int(m.group(1))
                        generated_indices.add(n - 1)
            
            with open(master_yesterday_path, 'r', encoding='utf-8') as f:
                master_yesterday_db = json.load(f)
            
            for idx in generated_indices:
                if idx < len(master_yesterday_db):
                    row = master_yesterday_db[idx]
                    refs = [r.strip() for r in row.get("image_references", "").split(";") if r.strip()]
                    for r in refs:
                        used_in_generated_norm.add(normalize_strict(r))
            print(f"Extracted {len(used_in_generated_norm)} normalized companion exclusions from {len(generated_indices)} generated images.")
        except Exception as e:
            print(f"Warning: Failed to extract companion exclusions: {e}")

    items_by_cat = {}
    excluded_companions_count = 0
    for filename, item in primary_db.items():
        item["filename"] = filename
        if normalize_strict(filename) in used_in_generated_norm:
            excluded_companions_count += 1
            continue
        cat = get_item_category(filename, item)
        items_by_cat[cat] = items_by_cat.get(cat, []) + [item]
    print(f"Excluded {excluded_companions_count} items from the companion pool because they were already generated yesterday.")

        
    unfeatured_ids = set(db.keys())
    packages = []
    
    # Define window sizes for all companion categories
    window_sizes = {
        "rug": 20,
        "dining_chair": 8,
        "armchair": 6,
        "coffeetable": 6,
        "dining_table": 6,
        "tv_bench": 3,
        "cabinet": 3,
        "dresser": 3,
        "sideboard": 3,
        "bookcase": 3,
        "shoe_cabinet": 3,
        "bedside_table": 3,
        "table_lamp": 3,
        "pendant_lamp": 3,
        "floor_lamp": 2,
        "desk": 3,
        "desk_chair": 3,
        "sofa": 6,
        "barstool": 6,
        "bartable": 2
    }

    # Precompute items lists for each category
    items_by_cat_lists = {}
    for cat in window_sizes.keys():
        items_by_cat_lists[cat] = sorted(list({item["filename"] for item in items_by_cat.get(cat, [])}))

    def get_allowed_items_for_idx(idx):
        allowed_map = {}
        batch_size = 600  # Shift allowed companions every 600 prompts (150 seeds)
        batch_idx = idx // batch_size
        shift = 20  # Shift by 20 to get fresh companion choices for the next batch
        for cat, w in window_sizes.items():
            items_list = items_by_cat_lists.get(cat, [])
            n = len(items_list)
            if n == 0:
                continue
            start_idx = (batch_idx * shift) % n
            allowed = set()
            for offset in range(w):
                allowed.add(items_list[(start_idx + offset) % n])
            allowed_map[cat] = allowed
        return allowed_map

    # Group seeds: all furniture seeds first, then all rug seeds, with 10 consecutive repetitions each
    furniture_seeds = [s for s in db.keys() if get_item_category(s, db[s]) != "rug"]
    rug_seeds = [s for s in db.keys() if get_item_category(s, db[s]) == "rug"]
    
    seeds = []
    for s in sorted(furniture_seeds):
        seeds.extend([s] * 10)
    for s in sorted(rug_seeds):
        seeds.extend([s] * 10)
    
    for seed_id in seeds:
        current_allowed_items = get_allowed_items_for_idx(len(packages))
        if not unfeatured_ids:
            unfeatured_ids = set(db.keys())
            
        seed_item = db[seed_id]
        seed_cat = get_item_category(seed_id, seed_item)
        
        # Determine room template based on seed category
        if seed_cat in ["dining_table", "dining_chair", "pendant_lamp"]:
            room_type = "dining"
        elif seed_cat in ["sofa", "armchair", "coffeetable", "floor_lamp"]:
            room_type = "living_seating"
        elif seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard", "table_lamp", "bench"]:
            room_type = "living_storage"
        elif seed_cat in ["desk", "desk_chair"]:
            room_type = "office"
        elif seed_cat == "bedside_table":
            room_type = "bedroom"
        elif seed_cat in ["barstool", "bartable"]:
            room_type = "bar"
        else: # rug or other
            room_type = "dining"
            
        matched_pkg = None
        for relax in range(10):
            exclude_ids = {seed_id}
            pkg = {"seed": seed_item, "room_type": room_type, "relax_level": relax}
            
            if room_type == "dining":
                dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dt: exclude_ids.add(dt["filename"])
                
                dc = seed_item if seed_cat == "dining_chair" else find_matching_companion(["dining_chair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dc: exclude_ids.add(dc["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, dt if dt else seed_item, relax)
                if rug: exclude_ids.add(rug["filename"])
                
                pl = seed_item if seed_cat == "pendant_lamp" else None
                if pl: exclude_ids.add(pl["filename"])
                
                bg = find_matching_companion(["cabinet", "dresser", "sideboard", "bookcase"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bg: exclude_ids.add(bg["filename"])
                
                if dt and dc and rug:
                    pkg.update({"dining_table": dt, "dining_chair": dc, "rug": rug, "pendant_lamp": pl, "background_storage": bg})
                    matched_pkg = pkg
                    break
                    
            elif room_type == "living_seating":
                sofa = seed_item if seed_cat == "sofa" else find_matching_companion(["sofa"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if sofa: exclude_ids.add(sofa["filename"])
                
                ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ac: exclude_ids.add(ac["filename"])
                
                ct = seed_item if seed_cat == "coffeetable" else find_matching_companion(["coffeetable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ct: exclude_ids.add(ct["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if rug: exclude_ids.add(rug["filename"])
                
                fl = seed_item if seed_cat == "floor_lamp" else None
                if fl: exclude_ids.add(fl["filename"])
                
                bg = find_matching_companion(["cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bg: exclude_ids.add(bg["filename"])
                
                if sofa and ct and rug:
                    pkg.update({"sofa": sofa, "armchair": ac, "coffeetable": ct, "rug": rug, "floor_lamp": fl, "background_storage": bg})
                    matched_pkg = pkg
                    break
                    
            elif room_type == "living_storage":
                ps = seed_item if seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard"] else find_matching_companion(["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ps: exclude_ids.add(ps["filename"])
                
                ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ac: exclude_ids.add(ac["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if rug: exclude_ids.add(rug["filename"])
                
                tl = seed_item if seed_cat == "table_lamp" else None
                if tl: exclude_ids.add(tl["filename"])
                
                # Solid match requires primary storage and a matching rug!
                if ps and rug:
                    pkg.update({"primary_storage": ps, "armchair": ac, "rug": rug, "table_lamp": tl})
                    matched_pkg = pkg
                    break
                    
            elif room_type == "office":
                desk = seed_item if seed_cat == "desk" else find_matching_companion(["desk"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if desk: exclude_ids.add(desk["filename"])
                
                dc = find_matching_companion(["desk_chair", "dining_chair", "armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dc: exclude_ids.add(dc["filename"])
                
                bc = find_matching_companion(["bookcase", "cabinet", "dresser"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bc: exclude_ids.add(bc["filename"])
                
                tl = seed_item if seed_cat == "table_lamp" else None
                if tl: exclude_ids.add(tl["filename"])
                
                # Solid match requires desk and desk chair!
                if desk and dc:
                    pkg.update({"desk": desk, "desk_chair": dc, "bookcase": bc, "table_lamp": tl})
                    matched_pkg = pkg
                    break
                    
            elif room_type == "bedroom":
                bst = seed_item if seed_cat == "bedside_table" else find_matching_companion(["bedside_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bst: exclude_ids.add(bst["filename"])
                
                bed = find_matching_companion(["sofa"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bed: exclude_ids.add(bed["filename"])
                
                dr = find_matching_companion(["dresser", "cabinet"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dr: exclude_ids.add(dr["filename"])
                
                tl = seed_item if seed_cat == "table_lamp" else None
                if tl: exclude_ids.add(tl["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if rug: exclude_ids.add(rug["filename"])
                
                # Solid match requires bedside table and rug!
                if bst and rug:
                    pkg.update({"bedside_table": bst, "bed": bed, "dresser": dr, "table_lamp": tl, "rug": rug})
                    matched_pkg = pkg
                    break
                    
            elif room_type == "bar":
                bs = seed_item if seed_cat == "barstool" else find_matching_companion(["barstool"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bs: exclude_ids.add(bs["filename"])
                
                bt = seed_item if seed_cat == "bartable" else find_matching_companion(["bartable", "dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bt: exclude_ids.add(bt["filename"])
                
                pl = seed_item if seed_cat == "pendant_lamp" else None
                if pl: exclude_ids.add(pl["filename"])
                
                rug = find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, bt if bt else seed_item, relax)
                if rug: exclude_ids.add(rug["filename"])
                
                bg = find_matching_companion(["cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bg: exclude_ids.add(bg["filename"])
                
                # Solid match requires barstool and rug!
                if bs and rug:
                    pkg.update({"barstool": bs, "bartable": bt, "pendant_lamp": pl, "rug": rug, "background_storage": bg})
                    matched_pkg = pkg
                    break
                    
        if matched_pkg:
            for slot, item in matched_pkg.items():
                if slot not in ["room_type", "relax_level", "seed"] and item is not None:
                    unfeatured_ids.discard(item["filename"])
            packages.append(matched_pkg)
            recount_usages(packages, db)
        else:
            # Fallback package
            packages.append({"seed": seed_item, "room_type": room_type, "relax_level": 10})
            recount_usages(packages, db)

    # Populate missing slots to make every room complete
    for pkg_idx, pkg in enumerate(packages):
        current_allowed_items = get_allowed_items_for_idx(pkg_idx)
        fill_empty_slots(pkg, items_by_cat, unfeatured_ids)
        recount_usages(packages, db)

    print(f"✓ Curation complete! Generated {len(packages)} packages covering 100% of the active catalog.")
    
    # ----------------------------------------------------
    # PROMPT GENERATION
    # ----------------------------------------------------
    def is_kitchen_applicable(pkg: Dict) -> bool:
        if pkg.get("room_type") in ("dining", "bar"):
            return True
        for slot, item in pkg.items():
            if slot not in ["room_type", "relax_level", "seed"] and item is not None:
                filename = item.get("filename", "").lower()
                cat = get_item_category(filename, item)
                if cat in ("dining_table", "dining_chair", "barstool", "bartable"):
                    return True
                if "kok" in filename or "kök" in filename:
                    return True
        return False

    def get_dynamic_location(pkg_idx: int, is_kitchen: bool) -> Tuple[str, str]:
        env_type = pkg_idx % 6
        
        if env_type == 0:
            room = "kitchen-living room" if is_kitchen else "living room"
            fireplace = "a classic tiled stove (kakelugn) in the corner" if (pkg_idx % 2 == 0) else "a clean empty fireplace against the wall"
            desc = f"Stockholm classic turn-of-the-century apartment {room} in Östermalm with {fireplace}, and views of tree-lined streets"
            name = "Classic Stockholm Apartment"
        elif env_type == 1:
            room = "Scandi kitchen-living room" if is_kitchen else "Scandi living room"
            desc = f"{room} with large windows, soft plaster walls, and light-toned ash floors"
            name = "Scandi Apartment"
        elif env_type == 2:
            room = "kitchen-living room" if is_kitchen else "living room"
            desc = f"Stockholm archipelago architect-designed villa {room} with massive floor-to-ceiling glass walls looking out over a serene waterfront and rocky pine shores"
            name = "Stockholm Archipelago Villa"
        elif env_type == 3:
            room = "kitchen-living room" if is_kitchen else "living room"
            desc = f"Scandi architect-designed cabin {room} featuring exposed pine timber structures and large windows facing a misty forest landscape"
            name = "Scandi Architect Cabin"
        elif env_type == 4:
            room = "kitchen-living room with garden view" if is_kitchen else "living room with garden view"
            desc = f"Scandi architect-designed {room}, set against large glass doors looking out onto a modern courtyard garden"
            name = "Scandi Villa with Garden"
        else: # env_type == 5
            room = "kitchen-living room" if is_kitchen else "living room"
            desc = f"Scandi penthouse {room} with panoramic windows, high ceilings, and sweeping views of city rooftops"
            name = "Scandi Penthouse"
            
        return desc, name

    def get_focus_phrase(seed_cat: str) -> str:
        if seed_cat == "sofa":
            return ", with focus on the sofa"
        elif seed_cat == "armchair":
            return ", with focus on the chairs"
        elif seed_cat == "coffeetable":
            return ", with focus on the coffee table"
        elif seed_cat == "rug":
            return ", with focus on the carpet"
        return ""

    output_rows = []
    tracking_rows = []
    
    for pkg_idx, pkg in enumerate(packages):
        package_id = f"PKG-{pkg_idx+1:03d}"
        room_type = pkg["room_type"]
        
        is_kitchen = is_kitchen_applicable(pkg)
        location_desc, location_name = get_dynamic_location(pkg_idx, is_kitchen)
        
        tagged_items = []
        
        subject_desc = ""
        subject_desc_2 = ""
        bg_elements = []
        bg_elements_2 = []
        style_val = pkg["seed"]["metadata"].get(STYLE_KEY, "scandinavian minimalist")
        tone_val = pkg["seed"]["metadata"].get(TONE_KEY, "warm neutral")
        wood_val = pkg["seed"]["metadata"].get(WOOD_KEY, "ek")
        
        seed_cat = get_item_category(pkg["seed"]["filename"], pkg["seed"])
        focus_phrase = get_focus_phrase(seed_cat)
        
        if room_type == "dining":
            dt = pkg.get("dining_table")
            dc = pkg.get("dining_chair")
            rug = pkg.get("rug")
            pl = pkg.get("pendant_lamp")
            bg = pkg.get("background_storage")
            
            dt_name = clean_tag_to_name(dt["filename"]) if dt else "minimalist wooden table"
            dc_name = clean_tag_to_name(dc["filename"]) if dc else "Scandinavian chairs"
            
            if dt: tagged_items.append(dt)
            if dc: tagged_items.append(dc)
            
            chair_type = "armchairs" if "karmstol" in (dc["filename"].lower() if dc else "") else "chairs"
            subject_desc = f"the elegant table ({dt_name}) and matching {chair_type} ({dc_name}) in the center of the spacious room"
            subject_desc_2 = f"the elegant table ({dt_name}) and matching {chair_type} ({dc_name})"
            
            if rug:
                tagged_items.append(rug)
                rug_desc = get_rug_description(rug, with_form=True)
                subject_desc += f", all resting on a {rug_desc}"
                subject_desc_2 += f", resting on the {rug_desc}"
                
            if pl:
                tagged_items.append(pl)
                pl_name = clean_tag_to_name(pl["filename"])
                subject_desc += f", with the designer pendant light ({pl_name}) hanging low from the ceiling directly above the table"
                subject_desc_2 += f", under the glowing designer pendant light ({pl_name}) casting a focused warm light"
                
            if bg:
                tagged_items.append(bg)
                bg_name = clean_tag_to_name(bg["filename"])
                bg_elements.append(f"a gorgeous cabinet ({bg_name}) standing against the wall")
                bg_elements_2.append(f"a gorgeous cabinet ({bg_name}) standing against the wall")
            else:
                bg_elements.append("an arty abstract poster without text hanging on the wall")
                bg_elements_2.append("an arty abstract poster without text hanging on the wall")
            
        elif room_type == "living_seating":
            sofa = pkg.get("sofa")
            ac = pkg.get("armchair")
            ct = pkg.get("coffeetable")
            rug = pkg.get("rug")
            fl = pkg.get("floor_lamp")
            bg = pkg.get("background_storage")
            
            sofa_name = clean_tag_to_name(sofa["filename"]) if sofa else ""
            ac_name = clean_tag_to_name(ac["filename"]) if ac else ""
            ct_name = clean_tag_to_name(ct["filename"]) if ct else "wooden coffee table"
            
            subject_parts = []
            parts_2 = []
            if sofa:
                tagged_items.append(sofa)
                subject_parts.append(f"the plush Scandinavian sofa ({sofa_name})")
                parts_2.append(f"the plush sofa ({sofa_name})")
            if ac:
                tagged_items.append(ac)
                ac_name = clean_tag_to_name(ac["filename"])
                import random
                if random.choice([True, False]):
                    subject_parts.append(f"a beautiful elegant armchair ({ac_name})")
                else:
                    subject_parts.append(f"a pair of matching elegant armchairs ({ac_name})")
                parts_2.append(f"a pair of matching elegant armchairs ({ac_name})")
            if ct:
                tagged_items.append(ct)
                subject_parts.append(f"the minimalist wood coffee table ({ct_name})")
                parts_2.append(f"the minimalist coffee table ({ct_name})")
                
            subject_desc = f"a warm and complete living room seating setup showcasing " + " and ".join(subject_parts)
            subject_desc_2 = " and ".join(parts_2)
            
            if rug:
                tagged_items.append(rug)
                rug_desc = get_rug_description(rug, with_form=False)
                subject_desc += f", grounded beautifully by a {rug_desc} underneath"
                subject_desc_2 += f", resting on the {rug_desc}"
                
            if fl:
                tagged_items.append(fl)
                fl_name = clean_tag_to_name(fl["filename"])
                bg_elements.append(f"a designer floor lamp ({fl_name}) standing in a quiet corner")
                bg_elements_2.append(f"a designer floor lamp ({fl_name}) standing in a quiet corner casting a warm ambient glow")
                
            if bg:
                tagged_items.append(bg)
                bg_name = clean_tag_to_name(bg["filename"])
                bg_elements.append(f"a matching cabinet ({bg_name}) standing against the wall")
                bg_elements_2.append(f"a matching cabinet ({bg_name}) standing against the wall")
            else:
                bg_elements.append("an arty abstract poster without text hanging on the wall")
                bg_elements_2.append("an arty abstract poster without text hanging on the wall")
                
        elif room_type == "living_storage":
            ps = pkg.get("primary_storage")
            ac = pkg.get("armchair")
            rug = pkg.get("rug")
            tl = pkg.get("table_lamp")
            
            ps_name = clean_tag_to_name(ps["filename"]) if ps else "designer cabinet"
            if ps: tagged_items.append(ps)
            
            is_bench = ps and ("bänk" in ps["filename"].lower() or "bank" in ps["filename"].lower()) and not ("tv-bänk" in ps["filename"].lower() or "tv-bönk" in ps["filename"].lower() or "mediabänk" in ps["filename"].lower())
            
            if is_bench:
                subject_desc = f"a sophisticated setup featuring the elegant bench ({ps_name}) standing along the wall"
                subject_desc_2 = f"the elegant bench ({ps_name}) standing along the wall"
            else:
                subject_desc = f"a sophisticated storage setup featuring the beautiful {ps_name} standing against the wall"
                subject_desc_2 = f"the elegant {ps_name} standing against the wall"
            
            if tl:
                tagged_items.append(tl)
                tl_name = clean_tag_to_name(tl["filename"])
                is_wall = "vagglampa" in tl["filename"].lower() or "vägglampa" in tl["filename"].lower() or "vagg" in tl["filename"].lower() or "vägg" in tl["filename"].lower()
                
                if is_wall:
                    subject_desc += f", with a designer wall lamp ({tl_name}) mounted on the wall above it"
                    subject_desc_2 += f" with the glowing designer wall lamp ({tl_name}) mounted on the wall above, casting a warm soft light downwards onto its surface"
                else:
                    subject_desc += f", with a designer table lamp ({tl_name}) placed on a windowsill in a large window"
                    subject_desc_2 += f" with the glowing designer table lamp ({tl_name}) casting a warm soft light on its surface"
                
            if ac:
                tagged_items.append(ac)
                ac_name = clean_tag_to_name(ac["filename"])
                bg_elements.append(f"a pair of matching elegant armchairs ({ac_name}) standing nearby")
                bg_elements_2.append(f"a pair of matching elegant armchairs ({ac_name}) standing nearby")
                
            if rug:
                tagged_items.append(rug)
                rug_desc = get_rug_description(rug, with_form=False)
                bg_elements.append(f"a {rug_desc} spreading on the floor")
                bg_elements_2.append(f"a {rug_desc} spreading on the floor")
            else:
                bg_elements.append("an arty abstract poster without text hanging on the wall")
                bg_elements_2.append("an arty abstract poster without text hanging on the wall")
                
        elif room_type == "office":
            desk = pkg.get("desk")
            dc = pkg.get("desk_chair")
            bc = pkg.get("bookcase")
            tl = pkg.get("table_lamp")
            
            desk_name = clean_tag_to_name(desk["filename"]) if desk else "study desk"
            if desk: tagged_items.append(desk)
            
            subject_desc = f"a refined home office study setup focusing on the elegant desk ({desk_name}) standing against the wall"
            subject_desc_2 = f"the refined desk ({desk_name}) standing against the wall"
            
            if dc:
                tagged_items.append(dc)
                dc_name = clean_tag_to_name(dc["filename"])
                subject_desc += f", paired with a matching structured chair ({dc_name}) tucked neatly underneath"
                subject_desc_2 += f" paired with the structured chair ({dc_name})"
                
            if tl:
                tagged_items.append(tl)
                tl_name = clean_tag_to_name(tl["filename"])
                is_wall = "vagglampa" in tl["filename"].lower() or "vägglampa" in tl["filename"].lower() or "vagg" in tl["filename"].lower() or "vägg" in tl["filename"].lower()
                
                if is_wall:
                    subject_desc += f", with a designer wall lamp ({tl_name}) mounted on the wall above"
                    subject_desc_2 += f" and the glowing designer wall lamp ({tl_name}) mounted on the wall above, illuminating the workspace with a quiet warm light"
                else:
                    subject_desc += f", with a designer table lamp ({tl_name}) placed on a windowsill in a large window"
                    subject_desc_2 += f" and the glowing designer table lamp ({tl_name}) illuminating the workspace with a quiet warm light"
                
            if bc:
                tagged_items.append(bc)
                bc_name = clean_tag_to_name(bc["filename"])
                bg_elements.append(f"a tall bookcase ({bc_name}) standing against the wall")
                bg_elements_2.append(f"a tall bookcase ({bc_name}) standing against the wall")
            else:
                bg_elements.append("an arty abstract poster without text hanging on the wall")
                bg_elements_2.append("an arty abstract poster without text hanging on the wall")
                
        elif room_type == "bedroom":
            bst = pkg.get("bedside_table")
            bed = pkg.get("bed")
            dr = pkg.get("dresser")
            tl = pkg.get("table_lamp")
            rug = pkg.get("rug")
            
            bst_name = clean_tag_to_name(bst["filename"]) if bst else "bedside table"
            if bst: tagged_items.append(bst)
            
            is_sofa = bed and ("soffa" in bed["filename"].lower() or "bäddsoffa" in bed["filename"].lower())
            
            if bed:
                tagged_items.append(bed)
                bed_name = clean_tag_to_name(bed["filename"])
                if is_sofa:
                    subject_desc = f"a serene master bedroom featuring the bedside table ({bst_name}) standing next to the comfortable sofa ({bed_name})"
                    subject_desc_2 = f"the serene bedside table ({bst_name}) standing next to the comfortable sofa ({bed_name})"
                else:
                    subject_desc = f"a serene master bedroom featuring the bedside table ({bst_name}) standing against the wall next to the beautifully made bed ({bed_name}) with crisp organic linen sheets"
                    subject_desc_2 = f"the serene bedside table ({bst_name}) standing against the wall next to the bed ({bed_name}) with crisp linen"
            else:
                subject_desc = f"a serene master bedroom featuring the bedside table ({bst_name}) standing against the wall next to a beautifully made bed with crisp organic linen sheets"
                subject_desc_2 = f"the serene bedside table ({bst_name}) standing against the wall next to the bed"
            
            if tl:
                tagged_items.append(tl)
                tl_name = clean_tag_to_name(tl["filename"])
                is_wall = "vagglampa" in tl["filename"].lower() or "vägglampa" in tl["filename"].lower() or "vagg" in tl["filename"].lower() or "vägg" in tl["filename"].lower()
                
                if is_wall:
                    subject_desc += f", with a designer wall lamp ({tl_name}) mounted on the wall above"
                    subject_desc_2 += f" with the glowing designer wall lamp ({tl_name}) mounted on the wall above, casting a warm soft light"
                else:
                    subject_desc += f", with a designer table lamp ({tl_name}) placed on a windowsill in a large window"
                    subject_desc_2 += f" with the glowing designer table lamp ({tl_name}) resting on it casting a warm soft light"
                
            if dr:
                tagged_items.append(dr)
                dr_name = clean_tag_to_name(dr["filename"])
                bg_elements.append(f"a large matching dresser ({dr_name}) standing against the wall")
                bg_elements_2.append(f"a large matching dresser ({dr_name}) standing against the wall")
                
            if rug:
                tagged_items.append(rug)
                rug_desc = get_rug_description(rug, with_form=False)
                bg_elements.append(f"a {rug_desc} placed under the sofa" if is_sofa else f"a {rug_desc} placed under the bed")
                bg_elements_2.append(f"a {rug_desc} placed under the sofa" if is_sofa else f"a {rug_desc} placed under the bed")
            else:
                bg_elements.append("an arty abstract poster without text hanging on the wall")
                bg_elements_2.append("an arty abstract poster without text hanging on the wall")
                
        elif room_type == "bar":
            bs = pkg.get("barstool")
            bt = pkg.get("bartable")
            pl = pkg.get("pendant_lamp")
            rug = pkg.get("rug")
            bg = pkg.get("background_storage")
            
            bs_name = clean_tag_to_name(bs["filename"]) if bs else "modern barstools"
            if bs: tagged_items.append(bs)
            
            if bt:
                tagged_items.append(bt)
                bt_name = clean_tag_to_name(bt["filename"])
                subject_desc = f"a beautiful kitchen bar setup with the barstools ({bs_name}) placed neatly around the matching bar table ({bt_name})"
                subject_desc_2 = f"the kitchen bar setup with the barstools ({bs_name}) paired with the matching bar table ({bt_name})"
            else:
                subject_desc = f"a kitchen island seating setup showcasing the minimalist barstools ({bs_name}) arranged along the white countertop"
                subject_desc_2 = f"the kitchen island setup with the barstools ({bs_name}) along the counter"
                
            if rug:
                tagged_items.append(rug)
                rug_desc = get_rug_description(rug, with_form=False)
                subject_desc += f", all resting on a {rug_desc}"
                subject_desc_2 += f", resting on the {rug_desc}"
                
            if pl:
                tagged_items.append(pl)
                pl_name = clean_tag_to_name(pl["filename"])
                subject_desc += f", with a gorgeous designer pendant lamp ({pl_name}) hanging low from the ceiling"
                subject_desc_2 += f" under the glowing designer pendant lamp ({pl_name}) casting a focused warm light"
                
            if bg:
                tagged_items.append(bg)
                bg_name = clean_tag_to_name(bg["filename"])
                bg_elements.append(f"a sideboard ({bg_name}) standing against the wall")
                bg_elements_2.append(f"a sideboard ({bg_name}) standing against the wall")
            else:
                bg_elements.append("an arty abstract poster without text hanging on the wall")
                bg_elements_2.append("an arty abstract poster without text hanging on the wall")
                
        seen_filenames = set()
        unique_tagged_items = []
        for x in tagged_items:
            if x["filename"] not in seen_filenames:
                seen_filenames.add(x["filename"])
                unique_tagged_items.append(x)
        tagged_items = unique_tagged_items
        
        tags_str = "  " + " ".join([get_short_tag(x["filename"]) for x in tagged_items])
        
        # USE THE EXACT LONG FILENAMES TO GUARANTEE 100% MATCHING!
        files_str = "; ".join([x["filename"] for x in tagged_items])
        
        short_tags_only = "; ".join([get_short_tag(x["filename"]) for x in tagged_items])
        is_lamp = seed_cat in ["table_lamp", "floor_lamp", "pendant_lamp"]
        
        # ----------------------------------------------------
        # Shot 1: Standard View
        # ----------------------------------------------------
        shot1_num = len(output_rows) + 1
        shot1_light = "warm afternoon light with long soft shadows" if is_lamp else ("crisp cinematic afternoon sunlight" if (pkg_idx % 2 == 0) else "bright natural morning light streaming through the windows")
        bg_sentence_1 = join_background_elements(bg_elements, close_up=False)
        bg_part_1 = f" {bg_sentence_1}" if bg_sentence_1 else ""
        
        prompt_1 = (
            f"{shot1_num:03d} - Architectural digest-style view of {subject_desc} set in a {location_desc} with {shot1_light}{focus_phrase}.{bg_part_1} "
            f"Dynamic three-quarter angle with controlled depth of field. Varied gloss levels on walls and trim to enhance depth, featuring tactile micro-imperfections. "
            f"Strictly preserve individual furniture material finishes (matte, lacquer, metal) without global gloss changes. Enhance atmosphere with very subtle volumetric-dust. "
            f"Prioritize high-end material tactility and realistic light-reactive surfaces over digital polish, showcasing premium wood and stone surfaces. "
            f"Utilize chiaroscuro lighting techniques to deepen shadow definition, ensuring clear silhouettes for furniture against the walls. "
            f"Break the monochromatic palette with refined material contrasts, such as cool-toned stone or matte metallic finishes to add depth and sophisticated material friction. "
            f"No cutting-boards, no wooden plates in the kitchen, no abstract sculpture, no plants, no knick-knack.{tags_str}"
        )
        
        output_rows.append({
            "prompt": prompt_1,
            "image_references": files_str,
            "image_tags": short_tags_only,
            "aspect_ratio": "1:1"
        })
        
        tracking_rows.append({
            "Row Number": shot1_num,
            "Package ID": package_id,
            "Package Type": room_type.capitalize(),
            "Template Style": location_name,
            "Focus Type": "Standard View",
            "Close-up": "No",
            "Location": location_name,
            "Focus Description": subject_desc,
            "Style / Aesthetic": style_val,
            "Color Tone": tone_val,
            "Wood Finish": wood_val,
            "Table Product": clean_tag_to_name(pkg.get("dining_table")["filename"], include_dimensions=False) if pkg.get("dining_table") else (clean_tag_to_name(pkg.get("coffeetable")["filename"], include_dimensions=False) if pkg.get("coffeetable") else (clean_tag_to_name(pkg.get("desk")["filename"], include_dimensions=False) if pkg.get("desk") else "None")),
            "Seating Product": clean_tag_to_name(pkg.get("dining_chair")["filename"], include_dimensions=False) if pkg.get("dining_chair") else (clean_tag_to_name(pkg.get("sofa")["filename"], include_dimensions=False) if pkg.get("sofa") else (clean_tag_to_name(pkg.get("armchair")["filename"], include_dimensions=False) if pkg.get("armchair") else (clean_tag_to_name(pkg.get("barstool")["filename"], include_dimensions=False) if pkg.get("barstool") else (clean_tag_to_name(pkg.get("desk_chair")["filename"], include_dimensions=False) if pkg.get("desk_chair") else "None")))),
            "Rug Product": clean_tag_to_name(pkg.get("rug")["filename"], include_dimensions=False) if pkg.get("rug") else "None",
            "Lamp Product": clean_tag_to_name(pkg.get("pendant_lamp")["filename"], include_dimensions=False) if pkg.get("pendant_lamp") else (clean_tag_to_name(pkg.get("floor_lamp")["filename"], include_dimensions=False) if pkg.get("floor_lamp") else (clean_tag_to_name(pkg.get("table_lamp")["filename"], include_dimensions=False) if pkg.get("table_lamp") else "None")),
            "Storage Product": clean_tag_to_name(pkg.get("background_storage")["filename"], include_dimensions=False) if pkg.get("background_storage") else (clean_tag_to_name(pkg.get("primary_storage")["filename"], include_dimensions=False) if pkg.get("primary_storage") else (clean_tag_to_name(pkg.get("bookcase")["filename"], include_dimensions=False) if pkg.get("bookcase") else (clean_tag_to_name(pkg.get("dresser")["filename"], include_dimensions=False) if pkg.get("dresser") else "None"))),
            "References Utilized": files_str,
            "Tags Utilized": short_tags_only
        })
        

        

    print(f"✓ Generated exactly {len(output_rows)} logical prompt rows in memory.")
    
    with open(EXPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, ensure_ascii=False, indent=2)
    print(f"✓ Exported JSON to: {EXPORT_JSON_PATH}")
    
    with open(FLAT_JSON_EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, ensure_ascii=False, indent=2)
    print(f"✓ Exported TurboFlow Flat JSON to: {FLAT_JSON_EXPORT_PATH}")
    
    try:
        with open(CSV_EXPORT_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["prompt", "image_references", "image_tags", "aspect_ratio"])
            for row in output_rows:
                writer.writerow([
                    row["prompt"],
                    row["image_references"],
                    row["image_tags"],
                    row["aspect_ratio"]
                ])
        print(f"✓ Exported standard TurboFlow CSV to: {CSV_EXPORT_PATH}")
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")
        
    try:
        with open(TXT_EXPORT_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["prompt", "image_references", "image_tags", "aspect_ratio"])
            for row in output_rows:
                writer.writerow([
                    row["prompt"],
                    row["image_references"],
                    row["image_tags"],
                    row["aspect_ratio"]
                ])
        print(f"✓ Exported standard TurboFlow TXT to: {TXT_EXPORT_PATH}")
    except Exception as e:
        print(f"❌ Error writing TXT: {e}")
        
    try:
        with open(PROMPTS_ONLY_EXPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
            for row in output_rows:
                f.write(row["prompt"] + "\n")
        print(f"✓ Exported raw prompts-only TXT to: {PROMPTS_ONLY_EXPORT_PATH}")
    except Exception as e:
        print(f"❌ Error writing prompts-only TXT: {e}")
        
    try:
        headers = [
            "Row Number", "Package ID", "Package Type", "Template Style", "Focus Type", "Close-up",
            "Location", "Focus Description", "Style / Aesthetic", "Color Tone",
            "Wood Finish", "Table Product", "Seating Product", "Rug Product",
            "Lamp Product", "Storage Product", "References Utilized", "Tags Utilized"
        ]
        with open(TRACKING_LOG_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=";")
            writer.writeheader()
            for row in tracking_rows:
                writer.writerow(row)
        print(f"✓ Exported Excel-compatible Tracking Spreadsheet CSV to: {TRACKING_LOG_PATH}")
    except Exception as e:
        print(f"❌ Error writing tracking CSV: {e}")
        
    print("\n🎉 Sample Prompts for Validation:")
    print("-" * 80)
    limit = min(4, len(tracking_rows))
    for i in range(limit):
        print(f"\nRow #{i+1} [{tracking_rows[i]['Focus Type']} - Close-up: {tracking_rows[i]['Close-up']}]:")
        print(f"  Location: {tracking_rows[i]['Location']}")
        print(f"  References: {tracking_rows[i]['References Utilized']}")
        print(f"  Prompt: {output_rows[i]['prompt']}")
    print("-" * 80)

if __name__ == "__main__":
    main()
