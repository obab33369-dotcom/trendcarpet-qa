import os
import stat

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def make_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass

def main():
    print("=== Deduplicating Clean and Discard Roots ===")
    
    if not os.path.exists(CLEAN_ROOT) or not os.path.exists(DISCARD_ROOT):
        print("Clean or Discard root does not exist.")
        return
        
    clean_folders = set(os.listdir(CLEAN_ROOT))
    discard_folders = set(os.listdir(DISCARD_ROOT))
    common_folders = sorted(list(clean_folders.intersection(discard_folders)))
    
    deleted_count = 0
    
    for folder in common_folders:
        if is_carpet(folder):
            continue
            
        cp = os.path.join(CLEAN_ROOT, folder)
        dp = os.path.join(DISCARD_ROOT, folder)
        
        cf = [f for f in os.listdir(cp) if not f.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(cp, f))]
        df = [f for f in os.listdir(dp) if not f.startswith("00_REFERENCE_") and os.path.isfile(os.path.join(dp, f))]
        
        intersection = set(cf).intersection(set(df))
        
        if intersection:
            print(f"Folder: {folder}")
            print(f"  Removing {len(intersection)} duplicates from clean folder...")
            for f in intersection:
                f_path = os.path.join(cp, f)
                make_writable(f_path)
                try:
                    os.remove(f_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"    Failed to delete {f}: {e}")
            print("-" * 50)
            
    print(f"\nDeduplication complete. Deleted a total of {deleted_count} duplicate files from the clean root.")

if __name__ == "__main__":
    main()
