import os
import json
import re
import shutil
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

REFORMA_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
BRAIN_SCRATCH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\scratch"
PICS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
TARGET_DIR = os.path.join(PICS_DIR, "Reforma-interiörer-26-06")
DIRS = [
    PICS_DIR,
    os.path.join(PICS_DIR, "första omgången fyrkantiga"),
    os.path.join(PICS_DIR, "arkiv_gamla_sorterade")
]

sku_map = {}
brand_sku_dict = {}
pipeline_slugs = {}
missed_products = {}
brand_keys = []
pipeline_keys = []
missed_keys = []

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
    # Split into words by replacing separators with spaces
    text = name.lower().replace('_', ' ').replace('-', ' ')
    
    # Common broken words in reference names due to UTF-8 decoding issues
    replacements = {
        'sngbord': 'sangbord',
        'lvhamn': 'lovhamn',
        'byr': 'byra',
        'ftlj': 'fatolj',
        'tvbnk': 'tvbank',
        'tv-bnk': 'tv-bank',
        'krra': 'karra',
        'sknk': 'skank',
        'skp': 'skap',
        'gr': 'gra',
        'tr': 'tra',
        'blvik': 'blavik',
        'sng': 'sang',
        'mrkgr': 'morkgra',
        'mrkgra': 'morkgra',
        'ljusgr': 'ljusgra',
        'stjrna': 'stjarna',
        'mssing': 'massing',
        'bors': 'boras',
        'kldhngare': 'kladhangare',
        'kldstll': 'kladstall'
    }
    
    words = text.split()
    words = [replacements.get(w, w) for w in words]
    text = " ".join(words)
        
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

    if cleaned in missed_products:
        return missed_products[cleaned], get_beautiful_name(cleaned)
    for mk in missed_keys:
        if mk['norm'] == norm_c:
            return mk['sku'], get_beautiful_name(mk['slug'])

    for pk in pipeline_keys:
        if pk['norm'] == norm_c:
            return pk['sku'], get_beautiful_name(pk['slug'])

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

    for mk in missed_keys:
        if mk['simple_norm'] == simple_norm_c:
            return mk['sku'], get_beautiful_name(mk['slug'])
    for pk in pipeline_keys:
        if pk['simple_norm'] == simple_norm_c:
            return pk['sku'], get_beautiful_name(pk['slug'])
    for bk in brand_keys:
        if bk['simple_norm_slug'] == simple_norm_c or bk['simple_norm_name'] == simple_norm_c:
            return bk['sku'], bk['name']

    for mk in missed_keys:
        if mk['norm'] in norm_c or norm_c in mk['norm']:
            return mk['sku'], get_beautiful_name(mk['slug'])
    for pk in pipeline_keys:
        if pk['norm'] in norm_c or norm_c in pk['norm']:
            return pk['sku'], get_beautiful_name(pk['slug'])
    for bk in brand_keys:
        if bk['norm_slug'] in norm_c or norm_c in bk['norm_slug'] or bk['norm_name'] in norm_c or norm_c in bk['norm_name']:
            return bk['sku'], bk['name']

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

    return None, get_beautiful_name(cleaned)

def load_databases():
    global sku_map, brand_sku_dict, pipeline_slugs, missed_products, brand_keys, pipeline_keys, missed_keys
    sku_map_path = os.path.join(REFORMA_DIR, 'sku_map.json')
    brand_dict_path = os.path.join(REFORMA_DIR, 'brand_sku_dict.json')
    pipeline_path = os.path.join(BRAIN_SCRATCH, 'pipeline_mappings.json')
    missed_path = os.path.join(PICS_DIR, 'missed_products.json')

    if os.path.exists(sku_map_path):
        with open(sku_map_path, 'r', encoding='utf-8') as f:
            sku_map = json.load(f)
    if os.path.exists(brand_dict_path):
        with open(brand_dict_path, 'r', encoding='utf-8') as f:
            brand_sku_dict = json.load(f)
    if os.path.exists(pipeline_path):
        with open(pipeline_path, 'r', encoding='utf-8') as f:
            pipeline_mappings = json.load(f)
            pipeline_slugs = {item['product']: item['sku'] for item in pipeline_mappings}
    if os.path.exists(missed_path):
        with open(missed_path, 'r', encoding='utf-8') as f:
            missed_products = json.load(f)

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

    for slug, sku in pipeline_slugs.items():
        norm_val = normalize(slug)
        pipeline_keys.append({
            'slug': slug,
            'sku': sku,
            'norm': norm_val,
            'simple_norm': get_simple_norm(norm_val)
        })

    for slug, sku in missed_products.items():
        norm_slug = normalize(slug)
        missed_keys.append({
            'slug': slug,
            'sku': sku,
            'norm': norm_slug,
            'simple_norm': get_simple_norm(norm_slug)
        })

def load_rooms_db(filename):
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
            mapping[idx] = {
                'refs': refs,
                'prompt': prompt
            }
    return mapping

def parse_folder_name(folder_name):
    m = re.search(r'\(([^)]+)\)$', folder_name)
    sku = m.group(1).strip() if m else None
    
    name_part = re.sub(r'\s*\([^)]+\)$', '', folder_name).strip()
    name_lower = name_part.lower()
    
    categories = ["baddsoffa", "barstol", "byra", "byrå", "bokhylla", "bord", "hylla", "matbord", "matgrupp", "sangbord", "sängbord", "sideboard", "sidobord", "skank", "skänk", "skap", "skåp", "skrivbord", "tv bank", "tv-bänk", "tv-bank", "tvbänk", "vagghylla", "vägghylla", "vinhylla"]
    category = None
    for cat in categories:
        if name_lower.startswith(cat):
            category = cat
            break
            
    if category:
        rest = name_part[len(category):].strip()
    else:
        rest = name_part
        
    rest = re.sub(r'^[^a-zA-Z0-9åäöÅÄÖ]+', '', rest).strip()
    words = rest.split()
    words = [w for w in words if re.search(r'[a-zA-ZåäöÅÄÖ0-9]', w)]
    
    return category, words, sku

def get_search_patterns(folder_name):
    category, words, sku = parse_folder_name(folder_name)
    if not words:
        return []
        
    generic_words = {
        "natur", "svart", "vit", "gra", "grå", "brun", "guld", "silver", "koppar", "mässing", "massing", 
        "ek", "valnöt", "valnot", "liten", "stor", "mellan", "hona", "hane", "beige", "grön", "gron", 
        "blå", "bla", "rosa", "gul", "runt", "160x90cm", "120x70cm", "180x70cm", "135cm", "140cm", 
        "120cm", "200x40cm", "75cm", "40cm", "45x110", "120x70", "90x90", "1", "2", "3", "4", "5", 
        "6", "7", "8", "9", "0", "cm", "mörkgrå", "morkgra", "ljusgrå", "ljusgra", "gråbrun", "grabrun",
        "beigebrun", "turkosmässing", "turkosmassing", "svartmässing", "svartmassing", "vitmässing", 
        "vitmassing", "turkos", "wood", "green", "black", "white", "grey", "natural", "walnut", "oak",
        "och", "med", "av", "till", "delar", "lådor", "lador", "stolar", "bord", "cm"
    }
    
    filtered = [w for w in words if w.lower() not in generic_words]
    if not filtered:
        filtered = [words[0]]
        
    generic_identifiers = {"light", "prime", "line", "sand", "trend", "industri", "nordisk", "lux", "form", "forma", "stil", "amot", "cozy", "classic"}
    first_kw = filtered[0].lower()
    
    norm_cat = normalize(category) if category else ""
    
    patterns = []
    if first_kw in generic_identifiers and norm_cat:
        patterns.append(norm_cat + normalize(first_kw))
    else:
        patterns.append(normalize(filtered[0]))
        
    return patterns

def main():
    print("==================================================")
    print("      FILLING UNDER-POPULATED FURNITURE FOLDERS   ")
    print("==================================================")
    
    load_databases()
    
    # 1. Load Room Mappings by Batch
    batch1_map = load_rooms_db("rooms_turboflow_batch1.json")
    batch2_map = load_rooms_db("rooms_turboflow_batch2.json")
    full_catalog_map = load_rooms_db("rooms_turboflow_full_catalog.json")
    print(f"Loaded mappings: Batch1={len(batch1_map)}, Batch2={len(batch2_map)}, FullCatalog={len(full_catalog_map)}")
    
    # 2. Scan available render files across all three folders
    print("\nScanning available render files...")
    render_files = [] # list of (idx, diff, filepath)
    
    suffix_pattern = re.compile(r"^(\d+)-architectural-digest-styl(?:e)?-(.+?)\.(?:png|jpg|jpeg|webp)$", re.IGNORECASE)
    
    for d in DIRS:
        if not os.path.exists(d):
            print(f"   Directory not found: {d}")
            continue
        files = [name for name in os.listdir(d) if os.path.isfile(os.path.join(d, name)) and name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        print(f"   Found {len(files)} files in {os.path.basename(d) or 'turboflow_root'}")
        
        for f in files:
            m = suffix_pattern.match(f)
            if not m:
                m_simple = re.match(r"^(\d+)", f)
                if not m_simple:
                    continue
                lead_idx = int(m_simple.group(1))
                diff = 0
            else:
                lead_idx = int(m.group(1))
                style_part = m.group(2)
                m_style_digits = re.match(r"^(\d+)", style_part)
                if m_style_digits:
                    style_num = int(m_style_digits.group(1))
                    diff = lead_idx - style_num
                else:
                    diff = 0
                    
            render_files.append((lead_idx, diff, os.path.join(d, f)))
            
    print(f"Mapped {len(render_files)} render files.")
    
    # 3. Associate render files with their refs and prompts
    b2_diffs = {46, 76, 92, 174, 248, 262, 326, 354, 382, 389, 436, 576, 593}
    b1_diffs = {371, 410, 556, 622, 784, 820, 884, 912, 919, 984, 1046, 1106, 1123, 1145, 1252, 1279, 1282, 1286, 1576, 1578, 1587, 1592, 1782, 1790, 1809, 1816, 2108, 2113, 2117, 2226, 2400}
    
    print("\nMapping renders to database rooms...")
    render_to_data = [] # list of (filepath, refs, list of (batch_name, normalized_prompt))
    
    for lead_idx, diff, filepath in render_files:
        results = []
        is_b2 = (diff in b2_diffs and lead_idx <= 692)
        is_b1 = (diff in b1_diffs and lead_idx <= 2416) or (diff == 0 and lead_idx <= 371)
        
        if is_b2:
            if lead_idx in batch2_map:
                results.append(("batch2", batch2_map[lead_idx]['refs'], batch2_map[lead_idx]['prompt']))
        if is_b1:
            if lead_idx in batch1_map:
                results.append(("batch1", batch1_map[lead_idx]['refs'], batch1_map[lead_idx]['prompt']))
                
        if not is_b1 and not is_b2:
            if lead_idx in full_catalog_map:
                results.append(("full_catalog", full_catalog_map[lead_idx]['refs'], full_catalog_map[lead_idx]['prompt']))
        elif diff == 0 or diff in {2524, 2654, 2716}:
            if lead_idx in full_catalog_map:
                results.append(("full_catalog", full_catalog_map[lead_idx]['refs'], full_catalog_map[lead_idx]['prompt']))
                
        if not results:
            for name, m in [("full_catalog", full_catalog_map), ("batch1", batch1_map), ("batch2", batch2_map)]:
                if lead_idx in m:
                    results.append((name, m[lead_idx]['refs'], m[lead_idx]['prompt']))
                    
        combined_refs = []
        combined_prompts = []
        for bt, r, p in results:
            combined_refs.extend(r)
            combined_prompts.append((bt, normalize(p)))
            
        render_to_data.append((filepath, list(set(combined_refs)), combined_prompts))
        
    print("Done mapping renders to rooms.")
    
    # 4. Resolve SKU-to-renders dictionary
    print("\nBuilding SKU to renders mapping...")
    sku_to_renders = {}
    for filepath, refs, _ in render_to_data:
        for ref in refs:
            sku, name = resolve_anchor(ref)
            if sku:
                for key in [sku, urllib.parse.unquote(sku)]:
                    k_lower = key.strip().lower()
                    if k_lower not in sku_to_renders:
                        sku_to_renders[k_lower] = []
                    sku_to_renders[k_lower].append(filepath)
                    
    print(f"Mapped {len(sku_to_renders)} unique SKUs to render lists.")
    
    # 5. Populate folders with less than 15 renders
    subdirs = [d for d in os.listdir(TARGET_DIR) if os.path.isdir(os.path.join(TARGET_DIR, d))]
    target_count = 15
    copied_count = 0
    folders_populated = 0
    
    print(f"\nChecking subdirectories for render counts (target is at least {target_count} renders)...")
    
    for d in subdirs:
        path = os.path.join(TARGET_DIR, d)
        files = os.listdir(path)
        renders = [f for f in files if not f.startswith("00_REFERENCE_")]
        
        if len(renders) >= target_count:
            continue
            
        category, words, sku = parse_folder_name(d)
        if not sku:
            continue
            
        print(f"\n📂 Folder: '{d}' (Current renders: {len(renders)} / {target_count})")
        print(f"   SKU: {sku}")
        
        # Pool 1: SKU matches
        sku_lower = sku.lower()
        renders_pool = sku_to_renders.get(sku_lower, [])
        unquoted = urllib.parse.unquote(sku).lower()
        if unquoted != sku_lower:
            renders_pool = list(set(renders_pool + sku_to_renders.get(unquoted, [])))
            
        # Pool 2: Prompt text search matches (if we still need renders)
        patterns = get_search_patterns(d)
        print(f"   Search keywords/patterns: {patterns}")
        
        prompt_matches = []
        if len(renders_pool) < target_count and patterns:
            for filepath, _, prompts_list in render_to_data:
                matched = False
                for bt, norm_prompt in prompts_list:
                    for pat in patterns:
                        if pat in norm_prompt:
                            matched = True
                            break
                    if matched:
                        break
                if matched:
                    prompt_matches.append(filepath)
            
            print(f"   Found {len(prompt_matches)} prompt-matched renders.")
            
        # Combine pools, preserving SKU matches first
        combined_pool = []
        seen = set()
        
        for r in renders_pool:
            if r not in seen:
                combined_pool.append(r)
                seen.add(r)
                
        for r in prompt_matches:
            if r not in seen:
                combined_pool.append(r)
                seen.add(r)
                
        selected = combined_pool[:target_count]
        
        existing_filenames = set(renders)
        to_copy = []
        for src_path in selected:
            fn = os.path.basename(src_path)
            if fn not in existing_filenames:
                to_copy.append(src_path)
                
        if to_copy:
            print(f"   Copying {len(to_copy)} new renders into folder...")
            for src_path in to_copy:
                fn = os.path.basename(src_path)
                dest_path = os.path.join(path, fn)
                try:
                    shutil.copy2(src_path, dest_path)
                    copied_count += 1
                except Exception as e:
                    print(f"      ❌ Error copying {fn}: {e}")
            folders_populated += 1
        else:
            print("   No new matching renders found to copy.")
            
    print("\n==================================================")
    print("            UNDER-POPULATED FOLDERS POPULATED!     ")
    print("==================================================")
    print(f"📂 Folders updated with new renders: {folders_populated}")
    print(f"📝 Total render files copied: {copied_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
