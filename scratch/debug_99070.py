import os
import re
import json
import numpy as np
from PIL import Image, ImageDraw

src_image = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\shelf\Klädhängare _Ljusdal_ 24cm - Svart\Klädhängare _Ljusdal_ 24cm - Svart-01-W-wonder.jpg"

if not os.path.exists(src_image):
    print("Source image not found.")
    exit(1)

# Let's read the status_db to see the bbox returned by Gemini
status_file = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\review_status.json"
bbox = [0.1505, 0.4465, 0.8585, 0.552] # from log output
db_key = "artiklar/99070.jpg"

with Image.open(src_image) as img:
    W, H = img.size
    print(f"Image Size: {W}x{H}")
    
    ymin_gem = int(bbox[0] * H)
    xmin_gem = int(bbox[1] * W)
    ymax_gem = int(bbox[2] * H)
    xmax_gem = int(bbox[3] * W)
    
    print(f"Gemini Box pixels: y:[{ymin_gem}, {ymax_gem}], x:[{xmin_gem}, {xmax_gem}]")
    
    # In log: [Crop] Detected product+shadow box (Hybrid): 217x1422 at y:[298,1720], x:[890,1107]
    ymin, xmin, ymax, xmax = 298, 890, 1720, 1107
    crop_w = xmax - xmin
    crop_h = ymax - ymin
    
    target_size = 1000
    target_w, target_h = 0.80, 0.83 # cabinet_large
    floor_pct = 0.10
    
    body_w = max(1, xmax_gem - xmin_gem)
    body_h = max(1, ymax_gem - ymin_gem)
    
    scale = (target_size * target_h) / body_h
    if body_w * scale > target_size * 0.90:
        scale = (target_size * 0.85) / body_w
        
    scale = min(scale, (target_size * 0.94) / crop_w)
    
    # centring constraint limit crop height
    max_body_h_px = target_size * (1.0 - floor_pct - 0.05)
    top_to_legs_px = max(1, ymax_gem - ymin)
    if top_to_legs_px * scale > max_body_h_px:
        scale = max_body_h_px / top_to_legs_px
    scale = min(scale, (target_size * 0.92) / crop_h)
    
    new_w = max(1, int(crop_w * scale))
    new_h = max(1, int(crop_h * scale))
    
    cx_prod = (xmin_gem + xmax_gem) / 2.0
    paste_x = int(round(target_size / 2.0 - (cx_prod - xmin) * scale))
    clamped_paste_x = max(0, min(target_size - new_w, paste_x))
    
    print(f"scale: {scale:.5f}")
    print(f"new_w: {new_w}, new_h: {new_h}")
    print(f"cx_prod: {cx_prod}")
    print(f"raw paste_x: {paste_x}")
    print(f"clamped_paste_x: {clamped_paste_x}")
    
    # Calculate where the product body center ends up in the final 1000x1000 canvas
    final_center_x = clamped_paste_x + (cx_prod - xmin) * scale
    print(f"Final product center X on canvas: {final_center_x:.2f} (ideal is 500.0)")
    
    canvas = Image.new("RGB", (target_size, target_size), (255, 255, 255))
    cropped = img.crop((xmin, ymin, xmax, ymax))
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas.paste(resized, (clamped_paste_x, 100)) # Y is dummy
    
    draw = ImageDraw.Draw(canvas)
    draw.line([(500, 0), (500, 1000)], fill="red", width=2)
    draw.line([(int(final_center_x), 0), (int(final_center_x), 1000)], fill="green", width=2)
    
    out_img = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\debug_99070.jpg"
    canvas.save(out_img)
    print(f"Saved visual debug image to {out_img}")
