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
    
    # Load prompt databases
    batch1 = load_db("rooms_turboflow_batch1.json")
    batch2 = load_db("rooms_turboflow_batch2.json")
    full_catalog = load_db("rooms_turboflow_full_catalog.json")
    
    db_mapping = {}
    db_mapping.update(batch1)
    db_mapping.update(batch2)
    db_mapping.update(full_catalog)
    
    # Let's collect all files on OneDrive (clean root) and see which ones are resolved to NEWCASTLE-BLACK
    target_folder_name = "Bokhylla Newcastle Svart (NEWCASTLE-BLACK)"
    target_path = os.path.join(CLEAN_ROOT, target_folder_name)
    target_reserv = os.path.join(target_path, "reserv")
    
    print(f"Target path: {target_path}")
    print(f"Target path exists: {os.path.exists(target_path)}")
    print(f"Target reserv exists: {os.path.exists(target_reserv)}")
    
    # Let's run a dry run of the mapping for Newcastle
    newcastle_secondaries = []
    
    # Let's scan files on OneDrive that rebuild_all_by_time scans
    dirs_to_scan = [
        ONEDRIVE_DIR,
        os.path.join(ONEDRIVE_DIR, "första omgången fyrkantiga")
    ]
    
    files_info = []
    for d in dirs_to_scan:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                files_info.append(f)
                
    print(f"\nTotal files in source dirs: {len(files_info)}")
    
    # Count how many files should map to NEWCASTLE-BLACK
    mapped_primary_count = 0
    mapped_secondary_count = 0
    
    for f in files_info:
        m = re.match(r"^(\d+)", f)
        if not m:
            continue
        prefix = int(m.group(1))
        
        if prefix in db_mapping:
            refs = db_mapping[prefix]["refs"]
            for ref_idx, ref in enumerate(refs):
                sku, name = resolve_anchor(ref)
                if sku == "NEWCASTLE-BLACK":
                    if ref_idx == 0:
                        mapped_primary_count += 1
                    else:
                        mapped_secondary_count += 1
                        newcastle_secondaries.append(f)
                        
    print(f"Should map as Primary: {mapped_primary_count}")
    print(f"Should map as Secondary: {mapped_secondary_count}")
    print(f"First 10 secondary files that should have been copied: {newcastle_secondaries[:10]}")

if __name__ == "__main__":
    main()
