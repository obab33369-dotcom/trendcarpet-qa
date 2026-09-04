import os
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
zoom_dir = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full", "artiklar", "zoom")

print("Inspecting all slots of 97828 on disk:")
for slot in range(1, 8):
    final_file = os.path.join(zoom_dir, f"97828_{slot}.jpg")
    if os.path.exists(final_file):
        with Image.open(final_file) as img:
            w, h = img.size
            arr = np.array(img.convert('RGB'))
            diff = np.sum(255 - arr, axis=-1)
            non_white = diff > 15
            
            non_white[:5, :] = False
            non_white[-5:, :] = False
            non_white[:, :5] = False
            non_white[:, -5:] = False
            
            coords = np.argwhere(non_white)
            if coords.size > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                height = y_max - y_min
                width = x_max - x_min
                print(f"  Slot {slot}: y_min={y_min:4d}, y_max={y_max:4d}, H={height:4d} ({height/2000*100:.1f}%), W={width:4d} ({width/2000*100:.1f}%)")
            else:
                print(f"  Slot {slot}: No product detected")
    else:
        print(f"  Slot {slot}: File not found")
