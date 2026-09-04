import os
from PIL import Image
import numpy as np

dest_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-18-FTP-Remaining\artiklar"
sku = "1310-L-S"

print(f"Checking all output files for {sku}...")

# Check main image
main_path = os.path.join(dest_dir, f"{sku}.jpg")
if os.path.exists(main_path):
    with Image.open(main_path) as img:
        arr = np.array(img.convert('RGB'))
        diff = np.sum(np.abs(arr - 255.0), axis=-1)
        coords = np.argwhere(diff > 15)
        if coords.size > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            print(f"Main Image: {img.size}")
            print(f"  BBox: [{x_min}, {y_min}, {x_max}, {y_max}] (Width: {x_max-x_min}, Height: {y_max-y_min})")
            if x_min <= 33 or x_max >= img.size[0] - 33 or y_min <= 33 or y_max >= img.size[1] - 33:
                print("  WARNING: Touches margins! (CLIPPED/CROPPED)")

# Check zoom images
zoom_dir = os.path.join(dest_dir, "zoom")
for slot in range(1, 15):
    p = os.path.join(zoom_dir, f"{sku}_{slot}.jpg")
    if os.path.exists(p):
        with Image.open(p) as img:
            arr = np.array(img.convert('RGB'))
            diff = np.sum(np.abs(arr - 255.0), axis=-1)
            coords = np.argwhere(diff > 15)
            if coords.size > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                print(f"Slot {slot}: {img.size}")
                print(f"  BBox: [{x_min}, {y_min}, {x_max}, {y_max}] (Width: {x_max-x_min}, Height: {y_max-y_min})")
                if x_min <= 33 or x_max >= img.size[0] - 33 or y_min <= 33 or y_max >= img.size[1] - 33:
                    print("  WARNING: Touches margins! (CLIPPED/CROPPED)")
