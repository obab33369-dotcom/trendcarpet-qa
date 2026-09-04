import os

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow"
SOURCE_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering")
DISCARD_DIR = os.path.join(ONEDRIVE_DIR, "Reforma-interiörer-ny-sortering-borttagna")

def get_stats(base_dir):
    if not os.path.exists(base_dir):
        return 0, 0
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    total_files = 0
    for f in folders:
        path = os.path.join(base_dir, f)
        # Count all files in folder and its subdirectories (excluding subfolders themselves)
        for root, dirs, files in os.walk(path):
            total_files += len([file for file in files if not file.startswith("00_REFERENCE_")])
    return len(folders), total_files

main_folders, main_files = get_stats(SOURCE_DIR)
discard_folders, discard_files = get_stats(DISCARD_DIR)

print("=== FINAL SORTING STATS ===")
print(f"Main Clean Folder ({os.path.basename(SOURCE_DIR)}):")
print(f"  Total Product Folders: {main_folders}")
print(f"  Total Clean Renders:   {main_files}")

print(f"\nDiscarded Folder ({os.path.basename(DISCARD_DIR)}):")
print(f"  Total Product Folders: {discard_folders}")
print(f"  Total Discarded Renders: {discard_files}")
