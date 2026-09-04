import os
import re
import json
import numpy as np
from PIL import Image

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
TOPAZ_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"

def is_white_background_robust(img):
    try:
        img_rgb = img.convert('RGB')
        arr = np.array(img_rgb)
        h, w, _ = arr.shape
        patches = [
            arr[10:20, 10:20],
            arr[10:20, -20:-10],
            arr[-20:-10, 10:20],
            arr[-20:-10, -20:-10]
        ]
        means = [np.mean(pat, axis=(0,1)) for pat in patches]
        means.sort(key=lambda c: np.sum(c))
        bg_color = np.mean(means[1:], axis=0) # average of top 3 corners
        bg_mean = np.mean(bg_color)
        return bg_mean > 235, bg_color
    except Exception:
        return False, None

# Find the file in TEST TOPAZ
target_names = {
    "4100081": "vinhylla-amaya-low-beige",
    "4100071": "vinhylla-guuji-low-svart",
    "4100072": "vinhylla-guuji-high-svart",
    "1400041": "pall-marcos-r", # partial name
    "1400040": "pall-marcos-g",
    "3200459": "soffa-len-vit",
    "3100237": "loungestol-duke",
    "1100476": "chair-lionel-beige"
}

topaz_files = os.listdir(TOPAZ_DIR)
for prefix, name_part in target_names.items():
    matching_files = [f for f in topaz_files if name_part.lower() in f.lower() and f.endswith(".webp")]
    print(f"\nSKU {prefix} ({name_part}): Found {len(matching_files)} files in TEST TOPAZ:")
    for f in matching_files:
        path = os.path.join(TOPAZ_DIR, f)
        img = Image.open(path)
        is_wb, bg_color = is_white_background_robust(img)
        print(f"  File: {f} -> Size: {img.size} -> is_wb: {is_wb} -> bg_color: {bg_color}")
        
        # Run mask/bounding box detection logic
        if is_wb and bg_color is not None:
            img_arr = np.array(img.convert('RGB')).astype(np.float32)
            bg_color_arr = np.array(bg_color).astype(np.float32)
            diff = np.sum(np.abs(img_arr - bg_color_arr), axis=-1)
            
            # Detect shadow bounding box
            product_pixels_shadow = np.any(img_arr[5:-5, 5:-5] < 254, axis=-1)
            coords_shadow = np.argwhere(product_pixels_shadow)
            
            # Detect body bounding box
            mask_body = (diff < 25) & (img_arr[:,:,0] > 180) & (img_arr[:,:,1] > 180) & (img_arr[:,:,2] > 180)
            arr_body = img_arr.copy()
            arr_body[mask_body] = [255, 255, 255]
            product_pixels_body = np.any(arr_body[5:-5, 5:-5] < 254, axis=-1)
            coords_body = np.argwhere(product_pixels_body)
            
            if coords_shadow.size > 0:
                y_min_raw = coords_shadow[:, 0].min() + 5
                y_max_raw = coords_shadow[:, 0].max() + 5
                x_min_raw = coords_shadow[:, 1].min() + 5
                x_max_raw = coords_shadow[:, 1].max() + 5
                print(f"    Raw BBox (Shadow): x_min={x_min_raw}, y_min={y_min_raw}, x_max={x_max_raw}, y_max={y_max_raw} (width={x_max_raw-x_min_raw}, height={y_max_raw-y_min_raw})")
            if coords_body.size > 0:
                y_min_clean = coords_body[:, 0].min() + 5
                y_max_clean = coords_body[:, 0].max() + 5
                x_min_clean = coords_body[:, 1].min() + 5
                x_max_clean = coords_body[:, 1].max() + 5
                print(f"    Clean BBox (Body): x_min={x_min_clean}, y_min={y_min_clean}, x_max={x_max_clean}, y_max={y_max_clean} (width={x_max_clean-x_min_clean}, height={y_max_clean-y_min_clean})")
