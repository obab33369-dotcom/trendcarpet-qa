import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"

CLEAN_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering")
DISCARD_ROOT = os.path.join(ONEDRIVE_DIR, "Reforma-Mattor-sortering-borttagna")

def count_files(root_dir):
    if not os.path.exists(root_dir):
        return 0, 0, 0
    folders_count = 0
    main_files = 0
    reserv_files = 0
    
    for item in os.listdir(root_dir):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path):
            folders_count += 1
            # Check main dir files
            for f in os.listdir(path):
                f_path = os.path.join(path, f)
                if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    main_files += 1
            # Check reserv
            reserv = os.path.join(path, "reserv")
            if os.path.exists(reserv) and os.path.isdir(reserv):
                for f in os.listdir(reserv):
                    f_path = os.path.join(reserv, f)
                    if os.path.isfile(f_path) and not f.startswith("00_REFERENCE_") and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        reserv_files += 1
                        
    return folders_count, main_files, reserv_files

def main():
    clean_folders, clean_main, clean_reserv = count_files(CLEAN_ROOT)
    discard_folders, discard_main, discard_reserv = count_files(DISCARD_ROOT)
    
    print("=== Final Carpet Reorganization Statistics ===")
    print(f"Approved root: Reforma-Mattor-sortering")
    print(f"  Folders: {clean_folders}")
    print(f"  Main Rendering Files: {clean_main}")
    print(f"  Reserv Rendering Files: {clean_reserv}")
    print(f"  Total Approved Images: {clean_main + clean_reserv}")
    
    print(f"\nDiscarded root: Reforma-Mattor-sortering-borttagna")
    print(f"  Folders: {discard_folders}")
    print(f"  Main Rendering Files: {discard_main}")
    print(f"  Reserv Rendering Files: {discard_reserv}")
    print(f"  Total Discarded Images: {discard_main + discard_reserv}")
    
    print(f"\nTotal Images Evaluated: {clean_main + clean_reserv + discard_main + discard_reserv}")

if __name__ == "__main__":
    main()
