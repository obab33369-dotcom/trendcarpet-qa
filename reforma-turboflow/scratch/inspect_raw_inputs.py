import os
import sys
import re

# Add project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

from reforma_pipeline.classification import normalize_name

prod_name = "1311-L-S"  # Let's search for this SKU
prod_norm = normalize_name(prod_name)

print("Searching for raw source paths for 1311-L-S...")

# Let's find folders in Refoma white background fix
if os.path.exists(NEW_WHITE_BG_DIR):
    for d in os.listdir(NEW_WHITE_BG_DIR):
        if normalize_name(d) == prod_norm or prod_norm in normalize_name(d):
            dir_path = os.path.join(NEW_WHITE_BG_DIR, d)
            print(f"\nFound folder in Refoma white background fix: {d}")
            for f in sorted(os.listdir(dir_path)):
                p = os.path.join(dir_path, f)
                if os.path.isfile(p):
                    from PIL import Image
                    try:
                        with Image.open(p) as img:
                            print(f"  {f}: size={img.size}, mode={img.mode}")
                    except Exception as e:
                        print(f"  {f}: error: {e}")

# Let's find in TEST TOPAZ
if os.path.exists(TOPAZ_DIR):
    for f in sorted(os.listdir(TOPAZ_DIR)):
        if prod_norm in normalize_name(f):
            p = os.path.join(TOPAZ_DIR, f)
            from PIL import Image
            try:
                with Image.open(p) as img:
                    print(f"Found in TEST TOPAZ: {f}: size={img.size}")
            except Exception as e:
                pass

# Let's find in reforma_original_images_by_product
if os.path.exists(ORIG_DIR):
    for d in os.listdir(ORIG_DIR):
        if prod_norm in normalize_name(d):
            dir_path = os.path.join(ORIG_DIR, d, "artiklar")
            if os.path.exists(dir_path):
                print(f"\nFound folder in ORIG_DIR: {d}")
                for f in sorted(os.listdir(dir_path)):
                    p = os.path.join(dir_path, f)
                    if os.path.isfile(p):
                        from PIL import Image
                        try:
                            with Image.open(p) as img:
                                print(f"  {f}: size={img.size}")
                        except Exception as e:
                            pass
