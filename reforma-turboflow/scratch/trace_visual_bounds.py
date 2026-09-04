import os
import sys
import json
import re
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

from reforma_pipeline.classification import normalize_name, classify_and_size_product
from reforma_pipeline.composition import CompositionEngine
from reforma_pipeline.orchestrator import is_processed_render, extract_slot_from_filename

sku = "1200180"
slot = 3
prod_name = "Fåtölj 'Dion' - SammetRosa (1200180)"
prod_norm = normalize_name(prod_name)

# Scan OneDrive directories
wb_fix_folders = {}
if os.path.exists(NEW_WHITE_BG_DIR):
    for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
        for d in dirs:
            dir_path = os.path.join(root, d)
            has_img = any(f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)))
            if has_img:
                norm = normalize_name(d)
                wb_fix_folders[norm] = dir_path

topaz_files = {}
if os.path.exists(TOPAZ_DIR):
    for f in os.listdir(TOPAZ_DIR):
        if f.lower().endswith('.webp'):
            m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
            if m:
                prod_name_parsed = m.group(1)
                slot_parsed = int(m.group(2))
                norm = normalize_name(prod_name_parsed)
                if norm not in topaz_files:
                    topaz_files[norm] = []
                topaz_files[norm].append((slot_parsed, os.path.join(TOPAZ_DIR, f)))

orig_folders = {}
orig_sku_folders = {}
if os.path.exists(ORIG_DIR):
    for folder in os.listdir(ORIG_DIR):
        p = os.path.join(ORIG_DIR, folder, "artiklar")
        if os.path.isdir(p):
            norm = normalize_name(folder)
            orig_folders[norm] = p
            sku_match = re.search(r'\(([^)]+)\)', folder)
            if sku_match:
                sku_parsed = sku_match.group(1).strip().lower()
                orig_sku_folders[sku_parsed] = p

raw_slots = {}
# 1. Baseline
dir_path = None
if prod_norm in orig_folders:
    dir_path = orig_folders[prod_norm]
elif sku_clean.lower() in orig_sku_folders:
    dir_path = orig_sku_folders[sku_clean.lower()]
if dir_path:
    for f in os.listdir(dir_path):
        p = os.path.join(dir_path, f)
        if os.path.isfile(p) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
            raw_slots[1] = p
    zoom_dir_path = os.path.join(dir_path, "zoom")
    if os.path.isdir(zoom_dir_path):
        for f in os.listdir(zoom_dir_path):
            p = os.path.join(zoom_dir_path, f)
            if os.path.isfile(p) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                s = 2
                slot_m = re.search(r'[-_](\d+)\.[a-zA-Z]+$', f)
                if slot_m:
                    s = int(slot_m.group(1))
                raw_slots[s] = p

# 2. Topaz
if prod_norm in topaz_files:
    for s, path in topaz_files[prod_norm]:
        raw_slots[s] = path

# 3. White bg fix
found_wb_fix_dir = None
if prod_norm in wb_fix_folders:
    found_wb_fix_dir = wb_fix_folders[prod_norm]
else:
    for f_norm, d_path in wb_fix_folders.items():
        if prod_norm == f_norm or prod_norm in f_norm or f_norm in prod_norm:
            found_wb_fix_dir = d_path
            break
if found_wb_fix_dir:
    files_in_dir = [f for f in os.listdir(found_wb_fix_dir) if os.path.isfile(os.path.join(found_wb_fix_dir, f))]
    processed_renders = [f for f in files_in_dir if is_processed_render(f)]
    slots_candidates = {}
    for f in processed_renders:
        s = extract_slot_from_filename(f)
        if s is not None:
            if s not in slots_candidates:
                slots_candidates[s] = []
            slots_candidates[s].append(f)
    for s, candidates in slots_candidates.items():
        best_cand = candidates[0]
        best_score = -1
        for cand in candidates:
            cand_lower = cand.lower()
            score = 0
            if cand_lower.endswith(('.jpg', '.jpeg')) and ('-w-' in cand_lower or '-w.' in cand_lower or cand_lower.endswith(('-w.jpg', '-w.jpeg', '-w-wonder.jpg', '-w-wonder.jpeg', '-wonder-w.jpg', '-wonder-w.jpeg'))):
                score = 10
            elif cand_lower.endswith('.webp'):
                score = 5
            elif 'wonder' in cand_lower:
                score = 4
            if score > best_score:
                best_score = score
                best_cand = cand
        raw_slots[s] = os.path.join(found_wb_fix_dir, best_cand)

img_path = raw_slots[slot] if slot in raw_slots else None
print(f"Image path: {img_path}")

# Load bbox db
with open("scratch/bbox_coordinates_db.json", "r", encoding="utf-8") as f:
    bbox_db = json.load(f)
bbox_clean = bbox_db[f"{sku}_{slot}"]
print(f"SAM3 bbox: {bbox_clean}")

# Run trace
engine = CompositionEngine()
# Get background color
with Image.open(img_path) as img_raw:
    w, h = img_raw.size
    longest = max(w, h)
    scale_init = 2000.0 / longest
    new_w = int(w * scale_init)
    new_h = int(h * scale_init)
    img_resized = img_raw.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    arr = np.array(img_resized.convert('RGB'))
    patches = [arr[10:25, 10:25], arr[10:25, -25:-10], arr[-25:-10, 10:25], arr[-25:-10, -25:-10]]
    means = [np.mean(pat, axis=(0,1)) for pat in patches]
    means.sort(key=lambda c: np.sum(c))
    bg_color = np.mean(means[1:], axis=0)
    
    x_min_raw, y_min_raw, x_max_raw, y_max_raw = engine.get_shadow_bbox(img_resized, bg_color)
    print(f"Shadow bbox: {x_min_raw, y_min_raw, x_max_raw, y_max_raw}")
    
    crop_x_min = max(0, x_min_raw - 40)
    crop_y_min = max(0, y_min_raw - 20)
    crop_x_max = min(new_w, x_max_raw + 40)
    crop_y_max = min(new_h, y_max_raw + 20)
    print(f"Crop box: {crop_x_min, crop_y_min, crop_x_max, crop_y_max}")
    
    x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
    W_p = max(1.0, float(x_max_clean - x_min_clean))
    H_p = max(1.0, float(y_max_clean - y_min_clean))
    print(f"Product width: {W_p}, height: {H_p}")
    
    # Let's say scale is cached from slot 1
    bbox_clean_1 = bbox_db[f"{sku}_1"]
    W_p_1 = max(1.0, float(bbox_clean_1[2] - bbox_clean_1[0]))
    H_p_1 = max(1.0, float(bbox_clean_1[3] - bbox_clean_1[1]))
    category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
    scale_main = min((target_w * 2000) / W_p_1, (target_h * 2000) / H_p_1)
    if W_p_1 * scale_main > 1900.0:
        scale_main = 1900.0 / W_p_1
    print(f"Main scale: {scale_main}, Main H_p: {H_p_1}")
    
    scale = scale_main * (H_p_1 / H_p)
    print(f"Scale for slot 3 (normalized): {scale}")
    
    x_min_vis, x_max_vis = engine.get_visual_body_bounds(img_resized, bbox_clean)
    print(f"Visual bounds: x_min_vis={x_min_vis}, x_max_vis={x_max_vis}")
    
    W_vis = max(1.0, float(x_max_vis - x_min_vis))
    new_w_vis = int(W_vis * scale)
    new_h_body = int(H_p * scale)
    print(f"New visual width: {new_w_vis}, New body height: {new_h_body}")
    
    paste_x_body = (2000 - new_w_vis) // 2
    paste_y_body = int(2000 - (floor_pct * 2000) - new_h_body)
    print(f"Paste X body: {paste_x_body}, Paste Y body: {paste_y_body}")
    
    offset_x = x_min_vis - crop_x_min
    offset_y = y_min_clean - crop_y_min
    print(f"Offset X: {offset_x}, Offset Y: {offset_y}")
    
    paste_x = paste_x_body - int(offset_x * scale)
    paste_y = paste_y_body - int(offset_y * scale)
    print(f"Final crop paste coordinates on canvas: paste_x={paste_x}, paste_y={paste_y}")
    
    # Calculate where the visual bounds end up on the canvas
    final_x_min_vis_on_canvas = paste_x + int(offset_x * scale)
    final_x_max_vis_on_canvas = final_x_min_vis_on_canvas + new_w_vis
    final_center = (final_x_min_vis_on_canvas + final_x_max_vis_on_canvas) / 2.0
    print(f"Visual bounds on canvas: {final_x_min_vis_on_canvas} to {final_x_max_vis_on_canvas}")
    print(f"Visual center on canvas: {final_center} (deviation={final_center - 1000.0}px)")
