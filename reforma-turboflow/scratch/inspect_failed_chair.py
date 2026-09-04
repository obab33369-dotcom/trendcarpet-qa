import os
import json
import sys
from PIL import Image

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
from vision_auto_corrector import process_and_correct, call_gemini_vision, CATEGORY_TARGETS, is_white_background_robust

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\1091-white-pigmented_2.jpg"
prod_name = "Stol 'Ystad' - Vitpigmenterad Ek/Grå"
category = "chair_dining"

with Image.open(img_path) as img:
    W, H = img.size
    is_wb, bg_color = is_white_background_robust(img)
    print(f"Image dimensions: W={W}, H={H}, is_wb={is_wb}, bg_color={bg_color}")

bbox, is_closeup = call_gemini_vision(img_path, category, prod_name)
print(f"Gemini box: {bbox}, is_closeup={is_closeup}")

target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS[category]
category_info = (category, target_w, target_h, floor_pct, is_centered)

dest_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\test_chair_corrected.jpg"
correction_meta = process_and_correct(img_path, dest_path, bbox, category_info, bg_color, sku="1091-white-pigmented", prod_name=prod_name)

print("Correction metadata:")
print(json.dumps(correction_meta, indent=2))
