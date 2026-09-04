import json
import os
import sys

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
with open(DB_PATH, "r", encoding="utf-8") as f:
    db = json.load(f)

# Filters and categories
CAT_KEY = 'typ_av_möbel'
WOOD_KEY = 'träslag'
MAT_KEY = 'tyg_material'
TONE_KEY = 'färgton'
STYLE_KEY = 'stil_estetik'

def clean_str(s: str) -> str:
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
    for c, r in repl.items():
        s = s.replace(c, r)
    return s.lower()

def should_skip_item(filename: str) -> bool:
    fname = filename.lower()
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    cleaned_fname = clean_str(fname)
    for kw in skip_keywords:
        if kw in fname or clean_str(kw) in cleaned_fname:
            return True
    return False

active_db = {k: v for k, v in db.items() if not should_skip_item(k)}
for filename, item in active_db.items():
    item["filename"] = filename

target_seed = "0451_byrå-nordisk-grå-1-26U-wonder.webp"
seed_item = active_db[target_seed]

# Build items_by_cat
def get_item_category(filename: str, item: dict) -> str:
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

items_by_cat = {}
for fname, item in active_db.items():
    cat = get_item_category(fname, item)
    items_by_cat.setdefault(cat, []).append(item)

usage_counts = {k: 0 for k in active_db.keys()}
unfeatured_ids = set(active_db.keys())

def find_matching_companion(cats_to_search, items_by_cat, unfeatured_ids, exclude_ids, anchor_item, relax_level):
    candidates = []
    for cat in cats_to_search:
        candidates.extend(items_by_cat.get(cat, []))
        
    # Sort candidates
    def sort_key(x):
        is_unfeatured = x["filename"] in unfeatured_ids
        usage = usage_counts.get(x["filename"], 0)
        return (0 if is_unfeatured else 1, usage, x["filename"])
        
    sorted_candidates = sorted(candidates, key=sort_key)
    
    anchor_style = anchor_item["metadata"].get(STYLE_KEY)
    anchor_tone = anchor_item["metadata"].get(TONE_KEY)
    anchor_wood = anchor_item["metadata"].get(WOOD_KEY)
    
    for item in sorted_candidates:
        if item["filename"] in exclude_ids:
            continue
            
        i_style = item["metadata"].get(STYLE_KEY)
        i_tone = item["metadata"].get(TONE_KEY)
        i_wood = item["metadata"].get(WOOD_KEY)
        
        style_ok = i_style == anchor_style
        tone_ok = i_tone == anchor_tone
        
        def woods_harmonize(w1, w2):
            if not w1 or not w2 or w1 == 'inget' or w2 == 'inget': return True
            if w1 in {'svart metall', 'marmor', 'vit'} or w2 in {'svart metall', 'marmor', 'vit'}: return True
            if w1 in {'ek', 'ask', 'natur'} and w2 in {'ek', 'ask', 'natur'}: return True
            if w1 in {'valnöt', 'mörkbrun'} and w2 in {'valnöt', 'mörkbrun'}: return True
            return False
            
        wood_ok = woods_harmonize(anchor_wood, i_wood)
        
        is_unfeatured = item["filename"] in unfeatured_ids
        
        if relax_level == 0:
            if is_unfeatured and style_ok and tone_ok and wood_ok: return item
        elif relax_level == 1:
            if style_ok and tone_ok and wood_ok: return item
        elif relax_level == 2:
            if is_unfeatured and style_ok and wood_ok: return item
        elif relax_level == 3:
            if style_ok and wood_ok: return item
        elif relax_level == 4:
            if is_unfeatured and tone_ok and wood_ok: return item
        elif relax_level == 5:
            if tone_ok and wood_ok: return item
        elif relax_level == 6:
            if is_unfeatured and wood_ok: return item
        elif relax_level == 7:
            if wood_ok: return item
        elif relax_level == 8:
            if is_unfeatured: return item
        elif relax_level == 9:
            return item
    return None

print("\n--- TRACING CURATION LOOP FOR SEED ---")
seed_cat = get_item_category(target_seed, seed_item)
print(f"seed_cat: {seed_cat}")

matched = False
for relax in range(10):
    exclude_ids = {target_seed}
    ps = seed_item if seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard"] else find_matching_companion(["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
    if ps: exclude_ids.add(ps["filename"])
    
    ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
    if ac: exclude_ids.add(ac["filename"])
    
    # Wait! In generate_batch1_rooms.py, is the search for rug correctly passed?
    # rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
    rug = find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
    if rug: exclude_ids.add(rug["filename"])
    
    print(f"Relax {relax}: ps={ps['filename'] if ps else None}, ac={ac['filename'] if ac else None}, rug={rug['filename'] if rug else None}")
    
    if ps and rug:
        print("SUCCESSFUL MATCH AT RELAX", relax)
        matched = True
        break

if not matched:
    print("❌ FAILED TO MATCH RUG AT ANY RELAX LEVEL!")
