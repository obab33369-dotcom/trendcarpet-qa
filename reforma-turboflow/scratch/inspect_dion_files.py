import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

# Check where Dion 1200180 images are located
dirs_to_check = [NEW_WHITE_BG_DIR, TOPAZ_DIR, ORIG_DIR]

for base_dir in dirs_to_check:
    if not os.path.exists(base_dir):
        continue
    print(f"\nScanning base directory: {base_dir}")
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if "1200180" in d or "dion" in d.lower():
                dir_path = os.path.join(root, d)
                print(f"Found folder: {dir_path}")
                for f in sorted(os.listdir(dir_path)):
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        print(f"  {f}")
