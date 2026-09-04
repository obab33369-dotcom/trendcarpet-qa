import os
import sys
import numpy as np
from PIL import Image

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow")
from reforma_pipeline.composition import CompositionEngine
from reforma_pipeline.qa_checker import QAChecker

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\1470_stol-oviken-blå-1-26U-wonder.webp"
bbox_clean = None  # Force fallback behavior
category = "chair_dining"
sku = "37281105"
slot = 1

img_raw = Image.open(img_path)
w, h = img_raw.size
longest = max(w, h)
scale_init = 2000.0 / longest
new_w = int(w * scale_init)
new_h = int(h * scale_init)
img = img_raw.resize((new_w, new_h), Image.Resampling.LANCZOS)
print(f"Resized Input Image Size: {img.size}")

engine = CompositionEngine()
qa_checker = QAChecker()

# Let's run compose_studio_image
canvas, scale, crop_box, paste_pos = engine.compose_studio_image(
    img=img,
    bbox_clean=bbox_clean,
    category=category,
    sku=sku,
    slot=slot,
    is_zoom_view=False,
    bg_color=np.array([255.0, 255.0, 255.0]),
    target_w=0.90,
    target_h=0.82,
    floor_pct=0.10,
    is_centered=False,
    sku_scale=None
)

print(f"Scale factor: {scale}")
print(f"Crop box: {crop_box}")
print(f"Paste pos: {paste_pos}")

# Run diagnostics
qa_res = qa_checker.run_diagnostics(
    canvas=canvas,
    bbox_clean=bbox_clean,
    crop_box=crop_box,
    paste_pos=paste_pos,
    scale=scale,
    is_cutoff_base=False,
    is_centered=False,
    category=category
)

print("\nQA Diagnostics Result:")
for k, v in qa_res.items():
    print(f"  {k}: {v}")

# Let's check top pixels of canvas
canvas_arr = np.array(canvas)
top_row = canvas_arr[0, :, :]
non_white_count = np.sum(np.any(top_row < 255, axis=-1))
print(f"\nCanvas top row non-white count: {non_white_count}")
if non_white_count > 0:
    non_white_idx = np.where(np.any(top_row < 255, axis=-1))[0]
    print(f"First 5 non-white index/colors: {[(idx, list(top_row[idx])) for idx in non_white_idx[:5]]}")
