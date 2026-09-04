import os
import json
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    import sys
    sys.path.append(PROJECT_DIR)
    from rebuild_all_by_time import load_db, resolve_anchor
    
    # Load prompt databases to find all prefixes for Newcastle-Black
    db = {}
    db.update(load_db("rooms_turboflow_batch1.json"))
    db.update(load_db("rooms_turboflow_batch2.json"))
    db.update(load_db("rooms_turboflow_full_catalog.json"))
    
    newcastle_prefixes = set()
    for prefix, info in db.items():
        for ref in info["refs"]:
            sku, name = resolve_anchor(ref)
            if sku == "NEWCASTLE-BLACK":
                newcastle_prefixes.add(prefix)
                
    print(f"Total prefixes referencing NEWCASTLE-BLACK: {len(newcastle_prefixes)}")
    
    # Now scan all folders in the clean root for files starting with these prefixes
    found_files = []
    
    for folder in os.listdir(CLEAN_ROOT):
        folder_path = os.path.join(CLEAN_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue
            
        # Check main folder files
        for f in os.listdir(folder_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                m = re.match(r"^(\d+)", f)
                if m:
                    prefix = int(m.group(1))
                    if prefix in newcastle_prefixes:
                        found_files.append((folder, f, False))
                        
        # Check reserv subfolder
        reserv_path = os.path.join(folder_path, "reserv")
        if os.path.exists(reserv_path) and os.path.isdir(reserv_path):
            for f in os.listdir(reserv_path):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    m = re.match(r"^(\d+)", f)
                    if m:
                        prefix = int(m.group(1))
                        if prefix in newcastle_prefixes:
                            found_files.append((folder, f, True))
                            
    print(f"\nFound {len(found_files)} rendering files on disk matching Newcastle prefixes:")
    # Group by folder they are currently in
    folder_distribution = {}
    for folder, fn, in_reserv in found_files:
        loc = folder + ("/reserv" if in_reserv else "")
        folder_distribution[loc] = folder_distribution.get(loc, 0) + 1
        
    sorted_locs = sorted(folder_distribution.items(), key=lambda x: x[1], reverse=True)
    for loc, cnt in sorted_locs[:20]:
        print(f"  * {loc} -> {cnt} files")
    if len(sorted_locs) > 20:
        print(f"  ... and {len(sorted_locs) - 20} more folders.")

if __name__ == "__main__":
    main()
