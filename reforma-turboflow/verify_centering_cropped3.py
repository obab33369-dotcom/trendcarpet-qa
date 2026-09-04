import os
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
CROPPED3_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "chairs_cropped3", "artiklar")
CROPPED2_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "chairs_cropped2", "artiklar")

def measure_folder_centering(folder_path, name):
    print(f"\n=== Centering stats for {name} ===")
    if not os.path.exists(folder_path):
        print("  Folder does not exist.")
        return
        
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(('.jpg', '.jpeg'))][:10]
    
    for f in files:
        fp = os.path.join(folder_path, f)
        try:
            with Image.open(fp) as img:
                arr = np.array(img.convert("L"))
                prod_y, prod_x = np.argwhere(arr < 254).T
                if prod_x.size > 0:
                    x_min, x_max = prod_x.min(), prod_x.max()
                    center_x = (x_min + x_max) / 2
                    shift = center_x - 500.0  # 500 is the center of 1000px canvas
                    print(f"  {f:30s} | bbox: x_min={x_min:3d}, x_max={x_max:3d} | Center={center_x:5.1f} | Shift={shift:+5.1f}px")
                else:
                    print(f"  {f:30s} | No product detected")
        except Exception as e:
            print(f"  {f:30s} | Error: {e}")

measure_folder_centering(CROPPED2_DIR, "chairs_cropped2 (OLD)")
measure_folder_centering(CROPPED3_DIR, "chairs_cropped3 (NEW)")
