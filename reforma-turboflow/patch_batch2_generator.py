import os

GENERATOR_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\generate_batch2_rooms.py"

def patch_generator():
    if not os.path.exists(GENERATOR_PATH):
        print(f"Error: File not found: {GENERATOR_PATH}")
        return
        
    with open(GENERATOR_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Update export file paths at the top
    code = code.replace(
        'DB_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\furniture_db.json"',
        'DB_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\furniture_db_batch2.json"'
    )
    code = code.replace(
        'EXPORT_JSON_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\rooms_turboflow.json"',
        'EXPORT_JSON_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\rooms_turboflow_batch2.json"'
    )
    code = code.replace(
        'CSV_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_ready.csv"',
        'CSV_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_ready_batch2.csv"'
    )
    code = code.replace(
        'FLAT_JSON_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_ready.json"',
        'FLAT_JSON_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_ready_batch2.json"'
    )
    code = code.replace(
        'TXT_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_ready.txt"',
        'TXT_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_ready_batch2.txt"'
    )
    code = code.replace(
        'PROMPTS_ONLY_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\prompts_only.txt"',
        'PROMPTS_ONLY_EXPORT_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\prompts_only_batch2.txt"'
    )
    code = code.replace(
        'TRACKING_LOG_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_tracking_log.csv"',
        'TRACKING_LOG_PATH = r"C:\\Users\\AndronikLindgren\\.gemini\\antigravity\\scratch\\reforma-turboflow\\turboflow_tracking_log_batch2.csv"'
    )

    # 2. Inject global usage dictionary and recount function, and update find_matching_companion sorting
    old_matching = """    # Sort candidates so we prioritize unfeatured items
    def sort_key(x):
        is_unfeatured = x["filename"] in unfeatured_ids
        return (0 if is_unfeatured else 1, x["filename"])
        
    sorted_candidates = sorted(candidates, key=sort_key)"""

    new_matching = """    # Sort candidates prioritizing: unfeatured first, then lowest usage count first
    def sort_key(x):
        is_unfeatured = x["filename"] in unfeatured_ids
        usage = usage_counts.get(x["filename"], 0)
        return (0 if is_unfeatured else 1, usage, x["filename"])
        
    sorted_candidates = sorted(candidates, key=sort_key)"""

    if "usage_counts = {}" not in code:
        code = code.replace(
            "def find_matching_companion(",
            "usage_counts = {}\n\ndef recount_usages(packages, db):\n    for k in db.keys():\n        usage_counts[k] = 0\n    for pkg in packages:\n        for slot, item in pkg.items():\n            if slot not in ['room_type', 'relax_level', 'seed'] and item is not None:\n                fn = item['filename']\n                usage_counts[fn] = usage_counts.get(fn, 0) + 1\n\ndef find_matching_companion("
        )

    code = code.replace(old_matching, new_matching)

    # 3. Initialize usage_counts in main()
    old_init = """    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    print(f"Total items loaded: {len(db)}")"""

    new_init = """    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    print(f"Total items loaded: {len(db)}")
    
    # Initialize usage counts
    for k in db.keys():
        usage_counts[k] = 0"""

    code = code.replace(old_init, new_init)

    # 4. Inject recount_usages in both loop storage steps
    old_loop1_append = """            for slot, item in matched_pkg.items():
                if slot not in ["room_type", "relax_level", "seed"] and item is not None:
                    unfeatured_ids.discard(item["filename"])
            packages.append(matched_pkg)"""

    new_loop1_append = """            for slot, item in matched_pkg.items():
                if slot not in ["room_type", "relax_level", "seed"] and item is not None:
                    unfeatured_ids.discard(item["filename"])
            packages.append(matched_pkg)
            recount_usages(packages, db)"""

    code = code.replace(old_loop1_append, new_loop1_append)

    old_loop2_append = """            if matched_pkg:
                packages.append(matched_pkg)"""

    new_loop2_append = """            if matched_pkg:
                packages.append(matched_pkg)
                recount_usages(packages, db)"""

    code = code.replace(old_loop2_append, new_loop2_append)

    # 5. Inject recount_usages inside fill_empty_slots loop
    old_fill_loop = """    # Populate missing slots to make every room complete and feature 4-6 items
    for pkg in packages:
        fill_empty_slots(pkg, items_by_cat, unfeatured_ids)"""

    new_fill_loop = """    # Populate missing slots to make every room complete and feature 4-6 items
    for pkg in packages:
        fill_empty_slots(pkg, items_by_cat, unfeatured_ids)
        recount_usages(packages, db)"""

    code = code.replace(old_fill_loop, new_fill_loop)

    # 6. Patch the extra packages loop to use the smart Lowest-Usage seed selector
    old_extra_loop = """    # Ensure exactly 110 packages
    if len(packages) < 110:
        db_keys_sorted = sorted(list(db.keys()))
        extra_idx = 0
        while len(packages) < 110 and extra_idx < len(db_keys_sorted):
            seed_id = db_keys_sorted[extra_idx]
            extra_idx += 1
            seed_item = db[seed_id]
            seed_cat = get_item_category(seed_id, seed_item)"""

    new_extra_loop = """    # Ensure exactly 110 packages
    if len(packages) < 110:
        extra_used_seeds = set()
        while len(packages) < 110:
            # Sort all db keys prioritizing the least-used items as seeds!
            sorted_by_usage = sorted(db.keys(), key=lambda k: (1 if k in extra_used_seeds else 0, usage_counts.get(k, 0), k))
            seed_id = sorted_by_usage[0]
            extra_used_seeds.add(seed_id)
            
            seed_item = db[seed_id]
            seed_cat = get_item_category(seed_id, seed_item)"""

    code = code.replace(old_extra_loop, new_extra_loop)

    # Save the updated file
    with open(GENERATOR_PATH, "w", encoding="utf-8") as f:
        f.write(code)

    print("SUCCESS: generate_batch2_rooms.py has been successfully patched with smart balancing logic!")

if __name__ == "__main__":
    patch_generator()
