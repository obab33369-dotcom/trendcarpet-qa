import os
import re

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
FALLBACK_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

print("TOPAZ DIR EXISTS:", os.path.exists(TOPAZ_DIR))
print("FALLBACK DIR EXISTS:", os.path.exists(FALLBACK_DIR))

if os.path.exists(TOPAZ_DIR):
    topaz_files = os.listdir(TOPAZ_DIR)
    print(f"Topaz files count: {len(topaz_files)}")
    print("Some topaz files:")
    for f in topaz_files[:15]:
        print(" -", f)

if os.path.exists(FALLBACK_DIR):
    fallback_dirs = os.listdir(FALLBACK_DIR)
    print(f"Fallback folders count: {len(fallback_dirs)}")
    print("Some fallback folders:")
    for d in fallback_dirs[:15]:
        print(" -", d)
