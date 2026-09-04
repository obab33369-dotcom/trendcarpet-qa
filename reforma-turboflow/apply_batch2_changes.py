import os

PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\generate_batch2_rooms.py"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

# ----------------------------------------------------
# 1. Imports and Helpers
# ----------------------------------------------------
target_short_tag = "def get_short_tag(filename: str) -> str:"

helpers_addition = """def clean_str(s: str) -> str:
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
    if rug_mat and rug_mat != "inget":
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

def get_short_tag(filename: str) -> str:"""

if target_short_tag in content:
    content = content.replace(target_short_tag, helpers_addition, 1)
    print("[OK] Helpers successfully injected!")
else:
    print("[FAIL] Helpers injection target not found!")

# ----------------------------------------------------
# 2. Categorization Rules (get_item_category)
# ----------------------------------------------------
target_cat_rug = """    if cat_meta == "matta" or "matta" in fname:
        return "rug"
        
    if "barstol" in fname or ("bar" in fname and "stol" in fname):"""

replacement_cat_rug = """    if cat_meta == "matta" or "matta" in fname:
        return "rug"
        
    if "skrivbordsstol" in fname:
        return "desk_chair"
        
    if "barstol" in fname or ("bar" in fname and "stol" in fname):"""

if target_cat_rug in content:
    content = content.replace(target_cat_rug, replacement_cat_rug, 1)
    print("[OK] desk_chair categorization rule successfully added!")
else:
    print("[FAIL] desk_chair categorization target not found!")

target_cat_tv = """    if "tv-b\\u00e4nk" in fname or "tv-b\\u00f6nk" in fname or "mediab\\u00e4nk" in fname:
        return "tv_bench"
    elif "bokhylla" in fname:"""

replacement_cat_tv = """    if "tv-b\\u00e4nk" in fname or "tv-b\\u00f6nk" in fname or "mediab\\u00e4nk" in fname:
        return "tv_bench"
    elif "b\\u00e4nk" in fname or "bank" in fname:
        return "bench"
    elif "bokhylla" in fname:"""

if target_cat_tv in content:
    content = content.replace(target_cat_tv, replacement_cat_tv, 1)
    print("[OK] bench categorization rule successfully added!")
else:
    # Try literal unicode check
    target_cat_tv_u = """    if "tv-b\u00e4nk" in fname or "tv-b\u00f6nk" in fname or "mediab\u00e4nk" in fname:
        return "tv_bench"
    elif "bokhylla" in fname:"""
    replacement_cat_tv_u = """    if "tv-b\u00e4nk" in fname or "tv-b\u00f6nk" in fname or "mediab\u00e4nk" in fname:
        return "tv_bench"
    elif "b\u00e4nk" in fname or "bank" in fname:
        return "bench"
    elif "bokhylla" in fname:"""
    if target_cat_tv_u in content:
        content = content.replace(target_cat_tv_u, replacement_cat_tv_u, 1)
        print("[OK] bench unicode categorization rule successfully added!")
    else:
        print("[FAIL] bench categorization target not found!")

# ----------------------------------------------------
# 3. Database Loading and Filtering in main()
# ----------------------------------------------------
target_db_load = """    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    print(f"Total items loaded: {len(db)}")"""

replacement_db_load = """    with open(DB_PATH, "r", encoding="utf-8") as f:
        raw_db = json.load(f)
        
    db = {}
    for k, v in raw_db.items():
        if should_skip_item(k):
            continue
        db[k] = v
        
    print(f"Total items loaded: {len(raw_db)} (Active after skip-filtering: {len(db)})")"""

if target_db_load in content:
    content = content.replace(target_db_load, replacement_db_load, 1)
    print("[OK] Skip filtering on DB load successfully added!")
else:
    print("[FAIL] DB loading target not found!")

# ----------------------------------------------------
# 4. Room type routing for bench and desk_chair seeds
# ----------------------------------------------------
target_route_1_std = """        elif seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard", "table_lamp"]:
            room_type = "living_storage"
        elif seed_cat == "desk":
            room_type = "office"
"""
replacement_route_1_std = """        elif seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard", "table_lamp", "bench"]:
            room_type = "living_storage"
        elif seed_cat in ["desk", "desk_chair"]:
            room_type = "office"
"""

if target_route_1_std in content:
    content = content.replace(target_route_1_std, replacement_route_1_std, 1)
    print("[OK] Routing for bench & desk_chair seeds in main curation loop successfully added!")
else:
    print("[FAIL] Routing target 1 not found!")

target_route_2_std = """            elif seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard", "table_lamp"]:
                room_type = "living_storage"
            elif seed_cat == "desk":
                room_type = "office"
"""
replacement_route_2_std = """            elif seed_cat in ["tv_bench", "dresser", "cabinet", "bookcase", "shoe_cabinet", "sideboard", "table_lamp", "bench"]:
                room_type = "living_storage"
            elif seed_cat in ["desk", "desk_chair"]:
                room_type = "office"
"""

if target_route_2_std in content:
    content = content.replace(target_route_2_std, replacement_route_2_std, 1)
    print("[OK] Routing for bench & desk_chair seeds in fallback loop successfully added!")
else:
    print("[FAIL] Routing target 2 not found!")

# ----------------------------------------------------
# 5. fill_empty_slots updates
# ----------------------------------------------------
target_fill_slots = """        "office": [
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
        ]"""

replacement_fill_slots = """        "office": [
            ("desk_chair", ["desk_chair", "dining_chair", "armchair"]),
            ("bookcase", ["bookcase", "cabinet", "dresser"])
        ],
        "bedroom": [
            ("bed", ["sofa"]),
            ("dresser", ["dresser", "cabinet"]),
            ("rug", ["rug"])
        ],
        "bar": [
            ("bartable", ["bartable"]),
            ("rug", ["rug"]),
            ("background_storage", ["cabinet", "sideboard"])
        ]"""

if target_fill_slots in content:
    content = content.replace(target_fill_slots, replacement_fill_slots, 1)
    print("[OK] fill_empty_slots definitions successfully updated!")
else:
    print("[FAIL] fill_empty_slots target not found!")

# ----------------------------------------------------
# 6. Bar template curation updates (Curation Loop 1 & 2)
# ----------------------------------------------------
target_bar_1 = """            elif room_type == "bar":
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
                    break"""

replacement_bar_1 = """            elif room_type == "bar":
                bs = seed_item if seed_cat == "barstool" else find_matching_companion(["barstool"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bs: exclude_ids.add(bs["filename"])
                
                bt = seed_item if seed_cat == "bartable" else find_matching_companion(["bartable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bt: exclude_ids.add(bt["filename"])
                
                pl = seed_item if seed_cat == "pendant_lamp" else None
                if pl: exclude_ids.add(pl["filename"])
                
                rug = find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, bt if bt else seed_item, relax)
                if rug: exclude_ids.add(rug["filename"])
                
                bg = find_matching_companion(["cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                if bg: exclude_ids.add(bg["filename"])
                
                if bs:
                    pkg.update({"barstool": bs, "bartable": bt, "pendant_lamp": pl, "rug": rug, "background_storage": bg})
                    matched_pkg = pkg
                    break"""

if target_bar_1 in content:
    content = content.replace(target_bar_1, replacement_bar_1, 1)
    print("[OK] Curation loop 1 bar template successfully updated with rug slot!")
else:
    print("[FAIL] Curation loop 1 bar target not found!")

target_bar_2 = """                elif room_type == "bar":
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
                        break"""

replacement_bar_2 = """                elif room_type == "bar":
                    bs = seed_item if seed_cat == "barstool" else find_matching_companion(["barstool"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bs: exclude_ids.add(bs["filename"])
                    
                    bt = seed_item if seed_cat == "bartable" else find_matching_companion(["bartable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bt: exclude_ids.add(bt["filename"])
                    
                    pl = seed_item if seed_cat == "pendant_lamp" else None
                    if pl: exclude_ids.add(pl["filename"])
                    
                    rug = find_matching_companion(["rug"], items_by_cat, unfeatured_ids, exclude_ids, bt if bt else seed_item, relax)
                    if rug: exclude_ids.add(rug["filename"])
                    
                    bg = find_matching_companion(["cabinet", "sideboard"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
                    if bg: exclude_ids.add(bg["filename"])
                    
                    if bs:
                        pkg.update({"barstool": bs, "bartable": bt, "pendant_lamp": pl, "rug": rug, "background_storage": bg})
                        matched_pkg = pkg
                        break"""

if target_bar_2 in content:
    content = content.replace(target_bar_2, replacement_bar_2, 1)
    print("[OK] Fallback curation loop 2 bar template successfully updated with rug slot!")
else:
    print("[FAIL] Fallback curation loop 2 bar target not found!")

# ----------------------------------------------------
# 7. Stockholm classic turn-of-the-century apartment in Östermalm template updates
# ----------------------------------------------------
# Let's inspect get_dynamic_location directly
get_dyn_start = content.find("def get_dynamic_location(pkg_idx: int, is_kitchen: bool) -> Tuple[str, str]:")
ostermalm_index = content.find("Stockholm classic turn-of-the-century apartment", get_dyn_start)
desc_line_end = content.find("\n", ostermalm_index)

ostermalm_original_line = content[ostermalm_index:desc_line_end]
print(f"Original Stockholm line: {ostermalm_original_line}")

# We replace it inside get_dynamic_location
if ostermalm_original_line:
    content = content.replace("desc = f\"" + ostermalm_original_line.replace('desc = f"', ''), "fireplace = \"a classic tiled stove (kakelugn) in the corner\" if (pkg_idx % 2 == 0) else \"a clean empty fireplace against the wall\"\n            desc = f\"Stockholm classic turn-of-the-century apartment {room} in Östermalm with {fireplace}, and views of tree-lined streets\"", 1)
    print("[OK] Classic Stockholm turn-of-the-century description updated (no ceilings/molding, yes kakelugn/fireplace)!")
else:
    print("[FAIL] Classic Stockholm turn-of-the-century description target not found!")

# ----------------------------------------------------
# 8. Curation prompt generation & output shots logic (replace everything from dining block up to tracking_rows.append in Shot 2)
# ----------------------------------------------------
start_loop = content.find("    for pkg_idx, pkg in enumerate(packages):")
start_dining_check = content.find("        if room_type == \"dining\":", start_loop)
# Let's find where tracking_rows.append of Shot 2 ends
end_shot2_append = content.find("        tracking_rows.append({\n            \"Row Number\": shot2_num,\n            \"Package ID\": package_id,", start_dining_check)
# Let's find the closing "        })" of Shot 2 append
closing_paren = content.find("        })", end_shot2_append)
end_point = closing_paren + len("        })")

target_prompt_block = content[start_dining_check:end_point]
print(f"Prompt block target length: {len(target_prompt_block)}")

# Define the replacement block
replacement_prompt_block = """        if room_type == "dining":
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
                subject_parts.append(f"the elegant armchair ({ac_name})")
                parts_2.append(f"the elegant armchair ({ac_name})")
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
            
            is_bench = ps and ("b\u00e4nk" in ps["filename"].lower() or "bank" in ps["filename"].lower()) and not ("tv-b\u00e4nk" in ps["filename"].lower() or "tv-b\u00f6nk" in ps["filename"].lower() or "mediab\u00e4nk" in ps["filename"].lower())
            
            if is_bench:
                subject_desc = f"a sophisticated setup featuring the elegant bench ({ps_name}) standing along the wall"
                subject_desc_2 = f"the elegant bench ({ps_name}) standing along the wall"
            else:
                subject_desc = f"a sophisticated storage setup featuring the beautiful {ps_name} standing against the wall"
                subject_desc_2 = f"the elegant {ps_name} standing against the wall"
            
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
            
            is_sofa = bed and ("soffa" in bed["filename"].lower() or "b\u00e4ddsoffa" in bed["filename"].lower())
            
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
                subject_desc += f", with a designer table lamp ({tl_name}) resting on top of the bedside table"
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
                
        # Ensure unique items while preserving order
        seen_filenames = set()
        unique_tagged_items = []
        for x in tagged_items:
            if x["filename"] not in seen_filenames:
                seen_filenames.add(x["filename"])
                unique_tagged_items.append(x)
        tagged_items = unique_tagged_items
        
        # Prepend the strict widescreen black border framing prefix to all prompts
        PREFIX = (
            "A centered top-to-bottom ar 1:1 square image asset, on a rectangle 16:9 widescreen black background - "
            "deep solid black pillarbox borders on the far left and far right of the square image, "
            "making the central 1:1 square scene the absolute focal point. The square scene interior: "
        )
        
        tags_str = "  " + "; ".join([get_short_tag(x["filename"]) for x in tagged_items])
        files_str = "; ".join([get_short_filename(x["filename"]) for x in tagged_items])
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
            f"{shot1_num:03d} - {PREFIX}Architectural digest-style view of {subject_desc} set in a {location_desc} with {shot1_light}.{bg_part_1} "
            f"Dynamic perspective with controlled depth of field. Varied gloss levels on walls and trim to enhance depth, "
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
            "aspect_ratio": "16:9"
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
        
        # ----------------------------------------------------
        # Shot 2: Close-up Detail View
        # ----------------------------------------------------
        shot2_num = len(output_rows) + 1
        shot2_light = "moody evening twilight with warm glowing indoor lights" if is_lamp else ("warm golden hour light creating long soft shadows" if (pkg_idx % 2 == 0) else "moody evening twilight with warm glowing indoor lights")
        bg_sentence_2 = join_background_elements(bg_elements_2, close_up=True)
        bg_part_2 = f" {bg_sentence_2}" if bg_sentence_2 else ""
        
        prompt_2 = (
            f"{shot2_num:03d} - {PREFIX}Architectural digest-style close-up shot showcasing {subject_desc_2}, set in a {location_desc} with {shot2_light}.{bg_part_2} "
            f"Dynamic close-up shot with controlled depth of field. Varied gloss levels on walls and trim to enhance depth, "
            f"featuring tactile micro-imperfections. Strictly preserve individual furniture material finishes (matte, lacquer, metal) "
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
            "aspect_ratio": "16:9"
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
            "Table Product": clean_tag_to_name(pkg.get("dining_table")["filename"], include_dimensions=False) if pkg.get("dining_table") else (clean_tag_to_name(pkg.get("coffeetable")["filename"], include_dimensions=False) if pkg.get("coffeetable") else (clean_tag_to_name(pkg.get("desk")["filename"], include_dimensions=False) if pkg.get("desk") else "None")),
            "Seating Product": clean_tag_to_name(pkg.get("dining_chair")["filename"], include_dimensions=False) if pkg.get("dining_chair") else (clean_tag_to_name(pkg.get("sofa")["filename"], include_dimensions=False) if pkg.get("sofa") else (clean_tag_to_name(pkg.get("armchair")["filename"], include_dimensions=False) if pkg.get("armchair") else (clean_tag_to_name(pkg.get("barstool")["filename"], include_dimensions=False) if pkg.get("barstool") else (clean_tag_to_name(pkg.get("desk_chair")["filename"], include_dimensions=False) if pkg.get("desk_chair") else "None")))),
            "Rug Product": clean_tag_to_name(pkg.get("rug")["filename"], include_dimensions=False) if pkg.get("rug") else "None",
            "Lamp Product": clean_tag_to_name(pkg.get("pendant_lamp")["filename"], include_dimensions=False) if pkg.get("pendant_lamp") else (clean_tag_to_name(pkg.get("floor_lamp")["filename"], include_dimensions=False) if pkg.get("floor_lamp") else (clean_tag_to_name(pkg.get("table_lamp")["filename"], include_dimensions=False) if pkg.get("table_lamp") else "None")),
            "Storage Product": clean_tag_to_name(pkg.get("background_storage")["filename"], include_dimensions=False) if pkg.get("background_storage") else (clean_tag_to_name(pkg.get("primary_storage")["filename"], include_dimensions=False) if pkg.get("primary_storage") else (clean_tag_to_name(pkg.get("bookcase")["filename"], include_dimensions=False) if pkg.get("bookcase") else (clean_tag_to_name(pkg.get("dresser")["filename"], include_dimensions=False) if pkg.get("dresser") else "None"))),
            "References Utilized": files_str,
            "Tags Utilized": short_tags_only
        })

        # ----------------------------------------------------
        # Shot 3: Wide Angle View
        # ----------------------------------------------------
        shot3_num = len(output_rows) + 1
        shot3_light = "bright natural morning light" if (pkg_idx % 2 == 0) else "crisp cinematic afternoon sunlight"
        bg_sentence_3 = join_background_elements(bg_elements, close_up=False)
        bg_part_3 = f" {bg_sentence_3}" if bg_sentence_3 else ""
        
        prompt_3 = (
            f"{shot3_num:03d} - {PREFIX}Architectural digest-style wide-angle view of {subject_desc} set in a {location_desc} with {shot3_light}.{bg_part_3} "
            f"Dynamic perspective with controlled depth of field. Varied gloss levels on walls and trim to enhance depth, "
            f"featuring tactile micro-imperfections. Strictly preserve individual furniture material finishes (matte, lacquer, metal) "
            f"without global gloss changes. Enhance atmosphere with very subtle volumetric-dust. Prioritize high-end material tactility "
            f"and realistic light-reactive surfaces over digital polish, showcasing premium wood and stone surfaces. Utilize chiaroscuro lighting "
            f"techniques to deepen shadow definition, ensuring clear silhouettes for furniture against the walls. "
            f"Break the monochromatic palette with refined material contrasts, such as cool-toned stone or matte metallic finishes to add "
            f"depth and sophisticated material friction. No cutting-boards, no wooden plates in the kitchen, no abstract sculpture, no plants, no knick-knacks, no knick-knack.{tags_str}"
        )
        
        output_rows.append({
            "prompt": prompt_3,
            "image_references": files_str,
            "image_tags": short_tags_only,
            "aspect_ratio": "16:9"
        })
        
        tracking_rows.append({
            "Row Number": shot3_num,
            "Package ID": package_id,
            "Package Type": room_type.capitalize(),
            "Template Style": location_name,
            "Focus Type": "Wide Angle View",
            "Close-up": "No",
            "Location": location_name,
            "Focus Description": f"Wide-angle view of {subject_desc}",
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

        # ----------------------------------------------------
        # Shot 4: Intimate Moody View
        # ----------------------------------------------------
        shot4_num = len(output_rows) + 1
        shot4_light = "cozy warm ambient light from indoor lamps and moody evening twilight"
        bg_sentence_4 = join_background_elements(bg_elements_2, close_up=True)
        bg_part_4 = f" {bg_sentence_4}" if bg_sentence_4 else ""
        
        prompt_4 = (
            f"{shot4_num:03d} - {PREFIX}Architectural digest-style cozy and intimate close-up shot showcasing {subject_desc_2}, set in a {location_desc} with {shot4_light}.{bg_part_4} "
            f"Dynamic close-up shot with controlled depth of field. Varied gloss levels on walls and trim to enhance depth, "
            f"featuring tactile micro-imperfections. Strictly preserve individual furniture material finishes (matte, lacquer, metal) "
            f"without global gloss changes. Enhance atmosphere with very subtle volumetric-dust. Prioritize high-end material tactility "
            f"and realistic light-reactive surfaces over digital polish, showcasing premium wood and stone surfaces. Utilize chiaroscuro lighting "
            f"techniques to deepen shadow definition, ensuring clear silhouettes for furniture against the walls. "
            f"Break the monochromatic palette with refined material contrasts, such as cool-toned stone or matte metallic finishes to add "
            f"depth and sophisticated material friction. No cutting-boards, no wooden plates in the kitchen, no abstract sculpture, no plants, no knick-knacks, no knick-knack.{tags_str}"
        )
        
        output_rows.append({
            "prompt": prompt_4,
            "image_references": files_str,
            "image_tags": short_tags_only,
            "aspect_ratio": "16:9"
        })
        
        tracking_rows.append({
            "Row Number": shot4_num,
            "Package ID": package_id,
            "Package Type": room_type.capitalize(),
            "Template Style": location_name,
            "Focus Type": "Intimate Moody View",
            "Close-up": "Yes",
            "Location": location_name,
            "Focus Description": f"Intimate cozy view of {subject_desc_2}",
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
        })"""

if len(target_prompt_block) > 100:
    content = content.replace(target_prompt_block, replacement_prompt_block, 1)
    print(f"[OK] Prompt block successfully replaced!")
else:
    print(f"[FAIL] Prompt block target not found!")

# ----------------------------------------------------
# 9. Save file
# ----------------------------------------------------
with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Patching of all Batch 2 enhancements completed successfully!")
