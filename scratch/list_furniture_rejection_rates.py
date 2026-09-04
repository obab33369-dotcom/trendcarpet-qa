import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def get_candidates(folder_path):
    if not os.path.exists(folder_path):
        return set()
    files = set()
    for f in os.listdir(folder_path):
        f_path = os.path.join(folder_path, f)
        if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            files.add(f)
    return files

def main():
    print("=== Scanning Furniture Folders for 100% Rejection ===")
    
    if not os.path.exists(CLEAN_ROOT):
        print("Clean root does not exist.")
        return
        
    folders = sorted([d for d in os.listdir(CLEAN_ROOT) if os.path.isdir(os.path.join(CLEAN_ROOT, d))])
    
    hundred_percent_rejected = []
    partially_rejected = []
    
    for folder in folders:
        if is_carpet(folder):
            continue
            
        clean_path = os.path.join(CLEAN_ROOT, folder)
        discard_path = os.path.join(DISCARD_ROOT, folder)
        
        clean_files = get_candidates(clean_path)
        discard_files = get_candidates(discard_path)
        
        if not clean_files and not discard_files:
            continue
            
        duplicates = clean_files.intersection(discard_files)
        
        # Candidate count in clean that are not in discard (actually kept)
        actual_kept = len(clean_files) - len(duplicates)
        # Total generated renders for this folder is union of clean and discard (excluding duplicates if they are same)
        total_renders = len(clean_files.union(discard_files))
        
        # If all clean files are duplicates of discard files, then 100% of renders in clean are actually discarded!
        # And if there are renders in discard for this folder, that means it's fully rejected.
        if len(clean_files) > 0 and len(clean_files) == len(duplicates):
            hundred_percent_rejected.append((folder, len(clean_files), len(discard_files), len(duplicates)))
        elif len(discard_files) > 0:
            partially_rejected.append((folder, len(clean_files), len(discard_files), len(duplicates)))
            
    print(f"\nFound {len(hundred_percent_rejected)} furniture folders with 100% REJECTION (all clean renders are duplicated in discard):")
    for folder, clean_cnt, discard_cnt, dupe_cnt in hundred_percent_rejected:
        print(f"  * {folder}")
        print(f"    - Clean files: {clean_cnt}")
        print(f"    - Discard files: {discard_cnt}")
        print(f"    - Duplicate files: {dupe_cnt}")
        print("-" * 50)
        
    print(f"\nFound {len(partially_rejected)} furniture folders with partial rejection (some renders duplicated or present in both):")
    for folder, clean_cnt, discard_cnt, dupe_cnt in partially_rejected[:10]: # Print top 10
        print(f"  * {folder}")
        print(f"    - Clean files: {clean_cnt}")
        print(f"    - Discard files: {discard_cnt}")
        print(f"    - Duplicate files: {dupe_cnt}")
        print("-" * 50)
    if len(partially_rejected) > 10:
        print(f"... and {len(partially_rejected) - 10} more.")

if __name__ == "__main__":
    main()
