import os
import json
import re
import csv
from typing import Dict, Any, List, Tuple

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
    return "other"

def clean_swedish_chars(text: str) -> str:
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text

def clean_tag_to_name(filename: str) -> str:
    base, _ = os.path.splitext(filename)
    base = re.sub(r'^\d+__*', '', base)
    base = re.sub(r'^\d+_', '', base)
    base = re.sub(r'-\d+-\w+-wonder$', '', base)
    base = re.sub(r'-\d+$', '', base)
    base = base.replace("-", " ").replace("_", " ").title()
    return clean_swedish_chars(base)

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

def run_simulation(window_sizes, generator_batch_size, generator_shift):
    db = {}
    for db_file in ['furniture_db.json', 'furniture_db_batch2.json', 'furniture_db_batch3.json']:
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                temp_db = json.load(f)
                for k, v in temp_db.items():
                    if not should_skip_item(k):
                        db[k] = v
        except:
            pass
            
    with open('brand_sku_dict.json', 'r', encoding='utf-8') as f:
        brand_db = json.load(f)
    for k, v in brand_db.items():
        if k not in db and not should_skip_item(k):
            db[k] = {'metadata': {}, 'url': v.get('url'), 'filename': k}
            
    done_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"
    done_titles = set()
    if os.path.exists(done_dir):
        for name in os.listdir(done_dir):
            if os.path.isdir(os.path.join(done_dir, name)):
                done_titles.add(name.lower().strip())
                
    filtered_db = {}
    for k, v in db.items():
        title = clean_tag_to_name(k).lower().strip()
        if title not in done_titles:
            filtered_db[k] = v
    db = filtered_db
    
    usage_counts = {k: 0 for k in db.keys()}
    items_by_cat = {}
    for filename, item in db.items():
        item["filename"] = filename
        cat = get_item_category(filename, item)
        items_by_cat[cat] = items_by_cat.get(cat, []) + [item]
        
    unfeatured_ids = set(db.keys())
    
    items_by_cat_lists = {}
    for cat in window_sizes.keys():
        items_by_cat_lists[cat] = sorted(list({item["filename"] for item in items_by_cat.get(cat, [])}))

    def get_allowed_items_for_idx(idx):
        allowed_map = {}
        batch_idx = idx // generator_batch_size
        for cat, w in window_sizes.items():
            items_list = items_by_cat_lists.get(cat, [])
            n = len(items_list)
            if n == 0:
                continue
            start_idx = (batch_idx * generator_shift) % n
            allowed = set()
            for offset in range(w):
                allowed.add(items_list[(start_idx + offset) % n])
            allowed_map[cat] = allowed
        return allowed_map

    def find_matching_companion(cats_to_search, exclude_ids, anchor_item, relax_level, allowed_ids):
        candidates = []
        for cat in cats_to_search:
            candidates.extend(items_by_cat.get(cat, []))
            
        anchor_style = anchor_item["metadata"].get(STYLE_KEY)
        anchor_tone = anchor_item["metadata"].get(TONE_KEY)
        anchor_wood = anchor_item["metadata"].get(WOOD_KEY)
        
        def sort_key(x):
            is_unfeatured = x["filename"] in unfeatured_ids
            usage = usage_counts.get(x["filename"], 0)
            return (0 if is_unfeatured else 1, usage, x["filename"])
            
        sorted_candidates = sorted(candidates, key=sort_key)
        
        for item in sorted_candidates:
            if item["filename"] in exclude_ids:
                continue
                
            item_cat = get_item_category(item["filename"], item)
            allowed = allowed_ids.get(item_cat)
            if allowed is not None and item["filename"] not in allowed:
                continue
                
            i_style = item["metadata"].get(STYLE_KEY)
            i_tone = item["metadata"].get(TONE_KEY)
            i_wood = item["metadata"].get(WOOD_KEY)
            
            style_ok = i_style == anchor_style
            tone_ok = i_tone == anchor_tone
            wood_ok = woods_harmonize(anchor_wood, i_wood)
            
            if "rug" in cats_to_search and relax_level < 8:
                anchor_cat = get_item_category(anchor_item["filename"], anchor_item)
                if anchor_cat in ["dining_table", "coffeetable"]:
                    is_table_round = any(x in anchor_item["filename"].lower() for x in ["runt", "rund", "cirkel", "cirkular", "round"])
                    rug_form = item["metadata"].get("form", "").strip().lower()
                    is_rug_round = rug_form == "rund" or any(x in item["filename"].lower() for x in ["runt", "rund", "cirkel", "cirkular", "round"])
                    if is_table_round != is_rug_round:
                        continue
            
            if relax_level == 0:
                if (item["filename"] in unfeatured_ids) and style_ok and tone_ok and wood_ok: return item
            elif relax_level == 1:
                if style_ok and tone_ok and wood_ok: return item
            elif relax_level == 2:
                if (item["filename"] in unfeatured_ids) and style_ok and wood_ok: return item
            elif relax_level == 3:
                if style_ok and wood_ok: return item
            elif relax_level == 4:
                if (item["filename"] in unfeatured_ids) and tone_ok and wood_ok: return item
            elif relax_level == 5:
                if tone_ok and wood_ok: return item
            elif relax_level == 6:
                if (item["filename"] in unfeatured_ids) and wood_ok: return item
            elif relax_level == 7:
                if wood_ok: return item
            elif relax_level == 8:
                if item["filename"] in unfeatured_ids: return item
            elif relax_level == 9:
                return item
        return None

    def fill_empty_slots(pkg, allowed_ids):
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
                    comp = find_matching_companion(cats, exclude, anchor_item, relax, allowed_ids)
                    if comp:
                        pkg[slot_name] = comp
                        break

    def recount_usages(packages):
        for k in db.keys():
            usage_counts[k] = 0
        for pkg in packages:
            for slot, item in pkg.items():
                if slot not in ['room_type', 'relax_level', 'seed'] and item is not None:
                    fn = item['filename']
                    usage_counts[fn] = usage_counts.get(fn, 0) + 1

    furniture_seeds = [s for s in db.keys() if get_item_category(s, db[s]) != "rug"]
    rug_seeds = [s for s in db.keys() if get_item_category(s, db[s]) == "rug"]
    
    seeds = []
    for s in sorted(furniture_seeds):
        seeds.extend([s] * 4)
    for s in sorted(rug_seeds):
        seeds.extend([s] * 4)
        
    packages = []
    for idx, seed_id in enumerate(seeds):
        allowed_ids = get_allowed_items_for_idx(idx)
        seed_item = db[seed_id]
        seed_cat = get_item_category(seed_id, seed_item)
        
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
        else:
            room_type = "dining"
            
        matched_pkg = None
        for relax in range(10):
            exclude_ids = {seed_id}
            pkg = {"seed": seed_item, "room_type": room_type, "relax_level": relax}
            
            if room_type == "dining":
                dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], exclude_ids, seed_item, relax, allowed_ids)
                if dt: exclude_ids.add(dt["filename"])
                dc = seed_item if seed_cat == "dining_chair" else find_matching_companion(["dining_chair"], exclude_ids, seed_item, relax, allowed_ids)
                if dc: exclude_ids.add(dc["filename"])
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], exclude_ids, dt if dt else seed_item, relax, allowed_ids)
                if rug: exclude_ids.add(rug["filename"])
                pl = seed_item if seed_cat == "pendant_lamp" else None
                if pl: exclude_ids.add(pl["filename"])
                bg = find_matching_companion(["cabinet", "dresser", "sideboard", "bookcase"], exclude_ids, seed_item, relax, allowed_ids)
                if bg: exclude_ids.add(bg["filename"])
                if dt and dc and rug:
                    pkg.update({"dining_table": dt, "dining_chair": dc, "rug": rug, "pendant_lamp": pl, "background_storage": bg})
                    matched_pkg = pkg
                    break
            elif room_type == "living_seating":
                sofa = seed_item if seed_cat == "sofa" else find_matching_companion(["sofa"], exclude_ids, seed_item, relax, allowed_ids)
                if sofa: exclude_ids.add(sofa["filename"])
                ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], exclude_ids, seed_item, relax, allowed_ids)
                if ac: exclude_ids.add(ac["filename"])
                ct = seed_item if seed_cat == "coffeetable" else find_matching_companion(["coffeetable"], exclude_ids, seed_item, relax, allowed_ids)
                if ct: exclude_ids.add(ct["filename"])
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], exclude_ids, seed_item, relax, allowed_ids)
                if rug: exclude_ids.add(rug["filename"])
                fl = seed_item if seed_cat == "floor_lamp" else None
                if fl: exclude_ids.add(fl["filename"])
                bg = find_matching_companion(["cabinet", "sideboard"], exclude_ids, seed_item, relax, allowed_ids)
                if bg: exclude_ids.add(bg["filename"])
                if sofa and ct and rug:
                    pkg.update({"sofa": sofa, "armchair": ac, "coffeetable": ct, "rug": rug, "floor_lamp": fl, "background_storage": bg})
                    matched_pkg = pkg
                    break
            elif room_type == "living_storage":
                ps = seed_item if seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard"] else find_matching_companion(["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard"], exclude_ids, seed_item, relax, allowed_ids)
                if ps: exclude_ids.add(ps["filename"])
                ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], exclude_ids, seed_item, relax, allowed_ids)
                if ac: exclude_ids.add(ac["filename"])
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], exclude_ids, seed_item, relax, allowed_ids)
                if rug: exclude_ids.add(rug["filename"])
                tl = seed_item if seed_cat == "table_lamp" else None
                if tl: exclude_ids.add(tl["filename"])
                if ps and rug:
                    pkg.update({"primary_storage": ps, "armchair": ac, "rug": rug, "table_lamp": tl})
                    matched_pkg = pkg
                    break
            elif room_type == "office":
                desk = seed_item if seed_cat == "desk" else find_matching_companion(["desk"], exclude_ids, seed_item, relax, allowed_ids)
                if desk: exclude_ids.add(desk["filename"])
                dc = find_matching_companion(["desk_chair", "dining_chair", "armchair"], exclude_ids, seed_item, relax, allowed_ids)
                if dc: exclude_ids.add(dc["filename"])
                bc = find_matching_companion(["bookcase", "cabinet", "dresser"], exclude_ids, seed_item, relax, allowed_ids)
                if bc: exclude_ids.add(bc["filename"])
                tl = seed_item if seed_cat == "table_lamp" else None
                if tl: exclude_ids.add(tl["filename"])
                if desk and dc:
                    pkg.update({"desk": desk, "desk_chair": dc, "bookcase": bc, "table_lamp": tl})
                    matched_pkg = pkg
                    break
            elif room_type == "bedroom":
                bst = seed_item if seed_cat == "bedside_table" else find_matching_companion(["bedside_table"], exclude_ids, seed_item, relax, allowed_ids)
                if bst: exclude_ids.add(bst["filename"])
                bed = find_matching_companion(["sofa"], exclude_ids, seed_item, relax, allowed_ids)
                if bed: exclude_ids.add(bed["filename"])
                dr = find_matching_companion(["dresser", "cabinet"], exclude_ids, seed_item, relax, allowed_ids)
                if dr: exclude_ids.add(dr["filename"])
                tl = seed_item if seed_cat == "table_lamp" else None
                if tl: exclude_ids.add(tl["filename"])
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], exclude_ids, seed_item, relax, allowed_ids)
                if rug: exclude_ids.add(rug["filename"])
                if bst and rug:
                    pkg.update({"bedside_table": bst, "bed": bed, "dresser": dr, "table_lamp": tl, "rug": rug})
                    matched_pkg = pkg
                    break
            elif room_type == "bar":
                bs = seed_item if seed_cat == "barstool" else find_matching_companion(["barstool"], exclude_ids, seed_item, relax, allowed_ids)
                if bs: exclude_ids.add(bs["filename"])
                bt = seed_item if seed_cat == "bartable" else find_matching_companion(["bartable", "dining_table"], exclude_ids, seed_item, relax, allowed_ids)
                if bt: exclude_ids.add(bt["filename"])
                pl = seed_item if seed_cat == "pendant_lamp" else None
                if pl: exclude_ids.add(pl["filename"])
                rug = find_matching_companion(["rug"], exclude_ids, bt if bt else seed_item, relax, allowed_ids)
                if rug: exclude_ids.add(rug["filename"])
                bg = find_matching_companion(["cabinet", "sideboard"], exclude_ids, seed_item, relax, allowed_ids)
                if bg: exclude_ids.add(bg["filename"])
                if bs and rug:
                    pkg.update({"barstool": bs, "bartable": bt, "pendant_lamp": pl, "rug": rug, "background_storage": bg})
                    matched_pkg = pkg
                    break
                    
        if matched_pkg:
            for slot, item in matched_pkg.items():
                if slot not in ["room_type", "relax_level", "seed"] and item is not None:
                    unfeatured_ids.discard(item["filename"])
            packages.append(matched_pkg)
            recount_usages(packages)
        else:
            packages.append({"seed": seed_item, "room_type": room_type, "relax_level": 10})
            recount_usages(packages)

    for p_idx, pkg in enumerate(packages):
        allowed_ids = get_allowed_items_for_idx(p_idx)
        fill_empty_slots(pkg, allowed_ids)
        recount_usages(packages)

    # Now split them and count batches
    IMAGE_LIMIT = 185
    batches = []
    current_images = set()
    current_pkg_count = 0
    
    for pkg in packages:
        # Collect unique images used in this package
        row_images = set()
        for slot, item in pkg.items():
            if slot not in ["room_type", "relax_level"] and item is not None:
                row_images.add(item["filename"])
                
        future_images = current_images.union(row_images)
        if len(future_images) > IMAGE_LIMIT and current_pkg_count > 0:
            batches.append(len(current_images))
            current_images = row_images
            current_pkg_count = 1
        else:
            current_images = future_images
            current_pkg_count += 1
            
    if current_pkg_count > 0:
        batches.append(len(current_images))
        
    return len(batches), batches

if __name__ == "__main__":
    # Test different setups
    print("Testing original settings (batch_size=180, shift=5)...")
    original_window_sizes = {
        "rug": 20, "dining_chair": 20, "armchair": 15, "coffeetable": 15, "dining_table": 15,
        "tv_bench": 10, "cabinet": 10, "dresser": 10, "sideboard": 10, "bookcase": 10,
        "shoe_cabinet": 10, "bedside_table": 10, "table_lamp": 10, "pendant_lamp": 10,
        "floor_lamp": 5, "desk": 10, "desk_chair": 10, "sofa": 15, "barstool": 15, "bartable": 5
    }
    
    batches_cnt, details = run_simulation(original_window_sizes, 180, 5)
    print(f"Result: {batches_cnt} batches. Details (unique images per batch): {details}")
    
    print("\nTesting smaller companion window sizes (window sizes halved, batch_size=360, shift=10)...")
    smaller_windows = {
        "rug": 10, "dining_chair": 10, "armchair": 8, "coffeetable": 8, "dining_table": 8,
        "tv_bench": 5, "cabinet": 5, "dresser": 5, "sideboard": 5, "bookcase": 5,
        "shoe_cabinet": 5, "bedside_table": 5, "table_lamp": 5, "pendant_lamp": 5,
        "floor_lamp": 3, "desk": 5, "desk_chair": 5, "sofa": 8, "barstool": 8, "bartable": 3
    }
    batches_cnt, details = run_simulation(smaller_windows, 360, 10)
    print(f"Result: {batches_cnt} batches. Details (unique images per batch): {details}")

    print("\nTesting even smaller companion window sizes (batch_size=600, shift=20)...")
    even_smaller_windows = {
        "rug": 10, "dining_chair": 6, "armchair": 5, "coffeetable": 5, "dining_table": 5,
        "tv_bench": 3, "cabinet": 3, "dresser": 3, "sideboard": 3, "bookcase": 3,
        "shoe_cabinet": 3, "bedside_table": 3, "table_lamp": 3, "pendant_lamp": 3,
        "floor_lamp": 2, "desk": 3, "desk_chair": 3, "sofa": 5, "barstool": 5, "bartable": 2
    }
    batches_cnt, details = run_simulation(even_smaller_windows, 600, 20)
    print(f"Result: {batches_cnt} batches. Details (unique images per batch): {details}")

    print("\nTesting extremely small companion window sizes (batch_size=800, shift=30)...")
    extreme_windows = {
        "rug": 5, "dining_chair": 3, "armchair": 3, "coffeetable": 3, "dining_table": 3,
        "tv_bench": 2, "cabinet": 2, "dresser": 2, "sideboard": 2, "bookcase": 2,
        "shoe_cabinet": 2, "bedside_table": 2, "table_lamp": 2, "pendant_lamp": 2,
        "floor_lamp": 2, "desk": 2, "desk_chair": 2, "sofa": 3, "barstool": 3, "bartable": 2
    }
    batches_cnt, details = run_simulation(extreme_windows, 800, 30)
    print(f"Result: {batches_cnt} batches. Details (unique images per batch): {details}")
