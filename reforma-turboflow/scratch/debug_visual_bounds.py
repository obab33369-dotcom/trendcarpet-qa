import os
import sys
import json
import numpy as np
from PIL import Image
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "Topaz_processed")
bbox_db_path = "scratch/bbox_coordinates_db.json"

with open(bbox_db_path, "r", encoding="utf-8") as f:
    bbox_db = json.load(f)

# Inspect Dion chair slot 3
sku = "1200180"
slot = 3
img_key = f"{sku}_{slot}"
bbox_clean = bbox_db[img_key]
print(f"SKU {sku} slot {slot} SAM3 bbox: {bbox_clean}")

from reforma_pipeline.classification import normalize_name
from reforma_pipeline.orchestrator import is_processed_render, extract_slot_from_filename

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

prod_name = "Fåtölj 'Dion' - SammetRosa (1200180)"
prod_norm = normalize_name(prod_name)
sku_clean = "1200180"

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

print(f"Curated raw slots: {raw_slots}")
files = [raw_slots[slot]] if slot in raw_slots else []
print(f"Slot {slot} file: {files}")

if files:
    img_path = files[0]
    with Image.open(img_path) as img:
        w, h = img.size
        print(f"Original image size: {w}x{h}")
        longest = max(w, h)
        scale_init = 2000.0 / longest
        new_w = int(w * scale_init)
        new_h = int(h * scale_init)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Check visual bounds
        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
        h_p = y_max_clean - y_min_clean
        y_cutoff = y_min_clean + int(0.70 * h_p)
        
        arr = np.array(img_resized.convert('RGB'))
        upper_mass = arr[y_min_clean:max(y_min_clean + 1, y_cutoff), x_min_clean:x_max_clean, :]
        diff_from_white = np.sum(255 - upper_mass, axis=-1)
        non_white_mask = diff_from_white > 15
        
        coords = np.argwhere(non_white_mask)
        print(f"Coords shape: {coords.shape}")
        if coords.size > 0:
            x_min_vis = coords[:, 1].min() + x_min_clean
            x_max_vis = coords[:, 1].max() + x_min_clean
            print(f"Visual bounds: x_min_vis={x_min_vis}, x_max_vis={x_max_vis}, W_vis={x_max_vis - x_min_vis}")
            print(f"SAM3 bounds: x_min={x_min_clean}, x_max={x_max_clean}, W_p={x_max_clean - x_min_clean}")
            # Center of visual bounds in resized image:
            print(f"Visual center in resized image: {(x_min_vis + x_max_vis)/2.0}")
            print(f"SAM3 center in resized image: {(x_min_clean + x_max_clean)/2.0}")
