import sys

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import re

FILE_PATH = "generate_batch2_rooms.py"

def patch():
    print("==================================================")
    print("       PATCHING GENERATE_BATCH2_ROOMS.PY          ")
    print("==================================================")
    
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Patch find_matching_companion to add the rug-table shape check
    target_match = """        # Match variables
        style_ok = i_style == anchor_style
        tone_ok = i_tone == anchor_tone
        wood_ok = woods_harmonize(anchor_wood, i_wood)"""
        
    replacement_match = """        # Match variables
        style_ok = i_style == anchor_style
        tone_ok = i_tone == anchor_tone
        wood_ok = woods_harmonize(anchor_wood, i_wood)
        
        # Shape constraint for rugs
        if "rug" in cats_to_search:
            anchor_cat = get_item_category(anchor_item["filename"], anchor_item)
            if anchor_cat in ["dining_table", "coffeetable"]:
                is_table_round = any(x in anchor_item["filename"].lower() for x in ["runt", "rund", "cirkel", "cirkular", "round"])
                rug_form = item["metadata"].get("form", "").strip().lower()
                is_rug_round = rug_form == "rund" or any(x in item["filename"].lower() for x in ["runt", "rund", "cirkel", "cirkular", "round"])
                if is_table_round != is_rug_round:
                    continue"""
                    
    if target_match in content:
        content = content.replace(target_match, replacement_match, 1)
        print("[OK] Successfully patched find_matching_companion with shape constraints.")
    else:
        print("[WARNING] Target match for find_matching_companion not found!")
        
    # 2. Patch the dining room rug matches
    # We will look for:
    # dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
    # ...
    # rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], ... seed_item, relax)
    # We want to replace the `seed_item` in `find_matching_companion(["rug"]` with `dt if dt else seed_item`
    
    # We can do a regex find and replace or a exact replace if we find the block
    # Let's print out the exact text we are replacing to be safe.
    
    # Let's use a regex to replace occurrences inside dining room blocks
    # Dining room blocks look like:
    # if room_type == "dining":
    # or: elif room_type == "dining":
    
    # Let's write a robust python replacement for the two blocks
    
    # Dining Block 1 (Line ~396):
    dining_target = """            if room_type == "dining":
                dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dt: exclude_ids.add(dt["filename"])
                
                dc = seed_item if seed_cat == "dining_chair" else find_matching_companion(["dining_chair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dc: exclude_ids.add(dc["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)"""
                
    dining_replacement = """            if room_type == "dining":
                dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dt: exclude_ids.add(dt["filename"])
                
                dc = seed_item if seed_cat == "dining_chair" else find_matching_companion(["dining_chair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if dc: exclude_ids.add(dc["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, dt if dt else seed_item, relax)"""
                
    if dining_target in content:
        content = content.replace(dining_target, dining_replacement, 1)
        print("[OK] Successfully patched dining block 1.")
    else:
        print("[WARNING] Dining block 1 target not found!")
        
    # Dining Block 2 (Line ~561):
    dining_target2 = """            if room_type == "dining":
                    dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if dt: exclude_ids.add(dt["filename"])
                    
                    dc = seed_item if seed_cat == "dining_chair" else find_matching_companion(["dining_chair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if dc: exclude_ids.add(dc["filename"])
                    
                    rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)"""
                    
    dining_replacement2 = """            if room_type == "dining":
                    dt = seed_item if seed_cat == "dining_table" else find_matching_companion(["dining_table"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if dt: exclude_ids.add(dt["filename"])
                    
                    dc = seed_item if seed_cat == "dining_chair" else find_matching_companion(["dining_chair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if dc: exclude_ids.add(dc["filename"])
                    
                    rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, dt if dt else seed_item, relax)"""
                    
    if dining_target2 in content:
        content = content.replace(dining_target2, dining_replacement2, 1)
        print("[OK] Successfully patched dining block 2.")
    else:
        # Let's try replacing them via a generic string replace if needed, or regex
        print("[WARNING] Dining block 2 target not found!")
        
    # Living Block 1 (Line ~420):
    living_target = """            elif room_type == "living_seating":
                sofa = seed_item if seed_cat == "sofa" else find_matching_companion(["sofa"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if sofa: exclude_ids.add(sofa["filename"])
                
                ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ac: exclude_ids.add(ac["filename"])
                
                ct = seed_item if seed_cat == "coffeetable" else find_matching_companion(["coffeetable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ct: exclude_ids.add(ct["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)"""
                
    living_replacement = """            elif room_type == "living_seating":
                sofa = seed_item if seed_cat == "sofa" else find_matching_companion(["sofa"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if sofa: exclude_ids.add(sofa["filename"])
                
                ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ac: exclude_ids.add(ac["filename"])
                
                ct = seed_item if seed_cat == "coffeetable" else find_matching_companion(["coffeetable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if ct: exclude_ids.add(ct["filename"])
                
                rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, ct if ct else seed_item, relax)"""
                
    if living_target in content:
        content = content.replace(living_target, living_replacement, 1)
        print("[OK] Successfully patched living block 1.")
    else:
        print("[WARNING] Living block 1 target not found!")
        
    # Living Block 2 (Line ~585):
    living_target2 = """            elif room_type == "living_seating":
                    sofa = seed_item if seed_cat == "sofa" else find_matching_companion(["sofa"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if sofa: exclude_ids.add(sofa["filename"])
                    
                    ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if ac: exclude_ids.add(ac["filename"])
                    
                    ct = seed_item if seed_cat == "coffeetable" else find_matching_companion(["coffeetable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if ct: exclude_ids.add(ct["filename"])
                    
                    rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)"""
                    
    living_replacement2 = """            elif room_type == "living_seating":
                    sofa = seed_item if seed_cat == "sofa" else find_matching_companion(["sofa"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if sofa: exclude_ids.add(sofa["filename"])
                    
                    ac = seed_item if seed_cat == "armchair" else find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if ac: exclude_ids.add(ac["filename"])
                    
                    ct = seed_item if seed_cat == "coffeetable" else find_matching_companion(["coffeetable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if ct: exclude_ids.add(ct["filename"])
                    
                    rug = seed_item if seed_cat == "rug" else find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, ct if ct else seed_item, relax)"""
                    
    if living_target2 in content:
        content = content.replace(living_target2, living_replacement2, 1)
        print("[OK] Successfully patched living block 2.")
    else:
        print("[WARNING] Living block 2 target not found!")
        
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("==================================================")
    print("               PATCHING COMPLETE                  ")
    print("==================================================")

if __name__ == "__main__":
    patch()
