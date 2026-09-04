import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
CLEAN_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-Full-Catalog-sortering-borttagna")

def count_in_dir(path):
    if not os.path.exists(path):
        return 0, 0
    total_files = 0
    total_folders = 0
    for folder in os.listdir(path):
        folder_path = os.path.join(path, folder)
        if os.path.isdir(folder_path):
            total_folders += 1
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and not f.startswith("00_REFERENCE_"):
                        total_files += 1
    return total_files, total_folders

clean_files, clean_folders = count_in_dir(CLEAN_DIR)
discard_files, discard_folders = count_in_dir(DISCARD_DIR)

print(f"CLEAN_DIR (Approved): {clean_files} files in {clean_folders} folders")
print(f"DISCARD_DIR (To review): {discard_files} files in {discard_folders} folders")
