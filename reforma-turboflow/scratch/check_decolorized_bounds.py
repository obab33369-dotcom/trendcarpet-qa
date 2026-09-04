import os
import json
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\armchairs\Fåtölj _Dion_ - SammetRosa\Fåtölj _Dion_ - SammetRosa-03-W-wonder.jpg"

with Image.open(img_path) as img_raw:
    w, h = img_raw.size
    scale_init = 2000.0 / max(w, h)
    img_resized = img_raw.resize((int(w * scale_init), int(h * scale_init)), Image.Resampling.LANCZOS)
    
    # Load bbox db
    with open("scratch/bbox_coordinates_db.json", "r", encoding="utf-8") as f:
        bbox_db = json.load(f)
    bbox_clean = bbox_db["1200180_3"]
    x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
    h_p = y_max_clean - y_min_clean
    y_cutoff = y_min_clean + int(0.70 * h_p)
    
    arr = np.array(img_resized.convert('RGB'))
    
    # Search the entire width (0 to 2000) instead of x_min_clean:x_max_clean
    upper_mass_full = arr[y_min_clean:max(y_min_clean+1, y_cutoff), :, :]
    diffs_full = np.sum(255 - upper_mass_full.astype(np.float32), axis=-1)
    non_white_mask_full = diffs_full > 15
    
    coords_full = np.argwhere(non_white_mask_full)
    if coords_full.size > 0:
        y_min_local, x_min_local = coords_full.min(axis=0)
        y_max_local, x_max_local = coords_full.max(axis=0)
        print("Visual bounds searching entire width:")
        print(f"  x_min_vis = {x_min_local}")
        print(f"  x_max_vis = {x_max_local}")
        print(f"  Width = {x_max_local - x_min_local}")
        print(f"  Center = {(x_min_local + x_max_local)/2.0}")
