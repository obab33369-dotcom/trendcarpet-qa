import os
import glob
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ZOOM_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full", "artiklar", "zoom")

target_skus = ["1200180", "T8044-white", "97828", "1311-L-S", "LINK-SM11-light"]

print(f"Inspecting zoom directory: {ZOOM_DIR}")
if not os.path.exists(ZOOM_DIR):
    print("Zoom directory does not exist!")
    exit(1)

for sku in target_skus:
    print(f"\nSKU: {sku}")
    pattern = os.path.join(ZOOM_DIR, f"{sku}_*.jpg")
    files = sorted(glob.glob(pattern))
    if not files:
        # Also check for non-indexed main image
        main_file = os.path.join(ZOOM_DIR, f"{sku}.jpg")
        if os.path.exists(main_file):
            files.append(main_file)
            
    if not files:
        print("  No files found.")
        continue
        
    for f in files:
        try:
            with Image.open(f) as img:
                w, h = img.size
                # Let's check if the image has white borders by checking the pixels at the borders
                import numpy as np
                arr = np.array(img.convert('RGB'))
                top_edge = np.mean(arr[0, :, :])
                bottom_edge = np.mean(arr[-1, :, :])
                left_edge = np.mean(arr[:, 0, :])
                right_edge = np.mean(arr[:, -1, :])
                is_white_border = (top_edge > 254) and (bottom_edge > 254) and (left_edge > 254) and (right_edge > 254)
                print(f"  {os.path.basename(f)}: size={w}x{h}, edges=(T:{top_edge:.1f}, B:{bottom_edge:.1f}, L:{left_edge:.1f}, R:{right_edge:.1f}), white_border={is_white_border}")
        except Exception as e:
            print(f"  Error reading {os.path.basename(f)}: {e}")
