import os
import json
import sys
from PIL import Image
import numpy as np

# Add parent path to import modules
sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
from vision_auto_corrector import process_and_correct, classify_and_size_product, CATEGORY_TARGETS, is_white_background_robust

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\YD-G18-W.jpg"
prod_name = "Pall 'Rustic' 45cm - Trä/Stål"
category = "stool"

with Image.open(img_path) as img:
    W, H = img.size
    is_wb, bg_color = is_white_background_robust(img)
    print(f"Image dimensions: W={W}, H={H}, is_wb={is_wb}, bg_color={bg_color}")

bbox = [0.038, 0.083, 0.95, 0.917]
target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS[category]
category_info = (category, target_w, target_h, floor_pct, is_centered)

dest_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\test_stool_corrected.jpg"
correction_meta = process_and_correct(img_path, dest_path, bbox, category_info, bg_color, sku="YD-G18-W", prod_name=prod_name)

print("Correction metadata:")
print(json.dumps(correction_meta, indent=2))
