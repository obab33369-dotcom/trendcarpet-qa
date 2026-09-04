import os
import sys
import json
import torch
import numpy as np
from PIL import Image

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
import vision_auto_corrector
from vision_auto_corrector import (
    classify_and_size_product, CATEGORY_TARGETS, trim_bbox_to_pixels, 
    call_gemini_vision, process_and_correct
)

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\1200180_3.jpg"
dest_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\1200180_3.jpg"

category = "armchair"
prod_name = "Fåtölj Dion - SammetRosa"

# Read original image dimensions to simulate the run
with Image.open(img_path) as img:
    W, H = img.size

bbox_src = [0.185, 0.285, 0.72, 0.705] # Gemini's first bounding box of the catalog image
category_info = (category, 0.85, 0.78, 0.10, False)

print("Running correction...")
process_and_correct(img_path, dest_path, bbox_src, category_info, bg_color=(255, 255, 255), sku="1200180", prod_name=prod_name)
print("Saved corrected image to:", dest_path)
