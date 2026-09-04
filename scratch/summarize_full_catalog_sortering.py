import os
import json
import re

USER_LIST_PATH = r"scratch/filenames_input_4.txt"
SORT_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-Full-Catalog-sortering"
DISCARD_ROOT = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\Reforma-Full-Catalog-sortering-borttagna"

def clean_prod_name(folder):
    # E.g. "Byra San Atervunnen Teak (4100018)" -> "Byra San Atervunnen Teak (4100018)"
    return folder

def main():
    if not os.path.exists(USER_LIST_PATH):
        print("User list not found.")
        return
        
    with open(USER_LIST_PATH, "r", encoding="utf-8") as f:
        filenames = set([line.strip() for line in f if line.strip()])
        
    print(f"Loaded {len(filenames)} unique target filenames.")
    
    # Scan SORT_ROOT
    sort_matches = {}
    for dirpath, dirnames, files in os.walk(SORT_ROOT):
        for f in files:
            if f in filenames:
                rel_dir = os.path.relpath(dirpath, SORT_ROOT)
                if rel_dir not in sort_matches:
                    sort_matches[rel_dir] = []
                sort_matches[rel_dir].append(f)
                
    # Scan DISCARD_ROOT
    discard_matches = {}
    for dirpath, dirnames, files in os.walk(DISCARD_ROOT):
        for f in files:
            if f in filenames:
                rel_dir = os.path.relpath(dirpath, DISCARD_ROOT)
                if rel_dir not in discard_matches:
                    discard_matches[rel_dir] = []
                discard_matches[rel_dir].append(f)
                
    print("\n--- DISTRIBUTION IN APPROVED SORTING ROOT (Reforma-Full-Catalog-sortering) ---")
    total_approved = 0
    for folder, matches in sorted(sort_matches.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  Folder: `{folder}` -> Count: {len(matches)} files")
        total_approved += len(matches)
    print(f"Total files in approved folders: {total_approved}")
        
    print("\n--- DISTRIBUTION IN DISCARDED SORTING ROOT (Reforma-Full-Catalog-sortering-borttagna) ---")
    total_discarded = 0
    for folder, matches in sorted(discard_matches.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  Folder: `{folder}` -> Count: {len(matches)} files")
        total_discarded += len(matches)
    print(f"Total files in discarded folders: {total_discarded}")

if __name__ == "__main__":
    main()
