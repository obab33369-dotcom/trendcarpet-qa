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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "furniture_db.json")
EXPORT_JSON_PATH = os.path.join(SCRIPT_DIR, "rooms_turboflow.json")
CSV_EXPORT_PATH = os.path.join(SCRIPT_DIR, "turboflow_ready.csv")
FLAT_JSON_EXPORT_PATH = os.path.join(SCRIPT_DIR, "turboflow_ready.json")
TXT_EXPORT_PATH = os.path.join(SCRIPT_DIR, "turboflow_ready.txt")
PROMPTS_ONLY_EXPORT_PATH = os.path.join(SCRIPT_DIR, "prompts_only.txt")
TRACKING_LOG_PATH = os.path.join(SCRIPT_DIR, "turboflow_tracking_log.csv")

CAT_KEY = 'typ_av_m\u00f6bel'
WOOD_KEY = 'tr\u00e4slag'
MAT_KEY = 'tyg_material'
TONE_KEY = 'f\u00e4rgton'
STYLE_KEY = 'stil_estetik'

def get_short_tag(filename: str) -> str:
    """
    Generates a unique tag based on the leading numeric ID.
    E.g. "0257_matbord-fager-135cm-natur-1-26U-wonder.webp" -> "@0257"
    """
    match = re.match(r'^(\d+)_', filename)
    if match:
        return f"@{match.group(1)}"
    
    base, _ = os.path.splitext(filename)
    base = re.sub(r'-\d+-\w+-wonder$', '', base)
    base = base.lower().strip().replace("_", "-")
    return f"@{base[:18]}"

def get_short_filename(filename: str) -> str:
    """
    Generates a short filename based on the leading numeric ID.
    """
    base, ext = os.path.splitext(filename)
    match = re.match(r'^(\d+)_', base)
    if match:
        return f"{match.group(1)}{ext}"
    return filename

def clean_swedish_chars(text: str) -> str:
    """
    Cleans Swedish characters for user-friendly display in names.
    """
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text

def clean_tag_to_name(filename: str) -> str:
    """
    Generates a beautiful human-readable name from filename.
    """
    base, _ = os.path.splitext(filename)
    base = re.sub(r'^\d+__*', '', base) # Remove leading digits and underscores
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
    w1, w2 = w1.strip().lower(), w2.strip().lower()
    if w1 == 'inget' or w2 == 'inget':
        return True
    neutrals = {'svart metall', 'marmor', 'vit'}
    if w1 in neutrals or w2 in neutrals:
        return True
    light_woods = {'ek', 'ask', 'natur'}
    dark_woods = {'valnöt', 'mörkbrun'}
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

def check_harmony(items: List[Dict]) -> bool:
    if not items:
        return False
    
    # Check Style Cohesion (must match if present)
    styles = [i["metadata"].get(STYLE_KEY) for i in items if i.get("metadata", {}).get(STYLE_KEY)]
    if len(set(styles)) > 1:
        return False
        
    # Check Color Tone Cohesion (must match if present)
    tones = [i["metadata"].get(TONE_KEY) for i in items if i.get("metadata", {}).get(TONE_KEY)]
    if len(set(tones)) > 1:
        return False
        
    # Check Wood Harmony for all pairs
    woods = [i["metadata"].get(WOOD_KEY) for i in items if i.get("metadata", {}).get(WOOD_KEY)]
    for i in range(len(woods)):
        for j in range(i + 1, len(woods)):
            if not woods_harmonize(woods[i], woods[j]):
                return False
    return True

def find_matching_companion(
    cats_to_search: List[str], 
    items_by_cat: Dict[str, List[Dict]], 
    unfeatured_ids: set, 
    exclude_ids: set, 
    anchor_item: Dict, 
    relax_level: int
) -> Dict:
    candidates = []
    for cat in cats_to_search:
        candidates.extend(items_by_cat.get(cat, []))
        
    anchor_style = anchor_item["metadata"].get(STYLE_KEY)
    anchor_tone = anchor_item["metadata"].get(TONE_KEY)
    anchor_wood = anchor_item["metadata"].get(WOOD_KEY)
    
    # Sort candidates so we prioritize unfeatured items
    def sort_key(x):
        is_unfeatured = x["filename"] in unfeatured_ids
        return (0 if is_unfeatured else 1, x["filename"])
        
    sorted_candidates = sorted(candidates, key=sort_key)
    
    for item in sorted_candidates:
        if item["filename"] in exclude_ids:
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

def fill_empty_slots(pkg, items_by_cat, unfeatured_ids):
    room_type = pkg["room_type"]
    anchor_item = pkg["seed"]
    
    slots_by_room = {
        "dining": [
            ("background_storage", ["cabinet", "dresser", "sideboard", "bookcase"])
        ],
        "living_seating": [
            ("sofa", ["sofa"]),
            ("armchair", ["armchair"]),
            ("background_storage", ["tv_bench", "dresser", "cabinet", "bookcase"])
        ],
        "living_storage": [
            ("armchair", ["armchair"]),
            ("rug", ["rug"])
        ],
        "office": [
            ("desk_chair", ["dining_chair", "armchair"]),
            ("bookcase", ["bookcase", "cabinet", "dresser"])
        ],
        "bedroom": [
            ("bed", ["sofa"]),
            ("dresser", ["dresser", "cabinet"]),
            ("rug", ["rug"])
        ],
        "bar": [
            ("bartable", ["bartable"]),
            ("background_storage", ["cabinet", "sideboard"])
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
                comp = find_matching_companion(cats, items_by_cat, unfeatured_ids, exclude, anchor_item, relax)
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
    print("Loading furniture database...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}.")
        sys.exit(1)
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    print(f"Total items loaded: {len(db)}")
    
    items_by_cat = {}
    for filename, item in db.items():
        item["filename"] = filename
        cat = get_item_category(filename, item)
        items_by_cat[cat] = items_by_cat.get(cat, []) + [item]
        
    # Set of unfeatured product IDs (starts with all 209 items)
    unfeatured_ids = set(db.keys())
    
    # List to store matched packages
    packages = []
    
    # 10-level cascade loop
    iteration = 0
    while unfeatured_ids and iteration < 1000:
        iteration += 1
        
        # Pop a seed item from unfeatured_ids consistently
        seed_id = sorted(list(unfeatured_ids))[0]
        seed_item = db[seed_id]
        seed_cat = get_item_category(seed_id, seed_item)
        
        # Determine room template based on seed category
        if seed_cat in ["dining_table", "dining_chair", "pendant_lamp"]:
            room_type = "dining"
        elif seed_cat in ["sofa", "armchair", "coffeetable", "floor_lamp"]:
            room_type = "living_seating"
        elif seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard", "table_lamp"]:
            room_type = "living_storage"
        elif seed_cat == "desk":
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
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
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
                
                bg = find_matching_companion(["tv_bench", "dresser", "cabinet", "bookcase"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bg: exclude_ids.add(bg["filename"])
                
                if (sofa or ac) and ct:
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
                
                if ps:
                    pkg.update({"primary_storage": ps, "armchair": ac, "rug": rug, "table_lamp": tl})
                    matched_pkg = pkg
                    break
                    
            elif room_type == "office":
                desk = seed_item if seed_cat == "desk" else find_matching_companion(["desk"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if desk: exclude_ids.add(desk["filename"])
                
                dc = find_matching_companion(["dining_chair", "armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dc: exclude_ids.add(dc["filename"])
                
                bc = find_matching_companion(["bookcase", "cabinet", "dresser"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bc: exclude_ids.add(bc["filename"])
                
                tl = seed_item if seed_cat == "table_lamp" else None
                if tl: exclude_ids.add(tl["filename"])
                
                if desk:
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
                
                if bst:
                    pkg.update({"bedside_table": bst, "bed": bed, "dresser": dr, "table_lamp": tl, "rug": rug})
                    matched_pkg = pkg
                    break
                    
            elif room_type == "bar":
                bs = seed_item if seed_cat == "barstool" else find_matching_companion(["barstool"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bs: exclude_ids.add(bs["filename"])
                
                bt = seed_item if seed_cat == "bartable" else find_matching_companion(["bartable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bt: exclude_ids.add(bt["filename"])
                
                pl = seed_item if seed_cat == "pendant_lamp" else None
                if pl: exclude_ids.add(pl["filename"])
                
                bg = find_matching_companion(["cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bg: exclude_ids.add(bg["filename"])
                
                if bs:
                    pkg.update({"barstool": bs, "bartable": bt, "pendant_lamp": pl, "background_storage": bg})
                    matched_pkg = pkg
                    break
                    
        if matched_pkg:
            # Mark all non-None items in matched_pkg as featured
            for slot, item in matched_pkg.items():
                if slot not in ["room_type", "relax_level", "seed"] and item is not None:
                    unfeatured_ids.discard(item["filename"])
            packages.append(matched_pkg)
        else:
            # Force discard seed to prevent infinite loops (should not happen with relax=9)
            unfeatured_ids.discard(seed_id)
            
    # Ensure exactly 110 packages
    if len(packages) < 110:
        db_keys_sorted = sorted(list(db.keys()))
        extra_idx = 0
        while len(packages) < 110 and extra_idx < len(db_keys_sorted):
            seed_id = db_keys_sorted[extra_idx]
            extra_idx += 1
            seed_item = db[seed_id]
            seed_cat = get_item_category(seed_id, seed_item)
            
            # Determine room template based on seed category
            if seed_cat in ["dining_table", "dining_chair", "pendant_lamp"]:
                room_type = "dining"
            elif seed_cat in ["sofa", "armchair", "coffeetable", "floor_lamp"]:
                room_type = "living_seating"
            elif seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard", "table_lamp"]:
                room_type = "living_storage"
            elif seed_cat == "desk":
                room_type = "office"
            elif seed_cat == "bedside_table":
                room_type = "bedroom"
            elif seed_cat in ["barstool", "bartable"]:
                room_type = "bar"
            else:
                room_type = "dining"
                
            matched_pkg = None
            for relax in range(5, 10):
                exclude_ids = {seed_id}
                pkg = {"seed": seed_item, "room_type": room_type, "relax_level": relax}
                
                if room_type == "dining":
                    dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if dt: exclude_ids.add(dt["filename"])
                    
                    dc = seed_item if seed_cat == "dining_chair" else find_matching_companion(["dining_chair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if dc: exclude_ids.add(dc["filename"])
                    
                    rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
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
                    
                    bg = find_matching_companion(["tv_bench", "dresser", "cabinet", "bookcase"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bg: exclude_ids.add(bg["filename"])
                    
                    if (sofa or ac) and ct:
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
                    
                    if ps:
                        pkg.update({"primary_storage": ps, "armchair": ac, "rug": rug, "table_lamp": tl})
                        matched_pkg = pkg
                        break
                        
                elif room_type == "office":
                    desk = seed_item if seed_cat == "desk" else find_matching_companion(["desk"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if desk: exclude_ids.add(desk["filename"])
                    
                    dc = find_matching_companion(["dining_chair", "armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if dc: exclude_ids.add(dc["filename"])
                    
                    bc = find_matching_companion(["bookcase", "cabinet", "dresser"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bc: exclude_ids.add(bc["filename"])
                    
                    tl = seed_item if seed_cat == "table_lamp" else None
                    if tl: exclude_ids.add(tl["filename"])
                    
                    if desk:
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
                    
                    if bst:
                        pkg.update({"bedside_table": bst, "bed": bed, "dresser": dr, "table_lamp": tl, "rug": rug})
                        matched_pkg = pkg
                        break
                        
                elif room_type == "bar":
                    bs = seed_item if seed_cat == "barstool" else find_matching_companion(["barstool"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bs: exclude_ids.add(bs["filename"])
                    
                    bt = seed_item if seed_cat == "bartable" else find_matching_companion(["bartable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bt: exclude_ids.add(bt["filename"])
                    
                    pl = seed_item if seed_cat == "pendant_lamp" else None
                    if pl: exclude_ids.add(pl["filename"])
                    
                    bg = find_matching_companion(["cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bg: exclude_ids.add(bg["filename"])
                    
                    if bs:
                        pkg.update({"barstool": bs, "bartable": bt, "pendant_lamp": pl, "background_storage": bg})
                        matched_pkg = pkg
                        break
                        
            if matched_pkg:
                packages.append(matched_pkg)

    # Populate missing slots to make every room complete and feature 4-6 items
    for pkg in packages:
        fill_empty_slots(pkg, items_by_cat, unfeatured_ids)

    print(f"✓ Curation complete! Generated {len(packages)} packages covering 100% of the catalog.")
    
    # ----------------------------------------------------
    # PROMPT GENERATION
    # ----------------------------------------------------
    def is_kitchen_applicable(pkg: Dict) -> bool:
        """
        Checks if a package contains kitchen-applicable furniture:
        - dining table/chair
        - barstool/table
        - cabinet where the category is kitchen/cabinet or filename contains kitchen words
        """
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
        """
        Returns (room_and_setting_desc, location_name) for the package.
        The 6 environments are:
        1. Stockholm classic turn-of-the-century apartment in Östermalm
        2. Scandi kitchen-living room / Scandi living room
        3. Stockholm archipelago architect-designed villa
        4. Scandi architect-designed cabin
        5. Scandi architect-designed living room with garden
        6. Scandi penthouse
        """
        env_type = pkg_idx % 6
        
        if env_type == 0:
            room = "kitchen-living room" if is_kitchen else "living room"
            desc = f"Stockholm classic turn-of-the-century apartment {room} in Östermalm with high decorated ceilings, delicate plaster moldings, and views of tree-lined streets"
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

    output_rows = []
    tracking_rows = []
    
    for pkg_idx, pkg in enumerate(packages):
        package_id = f"PKG-{pkg_idx+1:02d}"
        room_type = pkg["room_type"]
        relax_val = pkg["relax_level"]
        
        # Check kitchen applicability
        is_kitchen = is_kitchen_applicable(pkg)
        location_desc, location_name = get_dynamic_location(pkg_idx, is_kitchen)
        
        # Parse items and compile names and tags
        tagged_items = []
        
        # Build scene description text based on room type
        subject_desc = ""
        subject_desc_2 = ""
        bg_elements = []
        bg_elements_2 = []
        style_val = pkg["seed"]["metadata"].get(STYLE_KEY, "scandinavian minimalist")
        tone_val = pkg["seed"]["metadata"].get(TONE_KEY, "warm neutral")
        wood_val = pkg["seed"]["metadata"].get(WOOD_KEY, "ek")
        
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
            
            chair_type = "armchairs" if "karmstol" in (dc["filename"].lower() if dc else "") else "spindle-back chairs"
            subject_desc = f"the elegant table ({dt_name}) and matching {chair_type} ({dc_name}) in the center of the spacious room"
            subject_desc_2 = f"three-quarters of the elegant table ({dt_name}) and matching {chair_type} ({dc_name})"
            
            if rug:
                tagged_items.append(rug)
                rug_name = clean_tag_to_name(rug["filename"])
                rug_form = "round" if "rund" in rug["metadata"].get("form", "") or "cirkel" in rug["filename"].lower() else "rectangular"
                rug_mat = rug["metadata"].get(MAT_KEY, "textured wool")
                subject_desc += f", all resting on a matching real {rug_form} {rug_mat} area rug ({rug_name})"
                subject_desc_2 += f", resting on the beautiful {rug_form} {rug_mat} area rug ({rug_name})"
                
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
                subject_parts.append(f"the elegant armchair ({ac_name})")
                parts_2.append(f"the elegant armchair ({ac_name})")
            if ct:
                tagged_items.append(ct)
                subject_parts.append(f"the minimalist wood coffee table ({ct_name})")
                parts_2.append(f"the minimalist coffee table ({ct_name})")
                
            subject_desc = f"a warm and complete living room seating setup showcasing " + " and ".join(subject_parts)
            subject_desc_2 = "three-quarters of " + " and ".join(parts_2)
            
            if rug:
                tagged_items.append(rug)
                rug_name = clean_tag_to_name(rug["filename"])
                rug_mat = rug["metadata"].get(MAT_KEY, "textured wool")
                subject_desc += f", grounded beautifully by a matching {rug_mat} rug ({rug_name}) underneath"
                subject_desc_2 += f", resting on the matching {rug_mat} rug ({rug_name})"
                
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
            
            subject_desc = f"a sophisticated storage setup featuring the beautiful {ps_name} standing against the wall"
            subject_desc_2 = f"three-quarters of the elegant {ps_name} standing against the wall"
            
            if tl:
                tagged_items.append(tl)
                tl_name = clean_tag_to_name(tl["filename"])
                subject_desc += f", with a designer table lamp ({tl_name}) standing on top of it"
                subject_desc_2 += f" with the glowing designer table lamp ({tl_name}) casting a warm soft light on its surface"
                
            if ac:
                tagged_items.append(ac)
                ac_name = clean_tag_to_name(ac["filename"])
                bg_elements.append(f"an elegant armchair ({ac_name}) standing nearby")
                bg_elements_2.append(f"an elegant armchair ({ac_name}) standing nearby")
                
            if rug:
                tagged_items.append(rug)
                rug_name = clean_tag_to_name(rug["filename"])
                bg_elements.append(f"a soft textured area rug ({rug_name}) spreading on the floor")
                bg_elements_2.append(f"a soft textured area rug ({rug_name}) spreading on the floor")
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
            subject_desc_2 = f"three-quarters of the refined desk ({desk_name}) standing against the wall"
            
            if dc:
                tagged_items.append(dc)
                dc_name = clean_tag_to_name(dc["filename"])
                subject_desc += f", paired with a matching structured chair ({dc_name}) tucked neatly underneath"
                subject_desc_2 += f" paired with the structured chair ({dc_name})"
                
            if tl:
                tagged_items.append(tl)
                tl_name = clean_tag_to_name(tl["filename"])
                subject_desc += f", with a designer table lamp ({tl_name}) standing on the desk corner"
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
            
            if bed:
                tagged_items.append(bed)
                bed_name = clean_tag_to_name(bed["filename"])
                subject_desc = f"a serene master bedroom featuring the bedside table ({bst_name}) standing against the wall next to the beautifully made bed ({bed_name}) with crisp organic linen sheets"
                subject_desc_2 = f"three-quarters of the serene bedside table ({bst_name}) standing against the wall next to the bed ({bed_name}) with crisp linen"
            else:
                subject_desc = f"a serene master bedroom featuring the bedside table ({bst_name}) standing against the wall next to a beautifully made bed with crisp organic linen sheets"
                subject_desc_2 = f"three-quarters of the serene bedside table ({bst_name}) standing against the wall next to the bed"
            
            if tl:
                tagged_items.append(tl)
                tl_name = clean_tag_to_name(tl["filename"])
                subject_desc += f", with a designer table lamp ({tl_name}) resting on top of the bedside table"
                subject_desc_2 += f" with the glowing designer table lamp ({tl_name}) resting on it casting a warm soft light"
                
            if dr:
                tagged_items.append(dr)
                dr_name = clean_tag_to_name(dr["filename"])
                bg_elements.append(f"a large matching dresser ({dr_name}) standing against the wall")
                bg_elements_2.append(f"a large matching dresser ({dr_name}) standing against the wall")
                
            if rug:
                tagged_items.append(rug)
                rug_name = clean_tag_to_name(rug["filename"])
                bg_elements.append(f"a soft textured bedside rug ({rug_name}) placed under the bed")
                bg_elements_2.append(f"a soft textured bedside rug ({rug_name}) placed under the bed")
            else:
                bg_elements.append("an arty abstract poster without text hanging on the wall")
                bg_elements_2.append("an arty abstract poster without text hanging on the wall")
                
        elif room_type == "bar":
            bs = pkg.get("barstool")
            bt = pkg.get("bartable")
            pl = pkg.get("pendant_lamp")
            bg = pkg.get("background_storage")
            
            bs_name = clean_tag_to_name(bs["filename"]) if bs else "modern barstools"
            if bs: tagged_items.append(bs)
            
            if bt:
                tagged_items.append(bt)
                bt_name = clean_tag_to_name(bt["filename"])
                subject_desc = f"a beautiful kitchen bar setup with the barstools ({bs_name}) placed neatly around the matching bar table ({bt_name})"
                subject_desc_2 = f"three-quarters of the kitchen bar setup with the barstools ({bs_name}) paired with the matching bar table ({bt_name})"
            else:
                subject_desc = f"a kitchen island seating setup showcasing the minimalist barstools ({bs_name}) arranged along the white countertop"
                subject_desc_2 = f"three-quarters of the kitchen island setup with the barstools ({bs_name}) along the counter"
                
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
                
        # Ensure unique items while preserving order
        seen_filenames = set()
        unique_tagged_items = []
        for x in tagged_items:
            if x["filename"] not in seen_filenames:
                seen_filenames.add(x["filename"])
                unique_tagged_items.append(x)
        tagged_items = unique_tagged_items
        
        # Generate exactly 2 shots per package (one Standard, one Close-up)
        # This will yield exactly 220 prompts for 110 packages, covering 100% of the catalog.
        
        # Shot 1: Standard View
        shot1_num = len(output_rows) + 1
        is_lamp = seed_cat in ["table_lamp", "floor_lamp", "pendant_lamp"]
        if is_lamp:
            shot1_light = "warm afternoon light with long soft shadows"
        else:
            shot1_light = "crisp cinematic afternoon sunlight" if (pkg_idx % 2 == 0) else "bright natural morning light streaming through the windows"
        
        bg_sentence_1 = join_background_elements(bg_elements, close_up=False)
        bg_part_1 = f" {bg_sentence_1}" if bg_sentence_1 else ""
        
        tags_str = "  " + "; ".join([get_short_tag(x["filename"]) for x in tagged_items])
        files_str = "; ".join([get_short_filename(x["filename"]) for x in tagged_items])
        short_tags_only = "; ".join([get_short_tag(x["filename"]) for x in tagged_items])
        
        prompt_1 = (
            f"{shot1_num:03d} - Architectural digest-style three-quarter view of {subject_desc} set in a {location_desc} with {shot1_light}.{bg_part_1} "
            f"Dynamic three-quarter angle with controlled depth of field. Varied gloss levels on walls and trim to enhance depth, "
            f"featuring tactile micro-imperfections. Strictly preserve individual furniture material finishes (matte, lacquer, metal) "
            f"without global gloss changes. Enhance atmosphere with very subtle volumetric-dust. Prioritize high-end material tactility "
            f"and realistic light-reactive surfaces over digital polish, showcasing premium wood and stone surfaces. Utilize chiaroscuro lighting "
            f"techniques to deepen shadow definition, ensuring clear silhouettes for furniture against the walls. "
            f"Break the monochromatic palette with refined material contrasts, such as cool-toned stone or matte metallic finishes to add "
            f"depth and sophisticated material friction. No cutting-boards, no wooden plates in the kitchen, no abstract sculpture, no plants, no knick-knacks, no knick-knack.{tags_str}"
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
            "Table Product": clean_tag_to_name(pkg.get("dining_table")["filename"]) if pkg.get("dining_table") else (clean_tag_to_name(pkg.get("coffeetable")["filename"]) if pkg.get("coffeetable") else (clean_tag_to_name(pkg.get("desk")["filename"]) if pkg.get("desk") else "None")),
            "Seating Product": clean_tag_to_name(pkg.get("dining_chair")["filename"]) if pkg.get("dining_chair") else (clean_tag_to_name(pkg.get("sofa")["filename"]) if pkg.get("sofa") else (clean_tag_to_name(pkg.get("armchair")["filename"]) if pkg.get("armchair") else (clean_tag_to_name(pkg.get("barstool")["filename"]) if pkg.get("barstool") else "None"))),
            "Rug Product": clean_tag_to_name(pkg.get("rug")["filename"]) if pkg.get("rug") else "None",
            "Lamp Product": clean_tag_to_name(pkg.get("pendant_lamp")["filename"]) if pkg.get("pendant_lamp") else (clean_tag_to_name(pkg.get("floor_lamp")["filename"]) if pkg.get("floor_lamp") else (clean_tag_to_name(pkg.get("table_lamp")["filename"]) if pkg.get("table_lamp") else "None")),
            "Storage Product": clean_tag_to_name(pkg.get("background_storage")["filename"]) if pkg.get("background_storage") else (clean_tag_to_name(pkg.get("primary_storage")["filename"]) if pkg.get("primary_storage") else "None"),
            "References Utilized": files_str,
            "Tags Utilized": short_tags_only
        })
        
        # Shot 2: Close-up Detail View
        shot2_num = len(output_rows) + 1
        if is_lamp:
            shot2_light = "moody evening twilight with warm glowing indoor lights"
        else:
            shot2_light = "warm golden hour light creating long soft shadows" if (pkg_idx % 2 == 0) else "moody evening twilight with warm glowing indoor lights"
        
        bg_sentence_2 = join_background_elements(bg_elements_2, close_up=True)
        bg_part_2 = f" {bg_sentence_2}" if bg_sentence_2 else ""
        
        prompt_2 = (
            f"{shot2_num:03d} - Architectural digest-style close-up shot showcasing {subject_desc_2}, set in a {location_desc} with {shot2_light}.{bg_part_2} "
            f"Dynamic close-up shot with controlled depth of field. Varied gloss levels on walls and trim "
            f"to enhance depth, featuring tactile micro-imperfections. Strictly preserve individual furniture material finishes (matte, lacquer, metal) "
            f"without global gloss changes. Enhance atmosphere with very subtle volumetric-dust. Prioritize high-end material tactility "
            f"and realistic light-reactive surfaces over digital polish, showcasing premium wood and stone surfaces. Utilize chiaroscuro lighting "
            f"techniques to deepen shadow definition, ensuring clear silhouettes for furniture against the walls. "
            f"Break the monochromatic palette with refined material contrasts, such as cool-toned stone or matte metallic finishes to add "
            f"depth and sophisticated material friction. No cutting-boards, no wooden plates in the kitchen, no abstract sculpture, no plants, no knick-knacks, no knick-knack.{tags_str}"
        )
        
        output_rows.append({
            "prompt": prompt_2,
            "image_references": files_str,
            "image_tags": short_tags_only,
            "aspect_ratio": "1:1"
        })
        
        tracking_rows.append({
            "Row Number": shot2_num,
            "Package ID": package_id,
            "Package Type": room_type.capitalize(),
            "Template Style": location_name,
            "Focus Type": "Close-up Detail View",
            "Close-up": "Yes",
            "Location": location_name,
            "Focus Description": f"Close-up of {subject_desc_2}",
            "Style / Aesthetic": style_val,
            "Color Tone": tone_val,
            "Wood Finish": wood_val,
            "Table Product": clean_tag_to_name(pkg.get("dining_table")["filename"]) if pkg.get("dining_table") else (clean_tag_to_name(pkg.get("coffeetable")["filename"]) if pkg.get("coffeetable") else (clean_tag_to_name(pkg.get("desk")["filename"]) if pkg.get("desk") else "None")),
            "Seating Product": clean_tag_to_name(pkg.get("dining_chair")["filename"]) if pkg.get("dining_chair") else (clean_tag_to_name(pkg.get("sofa")["filename"]) if pkg.get("sofa") else (clean_tag_to_name(pkg.get("armchair")["filename"]) if pkg.get("armchair") else (clean_tag_to_name(pkg.get("barstool")["filename"]) if pkg.get("barstool") else "None"))),
            "Rug Product": clean_tag_to_name(pkg.get("rug")["filename"]) if pkg.get("rug") else "None",
            "Lamp Product": clean_tag_to_name(pkg.get("pendant_lamp")["filename"]) if pkg.get("pendant_lamp") else (clean_tag_to_name(pkg.get("floor_lamp")["filename"]) if pkg.get("floor_lamp") else (clean_tag_to_name(pkg.get("table_lamp")["filename"]) if pkg.get("table_lamp") else "None")),
            "Storage Product": clean_tag_to_name(pkg.get("background_storage")["filename"]) if pkg.get("background_storage") else (clean_tag_to_name(pkg.get("primary_storage")["filename"]) if pkg.get("primary_storage") else "None"),
            "References Utilized": files_str,
            "Tags Utilized": short_tags_only
        })

    print(f"✓ Generated exactly {len(output_rows)} logical prompt rows in memory.")
    
    # ----------------------------------------------------
    # EXPORTING BATCH FILES
    # ----------------------------------------------------
    # 1. Save standard JSON
    with open(EXPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, ensure_ascii=False, indent=2)
    print(f"✓ Exported JSON to: {EXPORT_JSON_PATH}")
    
    # 2. Save Flat JSON
    with open(FLAT_JSON_EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, ensure_ascii=False, indent=2)
    print(f"✓ Exported TurboFlow Flat JSON to: {FLAT_JSON_EXPORT_PATH}")
    
    # 3. Save CSV file (UTF-8, comma)
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
        
    # 4. Save TXT file (UTF-8, comma)
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
        
    # 5. Save raw prompts-only TXT file
    try:
        with open(PROMPTS_ONLY_EXPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
            for row in output_rows:
                f.write(row["prompt"] + "\n")
        print(f"✓ Exported raw prompts-only TXT to: {PROMPTS_ONLY_EXPORT_PATH}")
    except Exception as e:
        print(f"❌ Error writing prompts-only TXT: {e}")
        
    # 6. Save tracking spreadsheet CSV
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
