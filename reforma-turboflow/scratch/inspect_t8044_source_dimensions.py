import os
import json
import re
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

print("Scanning source directories for 'gori':")

# 1. Refoma white background fix
if os.path.exists(NEW_WHITE_BG_DIR):
    for d in os.listdir(NEW_WHITE_BG_DIR):
        if "gori" in d.lower():
            p = os.path.join(NEW_WHITE_BG_DIR, d)
            print(f"\nFound folder in Refoma white background fix: {d}")
            for f in sorted(os.listdir(p)):
                filepath = os.path.join(p, f)
                if os.path.isfile(filepath) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    with Image.open(filepath) as img:
                        print(f"  {f}: Size={img.size[0]}x{img.size[1]} ({img.format})")

# 2. TEST TOPAZ
if os.path.exists(TOPAZ_DIR):
    for f in sorted(os.listdir(TOPAZ_DIR)):
        if "gori" in f.lower():
            filepath = os.path.join(TOPAZ_DIR, f)
            with Image.open(filepath) as img:
                print(f"TEST TOPAZ - {f}: Size={img.size[0]}x{img.size[1]} ({img.format})")

# 3. reforma_original_images_by_product
if os.path.exists(ORIG_DIR):
    for d in os.listdir(ORIG_DIR):
        if "gori" in d.lower():
            p = os.path.join(ORIG_DIR, d, "artiklar")
            print(f"\nFound folder in reforma_original_images_by_product: {d}")
            if os.path.exists(p):
                for f in sorted(os.listdir(p)):
                    filepath = os.path.join(p, f)
                    if os.path.isfile(filepath) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        with Image.open(filepath) as img:
                            print(f"  {f}: Size={img.size[0]}x{img.size[1]} ({img.format})")
            zoom_p = os.path.join(ORIG_DIR, d, "artiklar", "zoom")
            if os.path.exists(zoom_p):
                for f in sorted(os.listdir(zoom_p)):
                    filepath = os.path.join(zoom_p, f)
                    if os.path.isfile(filepath) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        with Image.open(filepath) as img:
                            print(f"  zoom/{f}: Size={img.size[0]}x{img.size[1]} ({img.format})")
