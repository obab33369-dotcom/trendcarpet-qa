import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

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
    print("=== Scanning for Carpets with Zero Kept Images ===")
    
    clean_folders = sorted([d for d in os.listdir(CLEAN_ROOT) if os.path.isdir(os.path.join(CLEAN_ROOT, d))])
    
    flagged = []
    
    for folder in clean_folders:
        clean_path = os.path.join(CLEAN_ROOT, folder)
        discard_path = os.path.join(DISCARD_ROOT, folder)
        
        kept = count_renders(clean_path)
        discarded = count_renders(discard_path)
        
        if kept == 0 and discarded > 0:
            flagged.append((folder, discarded))
            
    print(f"\nFound {len(flagged)} folders with 0 kept and >0 discarded images:")
    for folder, discarded_count in flagged:
        # Get reference image name if exists
        ref_file = None
        for f in os.listdir(os.path.join(CLEAN_ROOT, folder)):
            if f.startswith("00_REFERENCE_"):
                ref_file = f
                break
        print(f"  * Folder: {folder}")
        print(f"    - Discarded images: {discarded_count}")
        print(f"    - Current Reference: {ref_file}")
        print("-" * 50)

if __name__ == "__main__":
    main()
