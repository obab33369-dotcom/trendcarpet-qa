import os
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
final_file = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full", "artiklar", "zoom", "1200180_3.jpg")

if not os.path.exists(final_file):
    print("File does not exist!")
    exit(1)

with Image.open(final_file) as img:
    arr = np.array(img.convert('RGB'))
    diff = np.sum(255 - arr, axis=-1)
    non_white = diff > 15
    
    # Exclude thin borders
    non_white[:5, :] = False
    non_white[-5:, :] = False
    non_white[:, :5] = False
    non_white[:, -5:] = False
    
    coords = np.argwhere(non_white)
    if coords.size > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        print(f"Product bounds on disk:")
        print(f"  Vertical:   y_min={y_min}, y_max={y_max}, height={y_max - y_min}")
        print(f"  Horizontal: x_min={x_min}, x_max={x_max}, width={x_max - x_min}")
        print(f"  Center:     {(x_min + x_max)/2.0} (deviation={(x_min + x_max)/2.0 - 1000.0}px)")
        
        # Check actual visual bounds
        y_cutoff = y_min + int(0.70 * (y_max - y_min))
        upper_coords = coords[coords[:, 0] <= y_cutoff]
        if upper_coords.size > 0:
            x_min_vis = upper_coords[:, 1].min()
            x_max_vis = upper_coords[:, 1].max()
            print(f"  Visual:     x_min_vis={x_min_vis}, x_max_vis={x_max_vis}, W_vis={x_max_vis - x_min_vis}")
            print(f"  Vis Center: {(x_min_vis + x_max_vis)/2.0} (deviation={(x_min_vis + x_max_vis)/2.0 - 1000.0}px)")
