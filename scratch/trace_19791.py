import os
import re

targets = ['19791', '19791-black-oak']
NEW_WHITE_BG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"
TOPAZ_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
ORIG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"

def check_folder(dir_path, label):
    if not os.path.exists(dir_path):
        print(f"{label} path does not exist: {dir_path}")
        return
    print(f"\nChecking {label}: {dir_path}")
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            if any(t in f.lower() for t in targets):
                print(f"  File: {os.path.join(root, f)}")
        for d in dirs:
            if any(t in d.lower() for t in targets):
                print(f"  Dir: {os.path.join(root, d)}")

check_folder(NEW_WHITE_BG_DIR, "Refoma white background fix")
check_folder(TOPAZ_DIR, "TEST TOPAZ")
check_folder(ORIG_DIR, "reforma_original_images_by_product")
