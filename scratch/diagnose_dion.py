import os
import sys
from PIL import Image
import numpy as np

# Add parent dir to path
sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
from vision_auto_corrector import classify_and_size_product, CATEGORY_TARGETS, trim_bbox_to_pixels

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\armchairs\Fåtölj _Dion_ - SammetRosa\Fåtölj _Dion_ - SammetRosa-03-W-wonder.jpg"

print("Exists:", os.path.exists(img_path))
if os.path.exists(img_path):
    with Image.open(img_path) as img:
        print("Size:", img.size)
        # Check corners
        W, H = img.size
        img_rgb = img.convert('RGB')
        corners = [
            img_rgb.getpixel((15, 15)),
            img_rgb.getpixel((W - 15, 15)),
            img_rgb.getpixel((15, H - 15)),
            img_rgb.getpixel((W - 15, H - 15))
        ]
        print("Corners:", corners)
