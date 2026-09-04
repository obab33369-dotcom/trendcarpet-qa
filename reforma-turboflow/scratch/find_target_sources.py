import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

target_skus = ["1200180", "T8044-white", "97828", "1311-L-S", "LINK-SM11-light"]

print("--- SCANNING FOR MATCHING FOLDERS ---")

def scan_dir(base_dir, label):
    if not os.path.exists(base_dir):
        print(f"Directory {label} ({base_dir}) does not exist.")
        return
    print(f"\nScanning {label}:")
    for item in os.listdir(base_dir):
        item_lower = item.lower()
        for sku in target_skus:
            sku_lower = sku.lower()
            if sku_lower in item_lower:
                p = os.path.join(base_dir, item)
                if os.path.isdir(p):
                    print(f"  [Folder] {item} -> contains SKU {sku}")
                    files = os.listdir(p)
                    print(f"    Files: {sorted(files)[:15]}")
                    if len(files) > 15:
                        print(f"    ... and {len(files) - 15} more files.")
                else:
                    print(f"  [File] {item} -> contains SKU {sku}")

scan_dir(NEW_WHITE_BG_DIR, "Refoma white background fix")
scan_dir(ORIG_DIR, "reforma_original_images_by_product")
scan_dir(TOPAZ_DIR, "TEST TOPAZ")
