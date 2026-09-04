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

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\armchairs\Fåtölj _Dion_ - SammetRosa\Fåtölj _Dion_ - SammetRosa-03-W-wonder.jpg"
dest_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\f5ef2c84-06ca-4e40-beac-e6e437cd6611\dion_corrected.jpg"

category = "armchair"
prod_name = "Fåtölj Dion - SammetRosa"
bbox_src = [0.185, 0.285, 0.72, 0.705]

category_info = (category, 0.85, 0.78, 0.10, False)

print("Running correction...")
process_and_correct(img_path, dest_path, bbox_src, category_info, bg_color=(255, 255, 255), sku="1200180", prod_name=prod_name)
print("Saved corrected image to:", dest_path)
