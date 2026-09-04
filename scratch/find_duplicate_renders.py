import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def main():
    print("=== Scanning for Duplicate Renderings (in both Clean and Discard) ===")
    
    clean_folders = set(os.listdir(CLEAN_ROOT))
    discard_folders = set(os.listdir(DISCARD_ROOT))
    
    common_folders = sorted(list(clean_folders.intersection(discard_folders)))
    
    duplicate_count = 0
    folders_with_dupes = 0
    
    for folder in common_folders:
        cp = os.path.join(CLEAN_ROOT, folder)
        dp = os.path.join(DISCARD_ROOT, folder)
        
        cf = [f for f in os.listdir(cp) if not f.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(cp, f))]
        df = [f for f in os.listdir(dp) if not f.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(dp, f))]
        
        intersection = set(cf).intersection(set(df))
        
        if intersection:
            folders_with_dupes += 1
            duplicate_count += len(intersection)
            print(f"  * Folder: {folder}")
            print(f"    - Clean count: {len(cf)}")
            print(f"    - Discard count: {len(df)}")
            print(f"    - Duplicates (in both): {len(intersection)}")
            print("-" * 50)
            
    print(f"\nScan complete. Found {duplicate_count} duplicate files across {folders_with_dupes} folders.")

if __name__ == "__main__":
    main()
