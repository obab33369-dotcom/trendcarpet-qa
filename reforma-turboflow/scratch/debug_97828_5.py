import os
import json
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
CACHE_PATH = "scratch/classification_cache.json"

# Let's find the original file path for 97828_5
with open("scratch/bbox_coordinates_db.json", "r") as f:
    bbox_db = json.load(f)
    
bbox = bbox_db.get("97828_5")
print(f"SAM3 BBox in database: {bbox}")

# Search for the original image
target_path = None
for root, dirs, files in os.walk(ONEDRIVE_DIR):
    if "97828" in root.lower() or "97828" in "".join(files).lower():
        for f in files:
            if "5" in f and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                target_path = os.path.join(root, f)
                print(f"Found candidate path: {target_path}")
                break
        if target_path:
            break

if not target_path:
    print("Could not find source file for 97828_5")
    exit(1)

with Image.open(target_path) as img:
    w, h = img.size
    print(f"Original Size: {w}x{h}")
    arr = np.array(img.convert('RGB'))
    
    # Check pixels at different thresholds to find the real product mass
    for th in [15, 50, 100]:
        diff = np.sum(255 - arr, axis=-1)
        non_white = diff > th
        
        # Exclude borders
        non_white[:10, :] = False
        non_white[-10:, :] = False
        non_white[:, :10] = False
        non_white[:, -10:] = False
        
        coords = np.argwhere(non_white)
        if coords.size > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            print(f"Threshold > {th:3d}: x_min={x_min}, x_max={x_max}, y_min={y_min}, y_max={y_max}, width={x_max - x_min}, height={y_max - y_min}")
        else:
            print(f"Threshold > {th:3d}: No pixels found")
