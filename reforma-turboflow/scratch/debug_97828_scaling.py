import os
import json
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reforma_pipeline.classification import classify_and_size_product, adjust_size_by_name
from reforma_pipeline.composition import CompositionEngine
import re

sku = "97828"
prod_name = "stol-angom-beige"

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

raw_slots = {}
for root, dirs, files in os.walk(ORIG_DIR):
    if "97828" in root.lower():
        p = os.path.join(root, "artiklar")
        if os.path.exists(p):
            for f in os.listdir(p):
                if f.lower().endswith(('.jpg', '.jpeg')):
                    raw_slots[1] = os.path.join(p, f)
            zoom_p = os.path.join(p, "zoom")
            if os.path.exists(zoom_p):
                for f in os.listdir(zoom_p):
                    m = re.search(r'[-_](\d+)\.[a-zA-Z]+$', f)
                    if m:
                        slot = int(m.group(1))
                        raw_slots[slot] = os.path.join(zoom_p, f)

with open("scratch/bbox_coordinates_db.json", "r") as f:
    bbox_db = json.load(f)

category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)

engine = CompositionEngine()
sku_scale = None

for slot in sorted(raw_slots.keys()):
    if slot > 5:
        continue
    img_path = raw_slots[slot]
    img_key = f"{sku}_{slot}"
    bbox_clean = bbox_db.get(img_key)
    
    print(f"\nSlot {slot}:")
    print(f"  Passed sku_scale: {sku_scale}")
    print(f"  Engine scale_cache: {engine.scale_cache}")
    print(f"  Engine height_cache: {engine.height_cache}")
    
    if bbox_clean is None:
        continue
        
    with Image.open(img_path) as img_raw:
        w, h = img_raw.size
        scale_init = 2000.0 / max(w, h)
        img_resized = img_raw.resize((int(w * scale_init), int(h * scale_init)), Image.Resampling.LANCZOS)
        
        arr = np.array(img_resized.convert('RGB'))
        patches = [arr[10:25, 10:25], arr[10:25, -25:-10], arr[-25:-10, 10:25], arr[-25:-10, -25:-10]]
        means = [np.mean(pat, axis=(0,1)) for pat in patches]
        means.sort(key=lambda c: np.sum(c))
        bg_color = np.mean(means[1:], axis=0)
        
        final_canvas, scale_used = engine.compose_studio_image(
            img=img_resized,
            bbox_clean=bbox_clean,
            category=category,
            sku=sku,
            slot=slot,
            is_zoom_view=False,
            bg_color=bg_color,
            target_w=target_w,
            target_h=target_h,
            floor_pct=floor_pct,
            is_centered=is_centered,
            sku_scale=sku_scale
        )
        print(f"  Returned scale: {scale_used}")
        if slot == 1:
            sku_scale = scale_used
