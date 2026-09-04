import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def is_carpet(folder_name):
    name_lower = folder_name.lower()
    return "matta" in name_lower or "rug" in name_lower or "rg01" in name_lower or "jute" in name_lower or "pet" in name_lower

def count_renders(folder_path):
    if not os.path.exists(folder_path):
        return 0
    count = 0
    for f in os.listdir(folder_path):
        f_path = os.path.join(folder_path, f)
        if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            count += 1
    return count

def main():
    print("=== Scanning for Furniture Folders with Zero Kept Images ===")
    
    if not os.path.exists(CLEAN_ROOT):
        print("Clean root does not exist.")
        return
        
    folders = sorted([d for d in os.listdir(CLEAN_ROOT) if os.path.isdir(os.path.join(CLEAN_ROOT, d))])
    
    flagged = []
    
    for folder in folders:
        if is_carpet(folder):
            continue
            
        clean_path = os.path.join(CLEAN_ROOT, folder)
        discard_path = os.path.join(DISCARD_ROOT, folder)
        
        kept = count_renders(clean_path)
        discarded = count_renders(discard_path)
        
        if kept == 0 and discarded > 0:
            # Get reference image name if exists
            ref_file = None
            for f in os.listdir(clean_path):
                if f.startswith("00_REFERENCE_"):
                    ref_file = f
                    break
            flagged.append((folder, discarded, ref_file))
            
    print(f"\nFound {len(flagged)} furniture folders with 0 kept and >0 discarded images:")
    for folder, discarded_count, ref_file in flagged:
        print(f"  * Folder: {folder}")
        print(f"    - Discarded images: {discarded_count}")
        print(f"    - Reference File: {ref_file}")
        print("-" * 50)

if __name__ == "__main__":
    main()
