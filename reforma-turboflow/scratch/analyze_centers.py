import os
import glob
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ZOOM_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full", "artiklar", "zoom")
target_skus = ["1200180", "T8044-white", "97828", "1311-L-S", "LINK-SM11-light"]

print("--- ANALYZING ACTUAL CENTER DEVIATION ---")
for sku in target_skus:
    print(f"\nSKU: {sku}")
    files = sorted(glob.glob(os.path.join(ZOOM_DIR, f"{sku}_*.jpg")))
    for f in files:
        # Skip lifestyle slots (we can identify them if they are not 2000x2000 or if they are in the cache)
        try:
            with Image.open(f) as img:
                w, h = img.size
                if w != 2000 or h != 2000:
                    print(f"  {os.path.basename(f)}: size={w}x{h} (Lifestyle/Detail bypass, skipped)")
                    continue
                
                arr = np.array(img.convert('RGB'))
                # Detect non-white pixels (distance from 255, 255, 255 > 15)
                diff = np.sum(255 - arr, axis=-1)
                non_white = diff > 15
                
                # Exclude borders
                non_white[:5, :] = False
                non_white[-5:, :] = False
                non_white[:, :5] = False
                non_white[:, -5:] = False
                
                coords = np.argwhere(non_white)
                if coords.size == 0:
                    print(f"  {os.path.basename(f)}: No product pixels detected")
                    continue
                
                # Full bounding box including shadows
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                full_center = (x_min + x_max) / 2.0
                full_dev = full_center - 1000.0
                
                # Visual mass center (upper 70% height of product body)
                y_cutoff = y_min + int(0.70 * (y_max - y_min))
                upper_coords = coords[coords[:, 0] <= y_cutoff]
                if upper_coords.size > 0:
                    x_min_vis = upper_coords[:, 1].min()
                    x_max_vis = upper_coords[:, 1].max()
                    vis_center = (x_min_vis + x_max_vis) / 2.0
                    vis_dev = vis_center - 1000.0
                else:
                    vis_dev = full_dev
                    
                print(f"  {os.path.basename(f)}: full_center_dev={full_dev:+.1f}px, upper_visual_dev={vis_dev:+.1f}px")
        except Exception as e:
            print(f"  Error analyzing {os.path.basename(f)}: {e}")
