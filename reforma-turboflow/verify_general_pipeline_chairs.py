import os
import re
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ARTIKLAR_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped", "artiklar")

# Let's find dining chair SKUs
# We can read the category mappings from run_new_white_background_ftp_pipeline.py or just check the SKUs generated
# Let's check a few SKUs that we know are chairs (e.g. 1091-white-pigmented, 19791, WS-8651A-Red-NEW, etc.)
chair_skus = [
    "1091-white-pigmented",
    "1091-black",
    "19791",
    "WS-8651A-Red-NEW",
    "LINK-SM11-light",
    "WD2001-KD-green"
]

print("==================================================")
print(" VERIFYING CHAIR SIZING IN GENERAL PIPELINE FOLDER")
print("==================================================")

verified_count = 0

for sku in chair_skus:
    img_path = os.path.join(ARTIKLAR_DIR, f"{sku}.jpg")
    if os.path.exists(img_path):
        try:
            with Image.open(img_path) as img:
                arr = np.array(img.convert("L"))
                # Threshold to detect product pixels (< 254)
                prod_y, prod_x = np.argwhere(arr < 254).T
                if prod_y.size > 0:
                    y_min, y_max = prod_y.min(), prod_y.max()
                    x_min, x_max = prod_x.min(), prod_x.max()
                    w = x_max - x_min + 1
                    h = y_max - y_min + 1
                    
                    # Target floor is y_max = 899 (for 1000px canvas)
                    floor_diff = abs(y_max - 899)
                    
                    print(f"SKU: {sku}")
                    print(f"  Dimensions: {w}x{h} ({w/1000*100:.1f}% width, {h/1000*100:.1f}% height)")
                    print(f"  Floor Level: y_max={y_max} (Target: 899, Diff: {floor_diff}px)")
                    
                    if floor_diff <= 2 and (abs(w - 820) <= 5 or abs(h - 780) <= 5):
                        print("  ✅ PASS: Perfect size and floor alignment!")
                        verified_count += 1
                    else:
                        print("  ⚠️ WARNING: Sizing or floor alignment deviation detected!")
                else:
                    print(f"SKU: {sku} - No product detected in image!")
        except Exception as e:
            print(f"SKU: {sku} - Error loading image: {e}")
    else:
        print(f"SKU: {sku} - Image file not found in staged artiklar folder.")

print(f"\nSuccessfully verified {verified_count} chairs.")
