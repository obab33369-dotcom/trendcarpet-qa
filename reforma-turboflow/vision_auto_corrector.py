import os
import sys
import re
import json
import base64
import requests
import time
import shutil
from PIL import Image, ImageDraw
import torch
import numpy as np
from ultralytics.models.sam import SAM3SemanticPredictor

# Configure UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
if not os.path.exists(REFORMA_DIR):
    REFORMA_DIR = os.getcwd()

GEMINI_ENV = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
BRAND_DICT_PATH = os.path.join(REFORMA_DIR, "brand_sku_dict.json")
FTP_UPLOAD_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v4"
INPUT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images"
SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full"
STATUS_FILE = os.path.join(FTP_UPLOAD_DIR, "review_status.json")
BACKUP_DIR = os.path.join(FTP_UPLOAD_DIR, "backup_before_correction")

def find_case_insensitive(base_dir, rel_path):
    parts = rel_path.replace('\\', '/').split('/')
    curr = base_dir
    for part in parts:
        if not os.path.isdir(curr):
            return None
        part_lower = part.lower()
        matched = None
        for item in os.listdir(curr):
            if item.lower() == part_lower:
                matched = item
                break
        if not matched:
            return None
        curr = os.path.join(curr, matched)
    return curr


# Load Gemini API Key
def load_gemini_key():
    if not os.path.exists(GEMINI_ENV):
        return None
    with open(GEMINI_ENV, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                if k.strip() == "GEMINI_API_KEY":
                    return v.strip().strip('"').strip("'")
    return None

GEMINI_API_KEY = load_gemini_key()
if not GEMINI_API_KEY:
    print("[ERROR] Gemini API key not found in GEMINI_API_KEY.env!")
    sys.exit(1)

# Category Specifications (Targets)
# format: (target_w_fill, target_h_fill, floor_pct, is_centered)
CATEGORY_TARGETS = {
    "sofa_2_seat": (0.88, 0.54, 0.13, False),
    "sofa_3_seat": (0.92, 0.48, 0.13, False),
    "bench_hallway": (0.88, 0.51, 0.10, False),
    "armchair": (0.87, 0.81, 0.10, False),
    "chair_dining": (0.68, 0.81, 0.10, False),
    "barstool": (0.54, 0.81, 0.10, False),
    "stool": (0.54, 0.54, 0.10, False),
    "table_dining": (0.90, 0.55, 0.11, False),
    "table_coffee": (0.90, 0.53, 0.11, False),
    "table_bedside": (0.62, 0.72, 0.10, False),
    "desk": (0.88, 0.72, 0.11, False),
    "sideboard_credenza": (0.90, 0.68, 0.10, False),
    "chest_of_drawers": (0.76, 0.81, 0.10, False),
    "cabinet_large": (0.80, 0.83, 0.10, False),
    "bookshelf_floor": (0.78, 0.83, 0.10, False),
    "shelf_hanging": (0.83, 0.42, 0.50, True),
    "lamp_floor": (0.46, 0.82, 0.10, False),
    "lamp_table": (0.44, 0.70, 0.12, False),
    "lamp_pendant": (0.74, 0.70, 0.50, True),
    "lamp_wall": (0.60, 0.60, 0.50, True),
    "default": (0.87, 0.87, 0.50, True)
}

SKU_COMMON_SCALES = {}
SKU_COMMON_CYS = {}

def get_base_sku(sku):
    if not sku:
        return ""
    parts = sku.split('-')
    return parts[0].strip().lower()

GLOBAL_STATUS_DB = {}

MAJOR_FURNITURE_CATEGORIES = {
    "sofa_2_seat", "sofa_3_seat", "bench_hallway", "armchair", "chair_dining",
    "barstool", "stool", "table_dining", "table_coffee", "table_bedside",
    "desk", "sideboard_credenza", "chest_of_drawers", "cabinet_large", "bookshelf_floor"
}

CATEGORY_GUIDELINES = {
    "sofa_2_seat": "The sofa should stand on the floor line and occupy a balanced width, typically between 75% and 90% of the image width.",
    "sofa_3_seat": "The sofa should stand on the floor line and occupy a balanced width, typically between 80% and 95% of the image width.",
    "bench_hallway": "The bench should stand on the floor line and occupy a balanced width (typically 75% to 90% of the image width). It is normal for it to have a lot of white space at the top since it is a low object. For angled or wide versions, a width of 60% to 75% is acceptable, and its height can be lower (e.g. 25% to 48%).",
    "chair_dining": "The dining chair is tall and narrow. It should stand on the floor line and occupy a balanced height, typically between 72% and 82% of the image height, but it is acceptable if it occupies less (e.g. 58% to 72%) if the product is wide or shown at an angled/perspective view, to prevent side margins cut-off. It is normal for it to have empty space on the sides.",
    "armchair": "The armchair should stand on the floor line and occupy a balanced height, typically between 70% and 82% of the image height, but it is acceptable if it occupies less (e.g. 55% to 70%) if the product is wide or shown at an angled/perspective view, to prevent side margins cut-off. It is normal for it to have empty space on the sides.",
    "barstool": "The barstool is tall and narrow. It should stand on the floor line and occupy a balanced height, typically between 74% and 85% of the image height, but it is acceptable if it occupies less (e.g. 58% to 74%) if the product is wide or shown at an angled/perspective view, to prevent side margins cut-off. It is normal for it to have empty space on the sides.",
    "stool": "The stool can be round, square, rectangular, or irregular. It should stand on the floor line and occupy a balanced height or width, typically between 48% and 60% of the image, but it is acceptable if it occupies less (e.g. 30% to 48%) if it is a detail shot, wide version, or angled view.",
    "table_dining": "The table should stand on the floor line and occupy a balanced width. For wide front views, it should occupy 75% to 90% of the width. For angled views, a width of 60% to 75% is expected and acceptable. The table height can be lower (e.g. 40% to 70%) for wide/angled views.",
    "table_coffee": "The coffee table is wide and low. It should stand on the floor line and occupy a balanced width. For wide front views, it should occupy 75% to 90% of the width. For angled views, a width of 60% to 75% is expected and acceptable. It is normal for it to have a lot of white space at the top. The table height can be lower (e.g. 30% to 60%) for wide/angled views.",
    "table_bedside": "The bedside table should stand on the floor line and occupy a balanced width or height, typically between 50% and 70% of the image, but it is acceptable if it occupies less (e.g. 35% to 50%) for wide or angled views.",
    "desk": "The desk should stand on the floor line and occupy a balanced width or height. For wide front views, it should occupy 75% to 90% of the width. For angled views, a width of 60% to 75% is expected and acceptable. The desk height can be lower (e.g. 50% to 70%) for wide/angled views.",
    "sideboard_credenza": "The sideboard or TV bench should stand on the floor line and occupy a balanced width. For wide front views, it should occupy 78% to 94% of the width. For angled views, a width of 60% to 94% is expected and acceptable. For side-profile or depth-wise views, it is normal for the width to be narrower (e.g. 30% to 55%) and its height to be larger (e.g. 50% to 75%). As long as it is balanced, it is a PASS.",
    "chest_of_drawers": "The chest of drawers should stand on the floor line and occupy a balanced height or width, typically between 72% and 85% of the image, but it is acceptable if it occupies less (e.g. 50% to 72%) for wide or angled views.",
    "cabinet_large": "The large cabinet or wardrobe should stand on the floor line and occupy a balanced height, typically between 75% and 90% of the image height, but it is acceptable if it occupies less (e.g. 55% to 75%) for wide or angled views.",
    "bookshelf_floor": "The floor bookshelf should stand on the floor line and occupy a balanced height, typically between 75% and 90% of the image height, but it is acceptable if it occupies less (e.g. 55% to 75%) for wide or angled views.",
    "shelf_hanging": "The hanging shelf should be centered vertically and horizontally, occupying a balanced portion of the image (typically 65% to 85% width or 35% to 50% height).",
    "lamp_floor": "The floor lamp is very tall and narrow. It should stand on the floor line and occupy about 82% to 92% of the height. It is normal to have empty space on the sides.",
    "lamp_table": "The table lamp should stand on the floor line and occupy a balanced height, typically between 60% and 75% of the image height. It is normal for it to have empty space on the sides.",
    "lamp_pendant": "The pendant lamp should be centered vertically and horizontally, occupying about 60% to 80% of the width or height.",
    "lamp_wall": "The wall lamp should be centered vertically and horizontally, occupying about 50% to 70% of the width or height.",
    "default": "The object should be centered and occupy a realistic proportion of the frame, looking balanced. For small accessories (e.g. felt pads, care kits, floor protectors, hardware), centering and size guidelines are very lenient; as long as the items are fully visible and on a clean white background, it is a PASS."
}

# Load bad crops list to force re-processing
BAD_CROPS_FILE = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\bad_crops_report.json"
BAD_CROPS = set()
if os.path.exists(BAD_CROPS_FILE):
    try:
        with open(BAD_CROPS_FILE, 'r', encoding='utf-8') as bf:
            bad_data = json.load(bf)
            for item in bad_data:
                filename = item.get("filename")
                if filename:
                    BAD_CROPS.add(filename.lower())
        print(f"Loaded {len(BAD_CROPS)} files from bad crops report to force re-processing.")
    except Exception as e:
        print(f"Failed to load bad crops report: {e}")

def get_target_size(dest_path):
    """Determine target square canvas size based on output slot."""
    path_lower = dest_path.lower().replace("\\", "/")
    if "/liten/" in path_lower:
        return 400
    elif "/zoom/" in path_lower:
        return 2000
    else:
        return 1000

def ensure_square_canvas(img_path, target_size, category="default"):
    """Place image on a white square canvas of target_size and save in-place with category-aware vertical positioning."""
    try:
        with Image.open(img_path) as img:
            img = img.convert('RGB')
            w, h = img.size
            # If already exact target size and square, skip
            if w == target_size and h == target_size:
                return
            # Create square canvas
            canvas = Image.new("RGB", (target_size, target_size), (255, 255, 255))
            
            # Category-aware vertical positioning and height limits
            target_w, _, floor_pct, is_centered = CATEGORY_TARGETS.get(category, (0.85, 0.85, 0.50, True))
            
            if category == "lamp_pendant":
                # Pendant lamps top-aligned
                max_h = target_size - (10 if target_size > 400 else 0)
                scale = min(target_size / w, max_h / h)
            elif is_centered:
                scale = min(target_size / w, target_size / h)
            else:
                # Floor standing categories: reserve floor_pct at bottom and 5% safety margin at top
                max_h = target_size * (1.0 - floor_pct - 0.05)
                # Keep it at least 50% of target_size to avoid shrinking too much
                max_h = max(max_h, target_size * 0.50)
                # Allow wide items to occupy up to target_w, but keep at least 3% safety margin on sides
                max_w_pct = min(0.97, target_w + 0.02)
                scale = min((target_size * max_w_pct) / w, max_h / h)
                
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Center horizontally
            paste_x = (target_size - new_w) // 2
            
            if category == "lamp_pendant":
                # Top align pendant lamps/stars to keep cables
                paste_y = 10 if target_size > 400 else 0
            elif is_centered:
                # Center vertically
                paste_y = (target_size - new_h) // 2
            else:
                # Align with floor line (floor_pct margin from bottom)
                paste_y = target_size - new_h - int(target_size * floor_pct)
                
            canvas.paste(resized, (paste_x, paste_y))
            canvas.save(img_path, "JPEG", quality=92)
            print(f"    [ensure_square_canvas] Saved {target_size}x{target_size} ({category}) to {os.path.basename(img_path)}")
    except Exception as e:
        print(f"    [ensure_square_canvas] Error: {e}")

def make_square_by_cropping(img_path, target_size, bbox=None):
    """
    Crop the image to a square full-bleed (no white margins) and resize to target_size.
    If bbox (ymin, xmin, ymax, xmax) is provided, we center the crop on the bbox center.
    Otherwise, we center the crop on the image center.
    """
    try:
        with Image.open(img_path) as img:
            img = img.convert('RGB')
            W, H = img.size

            if bbox:
                ymin, xmin, ymax, xmax = bbox
                cy = (ymin + ymax) / 2.0 * H
                cx = (xmin + xmax) / 2.0 * W
            else:
                cy = H / 2.0
                cx = W / 2.0

            # The crop size should be a square. We want to make it as large as possible: min(W, H).
            S = min(W, H)

            # Center the square of size S at (cx, cy)
            left = cx - S / 2.0
            top = cy - S / 2.0
            right = left + S
            bottom = top + S

            # Clamp the crop box so it lies entirely within [0, W] and [0, H]
            if left < 0:
                left = 0
                right = S
            elif right > W:
                right = W
                left = W - S

            if top < 0:
                top = 0
                bottom = S
            elif bottom > H:
                bottom = H
                top = H - S

            # Convert to integer coordinates
            crop_box = (int(round(left)), int(round(top)), int(round(right)), int(round(bottom)))
            cropped = img.crop(crop_box)
            resized = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
            resized.save(img_path, "JPEG", quality=92)
            print(f"    [make_square_by_cropping] Saved cropped {target_size}x{target_size} (centered on bbox) to {os.path.basename(img_path)}")
    except Exception as e:
        print(f"    [make_square_by_cropping] Error: {e}")

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

_sam_predictor = None

def get_sam_predictor():
    global _sam_predictor
    if _sam_predictor is None:
        print("    [SAM3] Lazy-loading SAM3SemanticPredictor on GPU...")
        model_path = os.path.join(REFORMA_DIR, "sam3.pt")
        _sam_predictor = SAM3SemanticPredictor(overrides=dict(model=model_path, conf=0.10, device="cuda", save=False))
    return _sam_predictor

def normalize_name(name):
    text = name.lower()
    # Strip leading numbers/spaces (e.g. "6 Stol _Ystad_..." -> "Stol _Ystad_...")
    text = re.sub(r'^\s*\d+\s*', '', text)
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

# Cache of all folders in NEW_WHITE_BG_DIR to avoid slow walks
WB_FIX_FOLDERS = set()
print("Indexing Refoma white background fix folder...")
if os.path.exists(NEW_WHITE_BG_DIR):
    for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
        for d in dirs:
            WB_FIX_FOLDERS.add(normalize_name(d))
print(f"Indexed {len(WB_FIX_FOLDERS)} folders in Refoma white background fix.")

def find_original_source_image(sku, prod_name, slot=1):
    prod_norm = normalize_name(prod_name)
    sku_clean = sku.strip().lower()

    # Special rule: for certain SKUs where slot 1 is cut off at the bottom, prefer slot 5 if available
    if slot == 1 and sku_clean in ["91467", "85624", "91469", "88983"]:
        src_slot5 = find_original_source_image(sku, prod_name, slot=5)
        if src_slot5 and os.path.exists(src_slot5):
            print(f"    [Slot Swap] SKU {sku} slot 1 is known to be cut off. Swapping to slot 5: {src_slot5}")
            return src_slot5

    # Check if the product has a folder in Refoma white background fix
    has_wb_fix_folder = prod_norm in WB_FIX_FOLDERS

    # 0. Check local INPUT_DIR first ONLY if it doesn't have a manual white background fix folder
    if not has_wb_fix_folder:
        if slot == 1:
            local_path = os.path.join(INPUT_DIR, "artiklar", f"{sku}.jpg")
            if os.path.exists(local_path):
                return local_path
        else:
            local_path = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_{slot}.jpg")
            if os.path.exists(local_path):
                return local_path
                
    # 1. Look in Refoma white background fix
    if os.path.exists(NEW_WHITE_BG_DIR):
        for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
            for d in dirs:
                if normalize_name(d) == prod_norm:
                    folder_path = os.path.join(root, d)
                    img_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                    
                    def parse_slot(filename):
                        fn_clean = filename.lower().rsplit('.', 1)[0]
                        # 1. Match patterns like "-01-1-W" or "-01-2-wonder"
                        m = re.search(r'-01-(\d+)[-_]', fn_clean)
                        if m:
                            return int(m.group(1))
                        # 2. Match standard formats with -W, -wonder, -26u-wonder, etc.
                        fn_suffix = re.sub(r'^\d+\s*stol\s*[a-z0-9_]*\s*[-_]', '', fn_clean)
                        suffix_matches = re.findall(r'[-_](\d+)(?:[-_]|$)', fn_suffix)
                        if suffix_matches:
                            for m_str in suffix_matches:
                                val = int(m_str)
                                if 1 <= val <= 10:
                                    return val
                        return None
                    
                    candidates = [f for f in img_files if parse_slot(f) == slot]
                    if candidates:
                        candidates.sort(key=lambda x: (
                            1 if re.search(r'-\d+-\d+', x.lower()) else 0,
                            0 if 'wonder' in x.lower() else 1,
                            1 if re.search(r'-01\s*-1', x.lower()) or '-01-1_w' in x.lower() else 0,
                            x.lower()
                        ))
                        return os.path.join(folder_path, candidates[0])
                    
                    # Fallback for slot 1
                    if slot == 1 and img_files:
                        # Find files that don't match any other slots (2-9)
                        fallback_candidates = [f for f in img_files if parse_slot(f) not in range(2, 10)]
                        if fallback_candidates:
                            fallback_candidates.sort(key=lambda x: (
                                1 if re.search(r'-\d+-\d+', x.lower()) else 0,
                                0 if 'wonder' in x.lower() else 1,
                                1 if re.search(r'-01\s*-1', x.lower()) or '-01-1_w' in x.lower() else 0,
                                x.lower()
                            ))
                            return os.path.join(folder_path, fallback_candidates[0])
                        return os.path.join(folder_path, img_files[0])
                        
    # 2. Look in TEST TOPAZ (disabled if product matches a fix folder or is a Ystad chair SKU)
    is_ystad_sku = "1979" in sku_clean
    if os.path.exists(TOPAZ_DIR) and not has_wb_fix_folder and not is_ystad_sku:
        for f in os.listdir(TOPAZ_DIR):
            if f.lower().endswith('.webp'):
                m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
                if m:
                    name_part = m.group(1)
                    s_part = int(m.group(2))
                    if normalize_name(name_part) == prod_norm and s_part == slot:
                        return os.path.join(TOPAZ_DIR, f)
                        
    # 3. Look in reforma_original_images_by_product
    if os.path.exists(ORIG_DIR):
        for folder in os.listdir(ORIG_DIR):
            sku_match = re.search(r'\(([^)]+)\)', folder)
            if sku_match:
                folder_sku = sku_match.group(1).strip().lower()
                if folder_sku == sku_clean:
                    if slot == 1:
                        folder_path = os.path.join(ORIG_DIR, folder, "artiklar")
                        if os.path.exists(folder_path):
                            candidates = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and os.path.isfile(os.path.join(folder_path, f))]
                            if candidates:
                                return os.path.join(folder_path, candidates[0])
                    else:
                        folder_path = os.path.join(ORIG_DIR, folder, "artiklar", "zoom")
                        if os.path.exists(folder_path):
                            candidates = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                            match_prefix = f"{sku_clean}_{slot}."
                            for c in candidates:
                                if c.lower().startswith(match_prefix):
                                    return os.path.join(folder_path, c)
                            
    # 4. Fallback to local INPUT_DIR if not checked in step 0
    if has_wb_fix_folder:
        if slot == 1:
            local_path = os.path.join(INPUT_DIR, "artiklar", f"{sku}.jpg")
            if os.path.exists(local_path):
                return local_path
        else:
            local_path = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_{slot}.jpg")
            if os.path.exists(local_path):
                return local_path

    return None

def get_sam3_text_prompt(category):
    category_prompts = {
        "sofa_2_seat": ["sofa", "couch"],
        "sofa_3_seat": ["sofa", "couch"],
        "bench_hallway": ["bench"],
        "armchair": ["chair", "armchair"],
        "chair_dining": ["chair"],
        "barstool": ["stool", "barstool", "chair"],
        "stool": ["stool", "pouffe"],
        "table_dining": ["table"],
        "table_coffee": ["table"],
        "table_bedside": ["table", "cabinet"],
        "desk": ["desk", "table"],
        "sideboard_credenza": ["cabinet", "sideboard"],
        "chest_of_drawers": ["cabinet", "chest of drawers", "drawers"],
        "cabinet_large": ["cabinet", "wardrobe"],
        "bookshelf_floor": ["bookshelf", "shelves"],
        "shelf_hanging": ["shelf", "shelves"],
        "lamp_floor": ["lamp", "floor lamp", "lighting"],
        "lamp_table": ["lamp", "table lamp", "lighting"],
        "lamp_pendant": ["lamp", "pendant lamp", "chandelier", "lighting"],
        "lamp_wall": ["lamp", "wall lamp", "lighting"]
    }
    return category_prompts.get(category, ["furniture"])

def apply_edge_fading_np(img_pil, margin=35, fade_bottom=True, fade_sides=True):
    img_np = np.array(img_pil).copy()
    h, w, c = img_np.shape
    
    y = np.arange(h)
    if fade_bottom:
        dist_y = np.minimum(y, h - 1 - y)
    else:
        dist_y = y
        
    if fade_sides:
        x = np.arange(w)
        dist_x = np.minimum(x, w - 1 - x)
        dist_to_edge = np.minimum(dist_x[np.newaxis, :], dist_y[:, np.newaxis])
    else:
        dist_to_edge = np.broadcast_to(dist_y[:, np.newaxis], (h, w))
        
    factor = np.clip(dist_to_edge / float(margin), 0.0, 1.0)
    factor[dist_to_edge <= 1] = 0.0
    factor = factor[:, :, np.newaxis]
    
    blended = (img_np * factor + 255.0 * (1.0 - factor)).astype(np.uint8)
    return Image.fromarray(blended)

def classify_and_size_product(prod_name):
    name_lower = prod_name.lower()
    
    # 0. Matgrupp check first to classify dining sets as dining tables
    if "matgrupp" in name_lower:
        return "table_dining"
        
    # 1. Lamp check first to prevent Bordslampa matching table keyword "bord"
    is_lamp = (any(x in name_lower for x in ["lamp", "lampa", "belysning", "stjarna", "stjärna", "advent"]) or \
              ("ljus" in name_lower and not any(c in name_lower for c in [
                  "ljusgrå", "ljusgra", "ljusblå", "ljusbla", "ljusbrun", "ljusrosa", 
                  "ljusgul", "ljusgrön", "ljusgron", "ljusröd", "ljusrod", "ljuslila",
                  "ljus valnöt", "ljus valnot", "ljus ek", "ljusek", "ljus ask", "ljusask", 
                  "ljus trä", "ljus tra", "ljus furu", "ljusfuru", "ljus sand", "ljussand", 
                  "ljus beige", "ljusbeige", "ljus matt", "ljusmatt", "ljus terrakotta", 
                  "ljus terracotta", "ljus mässing", "ljusmassing"
              ]))) and \
              not any(x in name_lower for x in ["klädhängare", "kladhangare", "hängare", "hangare", "ljusstake", "stake", "kronoberg", "ljusdal"])
    if is_lamp:
        if "golv" in name_lower:
            return "lamp_floor"
        elif any(x in name_lower for x in ["bord", "karlskrona", "satin", "boxholm", "senigallia", "fonster", "fönster", "portabel", "uppladdningsbar", "batteridriven", "laddbar"]):
            return "lamp_table"
        elif any(x in name_lower for x in ["taklampa", "pendel", "krona", "plafond", "adventstjarna", "adventstjärna", "stjarna", "stjärna", "oslo", "sally", "lotus"]):
            return "lamp_pendant"
        elif "vagg" in name_lower or "vägg" in name_lower:
            return "lamp_wall"
        else:
            return "lamp_pendant"
            
    if any(x in name_lower for x in ["soffa", "sofa", "baddsoffa", "bäddsoffa", "schaslong", "modulsoffa", "baddfatolj", "bäddfåtölj", "modul"]) and not any(x in name_lower for x in ["hylla", "hyllor", "skåp", "skap", "dresser", "byrå", "byra"]):
        if "soffbord" not in name_lower:
            is_2_seat = any(x in name_lower for x in ["2-sits", "2-seater", "2sits", "2seater", "loveseat", "love-seat", "baddfatolj", "bäddfåtölj"])
            return "sofa_2_seat" if is_2_seat else "sofa_3_seat"
            
    if any(x in name_lower for x in ["skap", "skåp", "byra", "byrå", "sideboard", "skank", "skänk", "garderob", "tv-bank", "tv-bänk", "tv bank", "tv bänk", "tvbank", "tvbänk", "vinhylla", "sidobord", "kladhangare", "klädhängare", "kladstall", "klädställ"]):
        if any(x in name_lower for x in ["byra", "byrå"]):
            return "chest_of_drawers"
        elif any(x in name_lower for x in ["sideboard", "skank", "skänk", "tv-bank", "tv-bänk", "tv bank", "tv bänk", "tvbank", "tvbänk", "sidobord"]):
            return "sideboard_credenza"
        elif any(x in name_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ", "högskåp", "hogskap"]):
            return "cabinet_large"
        else:
            if any(x in name_lower for x in ["litet", "sido", "säng"]):
                return "chest_of_drawers"
            return "cabinet_large"
            
    if any(x in name_lower for x in ["bänk", "bank", "hallbänk", "hallbank", "sittbänk", "sittbank", "dagbädd", "daybed"]):
        return "bench_hallway"
        
    if any(x in name_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"]):
        if any(x in name_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol", "lucca", "kisa", "kontorsstol"]):
            return "armchair"
        elif "barstol" in name_lower:
            return "barstool"
        elif any(x in name_lower for x in ["pall", "puff", "sittpuff"]):
            return "stool"
        else:
            return "chair_dining"
            
    if any(x in name_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord"]):
        if any(x in name_lower for x in ["matbord", "klaffbord", "slagbord", "barbord", "180x", "120x", "160", "135", "115"]):
            return "table_dining"
        elif any(x in name_lower for x in ["soffbord", "soff bord"]):
            return "table_coffee"
        elif any(x in name_lower for x in ["sangbord", "sängbord", "nattbord"]):
            return "table_bedside"
        elif any(x in name_lower for x in ["skrivbord", "avlastningsbord", "konsolbord", "skriv bord"]):
            return "desk"
        else:
            return "table_coffee"
            
    if any(x in name_lower for x in ["hylla", "hyllor", "vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "bookcase"]):
        if any(x in name_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"]):
            return "shelf_hanging"
        else:
            return "bookshelf_floor"
    return "default"

def adjust_size_by_name(category, name, target_w, target_h):
    name_clean = re.sub(r'(202[0-9]|26u)', '', name.lower())
    numbers = re.findall(r'\d+', name_clean)
    m_cross = re.search(r'(\d+)\s*x\s*(\d+)', name_clean)
    
    if category == "table_dining":
        length = 180
        if m_cross:
            length = int(m_cross.group(1))
        else:
            for num in map(int, numbers):
                if 100 <= num <= 260:
                    length = num
                    break
        scale = length / 180.0
        target_w = target_w * scale
        target_w = max(0.70, min(0.94, target_w))
    elif category == "shelf_hanging":
        width = 75
        for num in map(int, numbers):
            if 15 <= num <= 150:
                width = num
                break
        scale = width / 75.0
        target_w = target_w * scale
        target_w = max(0.65, min(0.94, target_w))
    elif category == "cabinet_large":
        height = 180
        if m_cross:
            height = int(m_cross.group(2))
        else:
            for num in map(int, numbers):
                if 100 <= num <= 240:
                    height = num
                    break
        scale = height / 180.0
        target_h = target_h * scale
        target_h = max(0.70, min(0.94, target_h))
    return target_w, target_h

def calculate_scale(category, w_curr, h_curr, target_w, target_h, floor_pct, is_centered, W=1000, H=1000, W_out=1000, H_out=1000):
    w_curr_px = w_curr * W
    h_curr_px = h_curr * H
    
    wide_categories = ["sofa_2_seat", "sofa_3_seat", "bench_hallway", "table_dining", "table_coffee", "desk", "sideboard_credenza"]
    is_wide = (category in wide_categories) and (w_curr_px / h_curr_px > 1.35 if h_curr_px > 0 else False)
    
    if is_wide:
        scale = (target_w * W_out) / w_curr_px if w_curr_px > 0 else 1.0
        max_h_px = (0.90 if is_centered else (1.0 - floor_pct - 0.05)) * H_out
        if h_curr_px * scale > max_h_px and h_curr_px > 0:
            scale = max_h_px / h_curr_px
    else:
        scale = (target_h * H_out) / h_curr_px if h_curr_px > 0 else 1.0
        max_w_px = target_w * W_out
        if w_curr_px * scale > max_w_px and w_curr_px > 0:
            scale = max_w_px / w_curr_px
            
    # Increased scale limit from 2.0 to 4.0 for high-res images
    scale = min(4.0, scale)
    
    # Height safety check to prevent armchairs/tall cabinets from extending too close to top/bottom edges
    if h_curr_px * scale > 0.92 * H_out and h_curr_px > 0:
        scale = (0.92 * H_out) / h_curr_px
        
    return scale

def is_white_background_robust(img):
    try:
        img_rgb = img.convert('RGB')
        w, h = img.size
        corners = [
            img_rgb.getpixel((15, 15)),
            img_rgb.getpixel((w - 15, 15)),
            img_rgb.getpixel((15, h - 15)),
            img_rgb.getpixel((w - 15, h - 15))
        ]
        r_avg = sum(c[0] for c in corners) / 4
        g_avg = sum(c[1] for c in corners) / 4
        b_avg = sum(c[2] for c in corners) / 4
        bg_mean = (r_avg + g_avg + b_avg) / 3
        is_wb = bg_mean > 230
        return is_wb, (int(r_avg), int(g_avg), int(b_avg))
    except Exception:
        try:
            w, h = img.size
            c = img.convert('RGB').getpixel((10, 10))
            return sum(c)/3 > 240, c
        except Exception:
            return False, None

def union_boxes(boxes):
    valid_boxes = []
    for b in boxes:
        if isinstance(b, list) and len(b) == 4:
            try:
                b_floats = [float(x) for x in b]
                # Check if values are normalized (0-1) or 0-1000 integers
                # If any value is > 1.05, it is likely on a 1000-scale
                if any(x > 1.05 for x in b_floats):
                    b_floats = [x / 1000.0 for x in b_floats]
                valid_boxes.append(b_floats)
            except Exception:
                pass
            
    if not valid_boxes:
        return None
        
    ymin = min(b[0] for b in valid_boxes)
    xmin = min(b[1] for b in valid_boxes)
    ymax = max(b[2] for b in valid_boxes)
    xmax = max(b[3] for b in valid_boxes)
    return [ymin, xmin, ymax, xmax]

def extract_bbox_from_parsed(parsed):
    if isinstance(parsed, list):
        # Case A: flat list of 4 numbers, e.g. [ymin, xmin, ymax, xmax]
        try:
            if len(parsed) == 4 and all(isinstance(float(x), float) for x in parsed):
                return union_boxes([parsed])
        except Exception:
            pass
            
        # Case B: list of dicts, e.g. [{"bbox": [...]}, ...]
        boxes = []
        for item in parsed:
            if isinstance(item, dict):
                for key in ["bbox", "box_2d"]:
                    if key in item and isinstance(item[key], list):
                        boxes.append(item[key])
        if boxes:
            return union_boxes(boxes)
        
    if isinstance(parsed, dict):
        for key in ["bbox", "box_2d"]:
            if key in parsed:
                val = parsed[key]
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], list):
                    return union_boxes(val)
                if isinstance(val, list):
                    if len(val) == 4:
                        return union_boxes([val])
                    elif len(val) > 4 and len(val) % 4 == 0:
                        chunked = [val[i:i+4] for i in range(0, len(val), 4)]
                        return union_boxes(chunked)
    return None

def call_gemini_vision(img_path, category, prod_name):
    with open(img_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode('utf-8')
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    category_prompts = {
        "sofa_2_seat": "Analyze this image of a sofa. Identify the exact boundaries of the sofa body (cushions, armrests, backrest, and legs all the way to where they touch the floor), strictly excluding the floor shadows and reflections on the floor.",
        "sofa_3_seat": "Analyze this image of a sofa. Identify the exact boundaries of the sofa body (cushions, armrests, backrest, and legs all the way to where they touch the floor), strictly excluding the floor shadows and reflections on the floor.",
        "bench_hallway": "Analyze this image of a hallway bench. Identify the exact boundaries of the bench body (seat and legs all the way to where they touch the floor), strictly excluding the floor shadows.",
        "chair_dining": "Analyze this image of a dining chair. Identify the exact boundaries of the chair body, including the backrest, seat, armrests, and legs all the way to where they touch the floor. Strictly exclude the floor shadow underneath and any reflections.",
        "armchair": "Analyze this image of an armchair. Identify the exact boundaries of the armchair body, including the backrest, seat, armrests, and legs all the way to where they touch the floor. Strictly exclude the floor shadow underneath and any reflections.",
        "barstool": "Analyze this image of a barstool. Identify the exact boundaries of the barstool body, including the seat, backrest (if any), footrest, and legs all the way to where they touch the floor. Strictly exclude the floor shadow underneath and any reflections.",
        "stool": "Analyze this image of a stool/pouffe. Identify the exact boundaries of the stool body, including the seat and legs all the way to where they touch the floor. Strictly exclude the floor shadow underneath and any reflections.",
        "table_dining": "Analyze this image of a dining table. Identify the exact boundaries of the table, including the tabletop and all legs all the way to where they touch the floor. Do not include any surrounding chairs if visible. Strictly exclude the floor shadows underneath the table legs.",
        "table_coffee": "Analyze this image of a coffee table. Identify the exact boundaries of the table, including the tabletop and all legs all the way to where they touch the floor. Do not include any surrounding items. Strictly exclude the floor shadows underneath the table legs.",
        "table_bedside": "Analyze this image of a bedside table. Identify the exact boundaries of the table, including the tabletop and legs all the way to where they touch the floor. Strictly exclude the floor shadows underneath.",
        "desk": "Analyze this image of a desk. Identify the exact boundaries of the desk, including the desktop, drawers, and legs all the way to where they touch the floor. Strictly exclude the floor shadows underneath.",
        "sideboard_credenza": "Analyze this image of a sideboard/tv bench/credenza. Identify the exact boundaries of the cabinet/tv bench body, including its doors, drawers, and legs/metal frame base all the way to where they touch the floor. Strictly exclude the floor shadows.",
        "chest_of_drawers": "Analyze this image of a chest of drawers. Identify the exact boundaries of the cabinet body, including its drawers, top, and legs/base all the way to where they touch the floor. Strictly exclude the floor shadows.",
        "cabinet_large": "Analyze this image of a wardrobe/large cabinet. Identify the exact boundaries of the cabinet body, including its doors, drawers, shelves, and legs/base all the way to where they touch the floor. Strictly exclude the floor shadows and any wall reflections.",
        "bookshelf_floor": "Analyze this image of a standing bookshelf. Identify the exact boundaries of the shelf unit, including all shelves, drawers (if any), and legs/base all the way to where they touch the floor. Strictly exclude the floor shadows.",
        "shelf_hanging": "Analyze this image of a wall-mounted shelf. Identify the exact boundaries of the shelf unit, including all shelves and brackets. Do not include wall shadows or brackets that are part of the wall.",
        "lamp_floor": "Analyze this image of a floor lamp. Identify the exact boundaries of the lamp body, including the shade, stand, and base all the way to where it touches the floor. Exclude floor shadows.",
        "lamp_table": "Analyze this image of a table lamp. Identify the exact boundaries of the lamp body, including the shade, stand, and base. Exclude wall/table shadows.",
        "lamp_pendant": "Analyze this image of a pendant lamp. Identify the exact boundaries of the main lamp fixture, including the shade. Exclude the ceiling mount or long hanging cables if they extend all the way to the top of the frame.",
        "lamp_wall": "Analyze this image of a wall lamp. Identify the exact boundaries of the lamp fixture, including the shade and wall bracket. Exclude wall shadows.",
        "default": "Analyze this image of a product. Identify the exact boundaries of the physical product body, strictly excluding any floor shadows, wall shadows, reflections, or packaging."
    }
    
    cat_desc = category_prompts.get(category, category_prompts["default"])
    if prod_name and category == "table_dining":
        is_set = any(x in prod_name.lower() for x in ["matgrupp", "set", "sats"]) or (("bord" in prod_name.lower()) and ("stolar" in prod_name.lower()))
        if is_set:
            cat_desc = "Analyze this image of a dining set (table and chairs). Identify the exact boundaries of the entire dining set composition, including the dining table and all chairs surrounding it. Do not exclude the chairs. Strictly exclude floor shadows."
            
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"You are an expert product image cropping assistant. {cat_desc}\n"
                            "Analyze the image and classify its image_type as one of the following:\n"
                            "- 'catalog_shot': A shot showing the entire product/furniture piece on a plain background.\n"
                            "- 'detail_shot': A close-up, detail view, crop, or texture shot showing only a part of the product (e.g., drawer handles, table corner, fabric, legs, backrest details).\n"
                            "- 'dimension_drawing': A sketch, blueprint, line drawing, or technical drawing showing dimensions/measurements/text.\n\n"
                            "Return a JSON object containing:\n"
                            "1. 'bbox': The normalized bounding box of the product body or product detail in [ymin, xmin, ymax, xmax] format. For 'detail_shot', provide the bounding box of the detail itself. For 'dimension_drawing', provide the bounding box of the main sketch.\n"
                            "2. 'image_type': The classified string ('catalog_shot', 'detail_shot', or 'dimension_drawing').\n\n"
                            "Values for bbox must be floats between 0.0 and 1.0 (where 0.0 is top/left and 1.0 is bottom/right).\n"
                            "Return ONLY a JSON block like: {\"bbox\": [ymin, xmin, ymax, xmax], \"image_type\": \"catalog_shot\"}"
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    for attempt in range(6):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=25)
            if res.status_code == 200:
                resp_json = res.json()
                text = resp_json['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(text.strip())
                bbox = extract_bbox_from_parsed(parsed)
                image_type = parsed.get("image_type", "catalog_shot")
                if "is_closeup_or_sketch" in parsed:
                    if parsed["is_closeup_or_sketch"]:
                        image_type = "detail_shot"
                if bbox:
                    return bbox, image_type
            elif res.status_code == 429:
                backoff = 6 * (attempt + 1)
                print(f"    Rate limit hit, waiting {backoff} seconds...")
                time.sleep(backoff)
            else:
                print(f"    API Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"    API Exception: {e}")
        time.sleep(2)
    return None, "catalog_shot"

def call_gemini_verification(img_path, category, w_expected, h_expected, y_expected_center, is_centered, is_round_table=False, scaled_by=None, prod_name=None):
    with open(img_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode('utf-8')
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    if category == "lamp_pendant":
        alignment_instruction = (
            "- Centered horizontally (horizontal center at 50.0%).\n"
            "- Aligned to the top of the frame (pendant lamp cord/mount near the top of the canvas, typically 0-5% from top margin)."
        )
    elif is_centered:
        alignment_instruction = (
            "- Centered horizontally (horizontal center at 50.0%).\n"
            "- Centered vertically (vertical center at 50.0%)."
        )
    else:
        floor_pct = 1.0 - (y_expected_center + h_expected / 2.0)
        alignment_instruction = (
            "- Centered horizontally (horizontal center at 50.0%).\n"
            f"- Aligned with the floor line at the bottom: its bottom edge (legs/base) must sit on the floor line (typically between 5% and 15% from the bottom of the image, e.g. around {floor_pct*100:.0f}%). As long as the product stands firmly near this floor line and is not floating high up (e.g. above 20%) or cut off at the bottom, it is a PASS."
        )
        
    guideline = CATEGORY_GUIDELINES.get(category, CATEGORY_GUIDELINES["default"])
    if category == "cabinet_large" and prod_name and any(x in prod_name.lower() for x in ["hängare", "hangare", "ställ", "stall", "garderobstång", "lotorp"]):
        guideline = "The coat rack / clothes rack / clothes hanger should stand on the floor line and occupy a balanced height, typically between 75% and 90% of the image height. Do NOT expect a solid cabinet or wardrobe box; it is an open frame structure."
    
    # Override guidelines for round/square/oval tables to prevent QA mismatch
    if is_round_table:
        if category == "table_coffee":
            guideline = "The coffee table can be round, square, oval, or rectangular. It should stand on the floor line and occupy about 55% to 70% of the width and height, centered."
        elif category == "table_dining":
            guideline = "The dining table/set can be round, square, oval, or rectangular. It should stand on the floor line and occupy about 70% to 85% of the width and height, centered."

    if prod_name:
        is_set = any(x in prod_name.lower() for x in ["3st", "2st", "set", "satsbord", "sats", "matgrupp", "delar"])
        if is_set:
            guideline += "\nNote: This product is a set of items (e.g. nesting tables, dining set, or multi-piece unit). It is expected and normal to see multiple objects in the image composition, rather than a single standalone product."

    size_instruction = "occupy a realistic and balanced portion of the image (typically between 40% and 85% of the canvas width or height, or between 30% and 85% for low and wide objects like coffee tables, TV benches, or hall benches, looking prominent but with clean white margins all around and never cut off at the edges)"

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"You are a quality assurance assistant for a premium furniture store. Analyze this corrected product image of category '{category}'.\n"
                            f"Guidelines for this category:\n{guideline}\n\n"
                            f"The furniture object should be:\n"
                            f"{alignment_instruction}\n"
                            f"- Sized reasonably: it should {size_instruction} without being tiny or cut off.\n"
                            f"- Fully visible and not cut off at any edge of the image frame.\n"
                            f"- Free of any visible rectangular borders, crop boxes, or background seams (the background canvas must be a clean, uniform color).\n\n"
                            "Verify if the image composition is high-quality, centered, and meets these standards.\n"
                            "Important Notes for Verification:\n"
                            "1. Thin Legs & Wireframes: If the product has very thin legs (e.g. thin black metal legs, wireframe base, or slender posts) on a white background, look extremely closely at the bottom of the image. These thin legs are part of the product. Do NOT assume the bottom shelf or main wooden/upholstered body is the bottom of the product. The thin legs extend further down. As long as the tips of the thin legs stand firmly near the floor line (typically between 5% and 15% from the bottom), it is a PASS.\n"
                            "2. Centering & Asymmetry: If the product is shown at a three-quarter angle or has asymmetrical parts (like legs extending further to one side), the visual center of the main body may appear slightly off-center (e.g. 45%). This is acceptable and should be verified as PASS, provided the whole product is balanced and fits cleanly within the margins.\n"
                            "3. Side-Profile (Profile) Views: If the image shows a side-profile view of a chair, stool, or sofa, one side will naturally have the tall backrest while the other side has the lower seat/armrest. This creates a natural visual asymmetry where the top-half of one side is empty. Do NOT fail the image for centering in this case. A minor horizontal imbalance (e.g., one side having a 23% margin and the other having 30%) is completely normal and acceptable. As long as the product is generally centered, balanced, and fits cleanly within the margins, it is a PASS.\n"
                            "4. Side-Profile Sideboards & Sofas: For side-profile or depth-profile views of sideboards, cabinets, sofas, or chairs (where we see it from the narrow side rather than the wide front), the product will naturally look narrower (e.g. 30-65% width) and taller (e.g. 50-75% height) than a front view. This is expected. As long as the physical bounding box is centered, the product is fully visible with white margins, and it looks balanced, it is a PASS.\n"
                            "5. Size Tolerance: Since the image has been corrected automatically, there may be cases where the product looks slightly larger or smaller than the strict numbers in the guidelines (e.g. occupying 85% height instead of 82%, or 50% width instead of 60%). Do NOT fail the image for these minor size deviations if the overall composition looks high-quality, centered, balanced, and has clear white margins all around without touching or being cut off by the edges of the canvas.\n"
                            "6. Dimension Overlays & Sketches: If the image has overlaid dimension numbers (e.g., '140cm'), arrows, or technical drawing lines, this is a standard dimension diagram. Do NOT fail it for containing text or arrows; it should be verified as PASS if the underlying product is correctly positioned and visible.\n"
                            "7. Low Resolution/Pixelation: If the corrected image has some pixelation, artifacts, or blurriness, this is due to the low resolution of the original source image. Do NOT fail the image for quality/resolution/pixelation/artifacts if the positioning, centering, margins, and background are correct and meet the guidelines.\n"
                            "Ignore floor shadows and reflections.\n"
                            "Return a JSON object: {\"verified\": true/false, \"reason\": \"...\"}"
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    for attempt in range(6):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=25)
            if res.status_code == 200:
                resp_json = res.json()
                text = resp_json['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(text.strip())
                if "verified" in parsed:
                    return parsed["verified"], parsed.get("reason", "")
            elif res.status_code == 429:
                backoff = 6 * (attempt + 1)
                print(f"    Rate limit hit, waiting {backoff} seconds...")
                time.sleep(backoff)
        except Exception:
            pass
        time.sleep(2)
    return True, "Defaulted to true due to API error"

def trim_bbox_to_pixels(img, bbox):
    # bbox is [ymin, xmin, ymax, xmax] normalized
    W, H = img.size
    ymin, xmin, ymax, xmax = bbox
    ymin_px = max(0, int(ymin * H))
    xmin_px = max(0, int(xmin * W))
    ymax_px = min(H, int(ymax * H))
    xmax_px = min(W, int(xmax * W))
    
    # Sample original background color from corners
    corners = [
        img.getpixel((15, 15)),
        img.getpixel((W - 15, 15)),
        img.getpixel((15, H - 15)),
        img.getpixel((W - 15, H - 15))
    ]
    bg_mean = sum(sum(c)/3.0 for c in corners) / 4.0
    bg_threshold = max(210, min(248, bg_mean - 8))
    
    # Vectorized numpy check for performance and robustness
    img_np = np.array(img.convert('RGB')).astype(np.float32)
    bbox_img = img_np[ymin_px:ymax_px, xmin_px:xmax_px, :]
    if bbox_img.size == 0:
        return bbox
        
    pixel_means = np.mean(bbox_img, axis=2)
    product_pixels = pixel_means <= bg_threshold
    
    active_rows = np.any(product_pixels, axis=1)
    active_cols = np.any(product_pixels, axis=0)
    
    if not np.any(active_rows) or not np.any(active_cols):
        return bbox
        
    rows = np.where(active_rows)[0]
    cols = np.where(active_cols)[0]
    
    real_ymin_px = ymin_px + rows[0]
    real_ymax_px = ymin_px + rows[-1]
    real_xmin_px = xmin_px + cols[0]
    real_xmax_px = xmin_px + cols[-1]
    
    return [real_ymin_px / H, real_xmin_px / W, real_ymax_px / H, real_xmax_px / W]

def detect_shadow_robust(img_pil, bg_val=255.0):
    try:
        img_hsv = img_pil.convert('HSV')
        hsv_np = np.array(img_hsv)
        s = hsv_np[:,:,1]
        v = hsv_np[:,:,2]
        
        # Shadow pixels are grey (low saturation) and darker than background
        shadow_mask = (s < 15) & (v > 80) & (v < (bg_val - 30))
        
        # Look at the bottom 25% of the image
        H, W = img_pil.size[1], img_pil.size[0]
        bottom_zone = shadow_mask[int(H*0.75):, :]
        
        shadow_pixels = np.sum(bottom_zone)
        total_pixels = bottom_zone.size
        
        return (shadow_pixels / total_pixels) > 0.008
    except Exception:
        return True # Default to True (safe fallback to preserve pixels)

def clean_offwhite_background(img, bg_color):
    img_arr = np.array(img.convert('RGB')).astype(np.float32)
    bg_color = np.array(bg_color).astype(np.float32)
    
    epsilon = 4.0
    scale = 255.0 / np.clip(bg_color - epsilon, 1.0, 255.0)
    normalized = np.clip(img_arr * scale, 0, 255)
    
    diff = np.sum(np.abs(img_arr - bg_color), axis=-1)
    mask = np.clip((diff - 15.0) / 20.0, 0.0, 1.0)
    mask = np.expand_dims(mask, axis=-1)
    
    blended = img_arr * mask + normalized * (1.0 - mask)
    
    gray = 0.299 * blended[:,:,0] + 0.587 * blended[:,:,1] + 0.114 * blended[:,:,2]
    gray = np.expand_dims(gray, axis=-1)
    gray_img = np.concatenate([gray, gray, gray], axis=-1)
    
    final_arr = blended * mask + gray_img * (1.0 - mask)
    return Image.fromarray(np.round(final_arr).astype(np.uint8))

def process_and_correct(img_path, dest_path, bbox, category_info, bg_color=(255, 255, 255), sku=None, prod_name=None):
    category, target_w, target_h, floor_pct, is_centered = category_info
    
    # Determine target canvas size from output slot (artiklar=1000, liten=400, zoom=2000)
    target_size = get_target_size(dest_path)
    
    # 1. Try to find the original image in fix-folder or fallback folders
    src_image = None
    if sku and prod_name:
        slot = 1
        fn = os.path.basename(dest_path)
        m = re.search(r'_(\d+)\.[a-z]+$', fn.lower())
        if m:
            slot = int(m.group(1))
        src_image = find_original_source_image(sku, prod_name, slot=slot)
        
    if src_image and os.path.exists(src_image):
        print(f"    [Source Match] Using raw original image from: {src_image}")
        input_image_path = src_image
    else:
        print(f"    [Fallback] Using reviewed image as starting point: {img_path}")
        input_image_path = img_path
        
    import io
    with open(input_image_path, 'rb') as f:
        img_bytes = f.read()
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    img.load()
    
    if True: # Keep indent intact
        W, H = img.size
        
        # 2. Get background color and clean background if off-white (ONLY for non-fix, non-lifestyle shadowless images!)
        is_wb, sampled_bg = is_white_background_robust(img)
        bg_val = sum(sampled_bg) / 3.0 if sampled_bg else 255.0
        
        is_fix_image = src_image is not None and "white background fix" in src_image.lower()
        
        # Check if SKU has been previously classified as lifestyle
        is_previously_lifestyle = False
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r', encoding='utf-8') as sf:
                    s_db = {k.lower(): v for k, v in json.load(sf).items()}
                    db_key = f"artiklar/{os.path.basename(dest_path)}" if "artiklar" in dest_path.lower() else f"zoom/{os.path.basename(dest_path)}"
                    db_key_lower = db_key.lower()
                    if db_key_lower in s_db:
                        reason = s_db[db_key_lower].get("reason", "").lower()
                        if "lifestyle" in reason or "room setting" in reason or "room environment" in reason:
                            is_previously_lifestyle = True
        except Exception:
            pass
            
        is_topaz_image = src_image is not None and "test topaz" in src_image.lower()
        
        if (not is_fix_image and not is_previously_lifestyle) or is_topaz_image:
            bg_min = 200.0 if is_topaz_image else 215.0
            bg_max = 254.8 if is_topaz_image else 254.0
            if bg_val > bg_min and bg_val < bg_max:
                has_shadow = detect_shadow_robust(img, bg_val=bg_val)
                if is_topaz_image or not has_shadow:
                    if sampled_bg:
                        img = clean_offwhite_background(img, sampled_bg)
                        print(f"    [Background Cleaning] Cut out product onto pure white background (bg_val={bg_val:.1f}, is_topaz={is_topaz_image}). Furniture pixels kept original.")
                    else:
                        print(f"    [Background Cleaning] Skipping (no sampled background color).")
                else:
                    print(f"    [Background Cleaning] Skipped: image has shadow (bg_val={bg_val:.1f}). Pixels kept 100% original.")
            else:
                print(f"    [Background Cleaning] Skipped: background not off-white (bg_val={bg_val:.1f}). Pixels kept 100% original.")
        else:
            reason_str = "fix folder image" if is_fix_image else "lifestyle/miljöbild"
            print(f"    [Background Cleaning] Skipped: image is {reason_str}. Pixels kept 100% original.")

            
        # Convert Gemini normalized bbox to pixels
        ymin_gem = int(bbox[0] * H)
        xmin_gem = int(bbox[1] * W)
        ymax_gem = int(bbox[2] * H)
        xmax_gem = int(bbox[3] * W)
        
        # Refine ymax_gem using dark pixels to capture thin legs that Gemini missed
        if not is_centered:
            col_min = max(0, xmin_gem)
            col_max = min(W, xmax_gem)
            search_bottom = min(H, ymax_gem + int(H * 0.25))
            
            gray_np = np.array(img.convert('L'))
            # Find the bottom-most pixel that is quite dark (threshold based on background color to capture light wood legs) in the product column range
            leg_threshold = max(160, int(bg_val - 12)) if bg_val > 240.0 else 160
            dark_pixels = (gray_np[ymax_gem:search_bottom, col_min:col_max] < leg_threshold)
            if np.any(dark_pixels):
                relative_y = np.argwhere(dark_pixels)[:, 0].max()
                ymax_dark = ymax_gem + relative_y
                if ymax_dark > ymax_gem:
                    print(f"    [Leg Refinement] Refined ymax_gem from {ymax_gem} to {ymax_dark} based on dark leg pixels.")
                    ymax_gem = ymax_dark
        
        # Define search area for pixel-based refinement (scale-independent percentage margins)
        if not is_centered:
            # Floor-standing: allow wider margins to capture long floor shadows extending to the sides
            margin_w = max(100, int(W * 0.30)) # 30% of width
            margin_h = max(50, int(H * 0.15))  # 15% of height
        else:
            margin_w = max(50, int(W * 0.12))  # 12% of width
            margin_h = max(50, int(H * 0.12))  # 12% of height

        search_ymin = max(0, ymin_gem - margin_h)
        search_xmin = max(0, xmin_gem - margin_w)
        search_xmax = min(W, xmax_gem + margin_w)
        
        if not is_centered:
            # Floor-standing: allow search to go further down to capture legs and shadows
            search_ymax = min(H, ymax_gem + max(100, int(H * 0.25)))
        else:
            search_ymax = min(H, ymax_gem + margin_h)
        
        # 3. Find boundaries of product + shadow inside search area to ignore edge noise
        gray = img.convert('L')
        gray_np = np.array(gray)
        
        threshold = 251.0 if bg_val > 250.0 else (bg_val - 8.0)
        non_white = (gray_np < threshold)
        
        # Constrain search to search area around Gemini bbox
        search_mask = np.zeros_like(non_white, dtype=bool)
        search_mask[search_ymin:search_ymax, search_xmin:search_xmax] = True
        non_white_constrained = non_white & search_mask
        
        coords = np.argwhere(non_white_constrained)
        if coords.size > 0:
            ymin_px = int(coords[:, 0].min())
            ymax_px = int(coords[:, 0].max())
            xmin_px = int(coords[:, 1].min())
            xmax_px = int(coords[:, 1].max())
            
            # Take union of Gemini bbox and pixel-based bbox to ensure white parts aren't missed
            ymin = min(ymin_gem, ymin_px)
            xmin = min(xmin_gem, xmin_px)
            ymax = max(ymax_gem, ymax_px)
            xmax = max(xmax_gem, xmax_px)
        else:
            ymin_px, ymax_px, xmin_px, xmax_px = ymin_gem, ymax_gem, xmin_gem, xmax_gem
            ymin, xmin, ymax, xmax = ymin_gem, xmin_gem, ymax_gem, xmax_gem
            
        # Add safety margins so shadows don't get cut off inside the crop box
        # For x-directions and bottom (where shadows fade out), use a generous margin
        ymin = max(0, ymin - 15)
        xmin = max(0, xmin - 80)
        ymax = min(H, ymax + 80)
        xmax = min(W, xmax + 80)
        
        crop_w = xmax - xmin
        crop_h = ymax - ymin
        if category == "lamp_pendant":
            ymin = 0
            crop_h = ymax - ymin
            print(f"    [Pendant Lamp Override] Forcing ymin=0 to keep entire cable. crop_h adjusted to {crop_h}")
        print(f"    [Crop] Detected product+shadow box (Hybrid): {crop_w}x{crop_h} at y:[{ymin},{ymax}], x:[{xmin},{xmax}]")

        # 4. Crop
        cropped = img.crop((xmin, ymin, xmax, ymax))

        # Refine Gemini bbox with pixel-based bounds for centered categories and fix-folder images (where shadows aren't an issue)
        if is_centered or is_fix_image:
            ymin_gem = min(ymin_gem, ymin_px)
            ymax_gem = max(ymax_gem, ymax_px)
        else:
            ymin_gem = min(ymin_gem, ymin_px)

        # Horizontally: only refine for centered categories (usually pendant/wall lamps without floor shadows).
        # For floor-standing furniture, keeping Gemini's horizontal bounds prevents shadows from pulling the product off-center.
        if is_centered:
            xmin_gem = min(xmin_gem, xmin_px)
            xmax_gem = max(xmax_gem, xmax_px)
        else:
            # Floor-standing furniture:
            # To prevent clipping of wide product parts (like chair backrests or sofa arms) that Gemini might have missed,
            # we check for non-white pixels in the upper/mid section of the product (top 70% of the body height).
            # Floor shadows are located at the bottom, so they won't interfere with this upper section search.
            ymin_gem_px = int(ymin_gem)
            ymax_gem_px = int(ymax_gem)
            body_h_px = max(1, ymax_gem_px - ymin_gem_px)
            upper_limit_y = ymin_gem_px + int(body_h_px * 0.70)
            
            if ymin_gem_px < upper_limit_y:
                gray_np = np.array(img.convert('L'))
                threshold = 251.0 if bg_val > 250.0 else (bg_val - 8.0)
                # Restrict search width to +/- 150 pixels of Gemini's horizontal bounds to avoid edge noise
                search_xmin_refine = max(0, int(xmin_gem) - 150)
                search_xmax_refine = min(W, int(xmax_gem) + 150)
                upper_non_white = (gray_np[ymin_gem_px:upper_limit_y, search_xmin_refine:search_xmax_refine] < threshold)
                
                coords_upper = np.argwhere(upper_non_white)
                if coords_upper.size > 0:
                    xmin_upper_px = int(coords_upper[:, 1].min()) + search_xmin_refine
                    xmax_upper_px = int(coords_upper[:, 1].max()) + search_xmin_refine
                    
                    if xmin_upper_px < xmin_gem:
                        print(f"    [Horizontal Refinement] Expanded xmin_gem from {xmin_gem} to {xmin_upper_px} based on upper body pixels (preventing clipping).")
                        xmin_gem = xmin_upper_px
                    if xmax_upper_px > xmax_gem:
                        print(f"    [Horizontal Refinement] Expanded xmax_gem from {xmax_gem} to {xmax_upper_px} based on upper body pixels (preventing clipping).")
                        xmax_gem = xmax_upper_px
        
        body_w = max(1, xmax_gem - xmin_gem)
        body_h = max(1, ymax_gem - ymin_gem)
        
        wide_categories = ["sofa_2_seat", "sofa_3_seat", "bench_hallway", "table_dining", "table_coffee", "desk", "sideboard_credenza", "shelf_hanging"]
        if category in wide_categories:
            scale = (target_size * target_w) / body_w
        else:
            scale = (target_size * target_h) / body_h
            if body_w * scale > target_size * target_w:
                scale = (target_size * target_w) / body_w

        # Check if this is a "wide outlier" for narrow categories (shows multiple items)
        is_wide_outlier = False
        narrow_categories = ["chair_dining", "armchair", "barstool", "stool"]
        if category in narrow_categories:
            body_ratio = body_w / body_h if body_h > 0 else 1.0
            if body_ratio > 1.20:
                is_wide_outlier = True
                print(f"    [Wide Outlier Detection] Image detected as wide outlier (ratio={body_ratio:.2f} for {category}). Using group layout.")
                is_centered = True  # Force vertical centering for group/pair shots
                scale = (target_size * 0.90) / body_w  # Scale to fit width nicely (90% width)
                scale = min(scale, (target_size * 0.90) / body_h)  # Height limit
                
        # Determine if this is a main image, zoom image, or small (liten) image based on output path
        filename = os.path.basename(dest_path)
        is_zoom_image = "zoom" in dest_path.lower() or re.search(r'_\d+\.[a-z]+$', filename.lower()) is not None
        is_liten_image = "liten" in dest_path.lower() or filename.lower().endswith('_s.jpg') or filename.lower().endswith('_s.png')
        is_main_image = not is_zoom_image and not is_liten_image

        if is_main_image:
            print(f"    [Scale Alignment] Main image detected ({filename}). Scaling individually to target {target_h:.2f} to guarantee same physical height as other variants.")
            # Individually calculated scale is used, no global/common scale override.
        else:
            # Zoom or Liten image: sync scale to the main image of this specific variant
            main_scale = None
            if sku:
                # Get specific variant SKU (e.g. "87650-black" from "87650-black_2.jpg" or "87650-black_S.jpg")
                variant_sku = sku.lower()
                variant_sku = re.sub(r'_\d+$', '', variant_sku)
                variant_sku = re.sub(r'_s$', '', variant_sku)
                
                main_key_target = f"artiklar/{variant_sku}.jpg"
                
                # Check GLOBAL_STATUS_DB case-insensitively
                main_entry = None
                for k, v in GLOBAL_STATUS_DB.items():
                    if k.lower() == main_key_target.lower():
                        main_entry = v
                        break
                        
                if main_entry:
                    meta = main_entry.get("correction_metadata")
                    if meta and "target_body_h_pixels" in meta and meta["target_body_h_pixels"] is not None:
                        scaled_by = meta.get("scaled_by", "height")
                        if scaled_by == "width" and "target_body_w_pixels" in meta and meta["target_body_w_pixels"] is not None:
                            scale = meta["target_body_w_pixels"] * (target_size / 1000.0) / body_w
                        else:
                            scale = meta["target_body_h_pixels"] * (target_size / 1000.0) / body_h
                        print(f"    [Scale Alignment] Applied physical scale alignment from main image (scaled_by={scaled_by}): {scale:.4f}")
                        main_scale = scale
                    else:
                        # Fallback 1: Estimate physical scale from main image's bbox
                        bbox_main = main_entry.get("original_bbox") or main_entry.get("bbox")
                        if bbox_main:
                            ymin_m, xmin_m, ymax_m, xmax_m = bbox_main
                            body_w_m = max(1, (xmax_m - xmin_m) * 1000)
                            body_h_m = max(1, (ymax_m - ymin_m) * 1000)
                            
                            scaled_by = "width" if category in wide_categories else "height"
                            if scaled_by == "width":
                                target_body_w_pixels = target_w * 1000.0
                                scale = target_body_w_pixels * (target_size / 1000.0) / body_w
                            else:
                                target_body_h_pixels = target_h * 1000.0
                                scale = target_body_h_pixels * (target_size / 1000.0) / body_h
                            print(f"    [Scale Alignment] Estimated physical scale from variant main image bbox (scaled_by={scaled_by}): {scale:.4f}")
                            main_scale = scale
                
                # Fallback 2: Look for physical target scale from other variants of the same base SKU
                if main_scale is None:
                    base_sku = get_base_sku(sku)
                    scales_h = []
                    scales_w = []
                    scaled_by_list = []
                    for k, v in GLOBAL_STATUS_DB.items():
                        if not k.lower().startswith("artiklar/"):
                            continue
                        parts = k.split('/')
                        if len(parts) > 1:
                            fn_without_ext = parts[1][:-4]
                            if get_base_sku(fn_without_ext) == base_sku:
                                meta = v.get("correction_metadata")
                                if meta and "target_body_h_pixels" in meta and meta["target_body_h_pixels"] is not None:
                                    scales_h.append(meta["target_body_h_pixels"])
                                    if "target_body_w_pixels" in meta and meta["target_body_w_pixels"] is not None:
                                        scales_w.append(meta["target_body_w_pixels"])
                                    scaled_by_list.append(meta.get("scaled_by", "height"))
                    if scales_h:
                        median_h = float(np.median(scales_h))
                        scaled_by = scaled_by_list[0] if scaled_by_list else "height"
                        if scaled_by == "width" and scales_w:
                            median_w = float(np.median(scales_w))
                            scale = median_w * (target_size / 1000.0) / body_w
                        else:
                            scale = median_h * (target_size / 1000.0) / body_h
                        print(f"    [Scale Alignment] Fallback: Using median physical scale from other variants of base SKU {base_sku} (scaled_by={scaled_by}): {scale:.4f}")
                        main_scale = scale
            
            if main_scale is not None:
                # Physical scale was successfully synced
                scale = main_scale
            else:
                print(f"    [Scale Alignment] No variant scale information found. Using individually calculated scale: {scale:.4f}")

        # Horizontal placement analysis: Refine horizontal center (cx_prod) to focus on the upper body of the product
        # to prevent floor shadows or spreading legs from shifting the product horizontally.
        ymin_gem_px = int(ymin_gem)
        ymax_gem_px = int(ymax_gem)
        body_h_px = max(1, ymax_gem_px - ymin_gem_px)
        upper_limit_y = ymin_gem_px + int(body_h_px * 0.60)
        
        gray_np = np.array(img.convert('L'))
        threshold = 251.0 if bg_val > 250.0 else (bg_val - 8.0)
        
        # Constrain x-range to Gemini bbox
        xmin_gem_int = max(0, int(xmin_gem))
        xmax_gem_int = min(W, int(xmax_gem))
        
        if is_fix_image:
            cx_prod = W / 2.0
            print(f"    [Centering] Fix image detected. Preserving original horizontal centering (cx_prod = {cx_prod:.1f}).")
        else:
            cx_prod = (xmin_gem + xmax_gem) / 2.0
        
        if ymin_gem_px < upper_limit_y and xmin_gem_int < xmax_gem_int and not is_fix_image:
            upper_non_white = (gray_np[ymin_gem_px:upper_limit_y, xmin_gem_int:xmax_gem_int] < threshold)
            if np.any(upper_non_white):
                coords_x = np.where(upper_non_white)[1] + xmin_gem_int
                xmin_upper = int(coords_x.min())
                xmax_upper = int(coords_x.max())
                cx_prod = (xmin_upper + xmax_upper) / 2.0
                print(f"    [Centering Refinement] Refining horizontal center to {cx_prod:.1f} based on upper body bounds [{xmin_upper}, {xmax_upper}]")

        # Limit scale to ensure that the product body (excluding shadows) stays within canvas margins
        margin_x = 0.04  # 4% margin
        body_dist_left = max(1.0, cx_prod - xmin_gem)
        body_dist_right = max(1.0, xmax_gem - cx_prod)
        max_body_dist_x = max(body_dist_left, body_dist_right)
        
        scale_limit_x = (target_size * (0.5 - margin_x)) / max_body_dist_x
        scale = min(scale, scale_limit_x)
        
        # Limit height / position to respect top/bottom margins of the product body
        if category == "lamp_pendant":
            scale = min(scale, (target_size * 0.95) / crop_h)
        elif not is_centered:
            floor_line = target_size - int(target_size * floor_pct)
            max_body_h_px = floor_line - target_size * 0.05
            max_body_h_px = max(max_body_h_px, target_size * 0.50)
            if body_h * scale > max_body_h_px:
                scale = max_body_h_px / body_h
        else:
            scale = min(scale, (target_size * 0.85) / body_h)

        new_w = max(1, int(crop_w * scale))
        new_h = max(1, int(crop_h * scale))

        resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Calculate paste_y in advance to determine if we should fade the bottom edge
        temp_cy_prod = (ymin_gem + ymax_gem) / 2.0
        if is_centered:
            temp_global_cy = SKU_COMMON_CYS.get(get_base_sku(sku)) if sku else None
            if temp_global_cy is None and sku:
                base_sku = get_base_sku(sku)
                cys = []
                for k, v in GLOBAL_STATUS_DB.items():
                    parts = k.split('/')
                    if len(parts) > 1:
                        fn_without_ext = parts[1][:-4]
                        if get_base_sku(fn_without_ext) == base_sku:
                            bbox = v.get("original_bbox")
                            if bbox:
                                cys.append(((bbox[0] + bbox[2]) / 2.0) * 1000.0)
                if cys:
                    temp_global_cy = float(np.median(cys))
            if temp_global_cy is not None:
                temp_cy_prod = temp_global_cy
            temp_paste_y = int(round(target_size / 2.0 - (temp_cy_prod - ymin) * scale))
            min_paste_y = int(round(-(ymin_gem - ymin) * scale))
            max_paste_y = int(round(target_size - (ymax_gem - ymin) * scale))
            if min_paste_y <= max_paste_y:
                temp_paste_y = max(min_paste_y, min(max_paste_y, temp_paste_y))
        else:
            floor_line = target_size - int(target_size * floor_pct)
            temp_paste_y = int(round(floor_line - (ymax_gem - ymin) * scale))
            min_paste_y = int(round(-(ymin_gem - ymin) * scale))
            temp_paste_y = max(min_paste_y, temp_paste_y)
        
        if category == "lamp_pendant":
            temp_paste_y = 0

        # Bottom is faded if centered OR if the bottom of the crop box lies inside the canvas
        fade_bottom = is_centered or (temp_paste_y + new_h < target_size)

        # 5b. Apply edge fading to prevent rectangular borders when pasting onto pure white canvas
        if not is_previously_lifestyle:
            fade_margin = max(5, int(target_size * 0.035)) # 3.5% of target size
            fade_margin = min(fade_margin, int(new_w * 0.15), int(new_h * 0.15)) # but not more than 15% of product dimensions
            fade_sides = not is_fix_image
            resized = apply_edge_fading_np(resized, margin=fade_margin, fade_bottom=fade_bottom, fade_sides=fade_sides)
            print(f"    [Edge Fading] Applied edge fading with margin={fade_margin}, fade_bottom={fade_bottom}, fade_sides={fade_sides} (bg_val={bg_val:.1f})")

        # 6. Create white square canvas and paste
        canvas = Image.new("RGB", (target_size, target_size), (255, 255, 255))

        paste_x = int(round(target_size / 2.0 - (cx_prod - xmin) * scale))
        
        # Apply constraints to guarantee that the product body (excluding shadows) is NOT cut off
        if is_fix_image:
            margin_x_val = 0.04
            max_paste_x = int(round(target_size * (1.0 - margin_x_val) - (xmax_gem - xmin) * scale))
            paste_x = min(paste_x, max_paste_x)
            print(f"    [Centering Constraints] Fix image: ensuring right side (xmax_gem) is within margin. paste_x adjusted to {paste_x}")
        else:
            min_paste_x = int(round(-(xmin_gem - xmin) * scale))
            max_paste_x = int(round(target_size - (xmax_gem - xmin) * scale))
            if min_paste_x <= max_paste_x:
                paste_x = max(min_paste_x, min(max_paste_x, paste_x))

        if is_centered:
            # Centered categories: center the product body semantically
            cy_prod = (ymin_gem + ymax_gem) / 2.0
            global_common_cy = None
            if sku:
                base_sku = get_base_sku(sku)
                global_common_cy = SKU_COMMON_CYS.get(base_sku)
                if global_common_cy is None:
                    cys = []
                    for k, v in GLOBAL_STATUS_DB.items():
                        parts = k.split('/')
                        if len(parts) > 1:
                            fn_without_ext = parts[1][:-4]
                            if get_base_sku(fn_without_ext) == base_sku:
                                bbox = v.get("original_bbox")
                                if bbox:
                                    cys.append(((bbox[0] + bbox[2]) / 2.0) * 1000.0)
                    if cys:
                        global_common_cy = float(np.median(cys))
                        SKU_COMMON_CYS[base_sku] = global_common_cy
                        print(f"    [Height Alignment] Dynamically computed common vertical center for base SKU {base_sku} from GLOBAL_STATUS_DB: {global_common_cy:.1f}")
            if global_common_cy is not None:
                cy_prod = global_common_cy
                print(f"    [Height Alignment] Using aligned common vertical center: {cy_prod:.1f}")
                
            paste_y = int(round(target_size / 2.0 - (cy_prod - ymin) * scale))
            
            min_paste_y = int(round(-(ymin_gem - ymin) * scale))
            max_paste_y = int(round(target_size - (ymax_gem - ymin) * scale))
            if min_paste_y <= max_paste_y:
                paste_y = max(min_paste_y, min(max_paste_y, paste_y))
        else:
            # Floor-standing categories: align the bottom of product legs (ymax_gem) with the floor line
            floor_line = target_size - int(target_size * floor_pct)
            paste_y = int(round(floor_line - (ymax_gem - ymin) * scale))
            
            # Top of the product body must not be cut off
            min_paste_y = int(round(-(ymin_gem - ymin) * scale))
            paste_y = max(min_paste_y, paste_y)
            
        if category == "lamp_pendant":
            paste_y = 0
            
        canvas.paste(resized, (paste_x, paste_y))
        canvas.save(dest_path, "JPEG", quality=92)
        print(f"    [Save] Saved corrected image: {target_size}x{target_size} to {os.path.basename(dest_path)}")
        
    w_new = new_w / target_size
    h_new = new_h / target_size
    ymin_new = paste_y / target_size
    xmin_new = paste_x / target_size
    ymax_new = (paste_y + new_h) / target_size
    xmax_new = (paste_x + new_w) / target_size
    
    wide_categories = ["sofa_2_seat", "sofa_3_seat", "bench_hallway", "table_dining", "table_coffee", "desk", "sideboard_credenza"]
    is_wide = (category in wide_categories) and (crop_w / crop_h > 1.35 if crop_h > 0 else False)
    
    return {
        "scale_applied": scale,
        "shift_x": paste_x,
        "shift_y": paste_y,
        "new_bbox": [ymin_new, xmin_new, ymax_new, xmax_new],
        "new_width_pct": w_new,
        "new_height_pct": h_new,
        "scaled_by": "width" if is_wide else "height",
        "target_body_h_pixels": body_h * scale if is_main_image else None,
        "target_body_w_pixels": body_w * scale if is_main_image else None
    }

def process_single_main_image(f, idx, total_count, sku_to_prod, status_db, artiklar_dir, liten_dir, zoom_dir, force_correction=False):
    sku = f[:-4]
    sku_lower = sku.lower()
    
    if sku_lower not in sku_to_prod:
        print(f"[{idx+1}/{total_count}] Unrecognized SKU: {sku}. Skipping.")
        return "skipped"
        
    slug, prod_name = sku_to_prod[sku_lower]
    category = classify_and_size_product(prod_name)
    
    # Check if this SKU has a match in the manual white background fix folder
    slot = 1
    fn = os.path.basename(f)
    m = re.search(r'_(\d+)\.[a-z]+$', fn.lower())
    if m:
        slot = int(m.group(1))
    src_image = find_original_source_image(sku, prod_name, slot=slot)
    has_fix_match = src_image is not None and "white background fix" in src_image.lower()
    
    # Check if the product has a manual white background fix folder
    prod_norm = normalize_name(prod_name)
    has_wb_fix_folder = prod_norm in WB_FIX_FOLDERS
                
    if has_wb_fix_folder and not has_fix_match:
        db_key = f"artiklar/{f}"
        print(f"[{idx+1}/{total_count}] SKU: {sku} - Excluded: Product has a fix folder but slot {slot} is not in it. Deleting.")
        img_path = os.path.join(artiklar_dir, f)
        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass
        liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
        if os.path.exists(liten_file):
            try: os.remove(liten_file)
            except Exception: pass
        zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
        if os.path.exists(zoom1_file):
            try: os.remove(zoom1_file)
            except Exception: pass
        status_db[db_key] = {
            "status": "skipped",
            "reason": f"Excluded: Product has a fix folder but slot {slot} is not in it",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        return "skipped"
    
    db_key = f"artiklar/{f}"
    input_img_path = os.path.join(INPUT_DIR, "artiklar", f)
    img_path = os.path.join(artiklar_dir, f)
    
    target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS[category]
    target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
    category_info = (category, target_w, target_h, floor_pct, is_centered)

    is_bad_crop = f.lower() in BAD_CROPS
    force_this_correction = force_correction or is_bad_crop
    
    if db_key in status_db and not force_this_correction:
        status = status_db[db_key].get("status")
        # Use cache even if there is a manual white background fix match (if already processed)
        if status in ("approved", "auto-corrected", "skipped", "verification_failed"):
            print(f"[{idx+1}/{total_count}] SKU: {sku} - Already {status.upper()}. Restoring (Cached)...")
            if status == "skipped":
                img_path = os.path.join(artiklar_dir, f)
                if os.path.exists(img_path):
                    try: os.remove(img_path)
                    except Exception: pass
                liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
                if os.path.exists(liten_file):
                    try: os.remove(liten_file)
                    except Exception: pass
                zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
                if os.path.exists(zoom1_file):
                    try: os.remove(zoom1_file)
                    except Exception: pass
                return "skipped"
            if status in ("approved", "auto-corrected", "verification_failed"):
                entry = status_db.get(db_key, {})
                original_bbox = entry.get("original_bbox")
                is_detail = (entry.get("image_type") == "detail_shot") or ("closeup" in entry.get("reason", "").lower()) or ("detail" in entry.get("reason", "").lower())
                
                # Check if we should copy directly from SRC_DIR (already approved, no raw original_bbox, or detail shot)
                copy_from_src = (status in ("approved", "verification_failed")) or (not original_bbox) or is_detail
                
                if copy_from_src:
                    # Copy directly from SRC_DIR (where the approved cropped images live)
                    src_main_rel = f"artiklar/{sku}.jpg"
                    src_main_path = find_case_insensitive(SRC_DIR, src_main_rel)
                    if src_main_path and os.path.exists(src_main_path):
                        shutil.copy2(src_main_path, img_path)
                    elif os.path.exists(input_img_path):
                        shutil.copy2(input_img_path, img_path)
                        ensure_square_canvas(img_path, get_target_size(img_path), category=category)
                    
                    liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
                    src_liten_rel = f"artiklar/liten/{sku}_S.jpg"
                    src_liten_path = find_case_insensitive(SRC_DIR, src_liten_rel)
                    if src_liten_path and os.path.exists(src_liten_path):
                        shutil.copy2(src_liten_path, liten_file)
                    else:
                        input_liten_file = os.path.join(INPUT_DIR, "artiklar", "liten", f"{sku}_S.jpg")
                        if os.path.exists(input_liten_file):
                            shutil.copy2(input_liten_file, liten_file)
                            ensure_square_canvas(liten_file, get_target_size(liten_file), category=category)
                            
                    zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
                    src_zoom_rel = f"artiklar/zoom/{sku}_1.jpg"
                    src_zoom_path = find_case_insensitive(SRC_DIR, src_zoom_rel)
                    if src_zoom_path and os.path.exists(src_zoom_path):
                        shutil.copy2(src_zoom_path, zoom1_file)
                    else:
                        input_zoom1_file = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_1.jpg")
                        if os.path.exists(input_zoom1_file):
                            shutil.copy2(input_zoom1_file, zoom1_file)
                            ensure_square_canvas(zoom1_file, get_target_size(zoom1_file), category=category)
                else:
                    # status == "auto-corrected" and original_bbox is present: local correction from raw
                    if not os.path.exists(img_path) and os.path.exists(input_img_path):
                        shutil.copy2(input_img_path, img_path)
                        try:
                            with Image.open(img_path) as img_temp:
                                _, bg_color = is_white_background_robust(img_temp)
                                if not bg_color:
                                    bg_color = (255, 255, 255)
                            process_and_correct(img_path, img_path, original_bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                        except Exception as e:
                            print(f"      [Cache Warning] Local correction failed, fallback to canvas padding: {e}")
                            ensure_square_canvas(img_path, get_target_size(img_path), category=category)
                        
                        liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
                        input_liten_file = os.path.join(INPUT_DIR, "artiklar", "liten", f"{sku}_S.jpg")
                        if os.path.exists(input_liten_file):
                            shutil.copy2(input_liten_file, liten_file)
                            try:
                                process_and_correct(liten_file, liten_file, original_bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                            except Exception:
                                ensure_square_canvas(liten_file, get_target_size(liten_file), category=category)
                        
                        zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
                        input_zoom1_file = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_1.jpg")
                        if os.path.exists(input_zoom1_file):
                            shutil.copy2(input_zoom1_file, zoom1_file)
                            try:
                                process_and_correct(zoom1_file, zoom1_file, original_bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                            except Exception:
                                ensure_square_canvas(zoom1_file, get_target_size(zoom1_file), category=category)
            return status
            
    if os.path.exists(input_img_path):
        shutil.copy2(input_img_path, img_path)
        
    try:
        with Image.open(img_path) as img:
            is_wb, bg_color = is_white_background_robust(img)
            W, H = img.size
    except Exception as e:
        print(f"    ✗ Failed to open or read image file {img_path}: {e}")
        status_db[db_key] = {
            "status": "file_error",
            "reason": f"Failed to open image file: {e}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        sys.exit(f"CRITICAL_FAILURE: Image open failed for {db_key} - {e}")
        
    if not is_wb:
        print(f"[{idx+1}/{total_count}] SKU: {sku} - Lifestyle image detected. Skipping.")
        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass
        liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
        if os.path.exists(liten_file):
            try: os.remove(liten_file)
            except Exception: pass
        zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
        if os.path.exists(zoom1_file):
            try: os.remove(zoom1_file)
            except Exception: pass
        status_db[db_key] = {
            "status": "skipped",
            "reason": "Lifestyle image (no white background)",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        return "skipped"

    target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS[category]
    target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
    category_info = (category, target_w, target_h, floor_pct, is_centered)

    query_img_path = src_image if (src_image and os.path.exists(src_image)) else img_path
    print(f"[{idx+1}/{total_count}] SKU: {sku} | Name: '{prod_name}' | Cat: {category}")
    print(f"    Querying Gemini Vision API for bounding box on {os.path.basename(query_img_path)}...")
    bbox, image_type = call_gemini_vision(query_img_path, category, prod_name)

    if image_type == "lifestyle_shot":
        print(f"    [Lifestyle Detected] Gemini classified image as lifestyle_shot. Skipping.")
        img_path = os.path.join(artiklar_dir, f)
        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass
        liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
        if os.path.exists(liten_file):
            try: os.remove(liten_file)
            except Exception: pass
        zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
        if os.path.exists(zoom1_file):
            try: os.remove(zoom1_file)
            except Exception: pass
        status_db[db_key] = {
            "status": "skipped",
            "reason": "Lifestyle image (Gemini classified)",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        return "skipped"

    if not bbox:
        print(f"    ✗ Failed to get bounding box from Gemini API for {db_key}.")
        status_db[db_key] = {
            "status": "api_failed",
            "reason": "Failed to get bounding box from Gemini API",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        sys.exit(f"CRITICAL_FAILURE: Bounding box API call failed for {db_key}")

    if image_type == "detail_shot" and category in MAJOR_FURNITURE_CATEGORIES:
        print(f"    ⚠ Gemini classified main image as 'detail_shot' for major furniture category '{category}'. Overriding to 'catalog_shot' to ensure alignment.")
        image_type = "catalog_shot"

    if image_type == "detail_shot":
        reason_text = "Detail close-up (cropped to square full-bleed)"
        print(f"    ✓ Approved. {reason_text}")
        status_db[db_key] = {
            "status": "approved",
            "category": category,
            "bbox": bbox,
            "image_type": image_type,
            "target_w": target_w,
            "target_h": target_h,
            "reason": reason_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        if src_image and os.path.exists(src_image):
            print(f"    [Source Match] Copying raw original image to main before cropping: {src_image}")
            shutil.copy2(src_image, img_path)
        make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
        return "approved"
        
    # Trim bbox to actual product pixels to eliminate loose margins
    try:
        with Image.open(img_path) as img_check:
            bbox = trim_bbox_to_pixels(img_check, bbox)
    except Exception:
        pass
        
    ymin, xmin, ymax, xmax = bbox
    w_curr = xmax - xmin
    h_curr = ymax - ymin
    cx_curr = (xmin + xmax) / 2
    cy_curr = (ymin + ymax) / 2
    
    # Dynamic adjustment for round/square tables based on bounding box aspect ratio and product name
    aspect_ratio = (w_curr * W) / (h_curr * H) if h_curr > 0 else 1.0
    m_cross = re.search(r'(\d+)\s*x\s*(\d+)', prod_name.lower())
    is_square = False
    if m_cross:
        is_square = (m_cross.group(1) == m_cross.group(2))
    is_round_or_oval = any(x in prod_name.lower() for x in ["runt", "rund", "ovalt", "oval", "ø", "diam"]) or is_square or (aspect_ratio < 1.35)
    is_round_table_override = False
    if category == "table_coffee" and is_round_or_oval and aspect_ratio < 1.3:
        is_rect = any(x in prod_name.lower() for x in ["skrivbord", "avlastningsbord", "120x", "140x", "160x", "180x", "200x"])
        if not is_rect:
            target_w = 0.58
            target_h = 0.58
            category_info = (category, target_w, target_h, floor_pct, is_centered)
            is_round_table_override = True
    elif category == "table_dining" and is_round_or_oval and aspect_ratio < 1.3:
        is_rect = any(x in prod_name.lower() for x in ["140x", "160x", "180x", "200x", "220x"])
        if not is_rect:
            target_w = 0.78
            target_h = 0.78
            category_info = (category, target_w, target_h, floor_pct, is_centered)
            is_round_table_override = True
            
    # If the table or desk is rectangular but photographed from the short end (square-ish bounding box)
    # we increase target_h to prevent it from being scaled down to a tiny width.
    if not is_round_table_override:
        if category == "table_dining" and aspect_ratio < 1.4:
            target_h = 0.78
            category_info = (category, target_w, target_h, floor_pct, is_centered)
        elif category == "table_coffee" and aspect_ratio < 1.4:
            target_h = 0.72
            category_info = (category, target_w, target_h, floor_pct, is_centered)
        elif category == "desk" and aspect_ratio < 1.4:
            target_h = 0.75
            category_info = (category, target_w, target_h, floor_pct, is_centered)
            
    # Adjust target dimensions for square-ish chests of drawers, cabinets, and bookshelves
    if category in ["chest_of_drawers", "cabinet_large", "bookshelf_floor"] and 0.80 <= aspect_ratio <= 1.25:
        target_h = 0.70
        target_w = 0.70
        category_info = (category, target_w, target_h, floor_pct, is_centered)
        print(f"    [Size Adjustment] Square-ish furniture detected (aspect_ratio={aspect_ratio:.2f}). Adjusting target size to 0.70.")

    scale_needed = calculate_scale(category, w_curr, h_curr, target_w, target_h, floor_pct, is_centered)
    cx_dev = abs(cx_curr - 0.50)
    
    if not is_centered:
        target_bottom = 1.0 - floor_pct
        bottom_dev = abs(ymax - target_bottom)
    else:
        bottom_dev = abs(cy_curr - 0.50)
        
    tolerance = 0.05
    is_ok = (0.95 <= scale_needed <= 1.05) and (cx_dev <= tolerance) and (bottom_dev <= tolerance)
    if has_fix_match:
        print(f"    [Fix Match Force] SKU has a manual white background fix match. Forcing auto-correction flow...")
        is_ok = False
    
    # Rule-based is_closeup override disabled for main images to prevent false positives on tight crops.
    is_closeup = False
        
    is_tabletop_only = False
    
    if force_correction:
        print(f"    [Force Option] Bypassing normal checks to force auto-correction flow...")
        is_ok = False
        is_closeup = False
        is_tabletop_only = False
            
    if is_ok or is_closeup or is_tabletop_only:
        if is_tabletop_only:
            reason_text = "Approved (Tabletop-only detection due to white-on-white, preserved as-is)"
        else:
            reason_text = "Approved (Within tolerance)" if not is_closeup else "Detail close-up image (preserved as-is)"
        print(f"    ✓ Approved. {reason_text}")
        status_db[db_key] = {
            "status": "approved",
            "category": category,
            "bbox": bbox,
            "target_w": target_w,
            "target_h": target_h,
            "reason": reason_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        ensure_square_canvas(img_path, get_target_size(img_path), category=category)
        return "approved"
    else:
        print(f"    ✗ Fails alignment. Width={w_curr:.2f} (target {target_w:.2f}), Bottom={ymax:.2f} (target {1.0-floor_pct if not is_centered else 0.50:.2f}). Autocorrecting...")
        
        backup_path = os.path.join(BACKUP_DIR, f)
        shutil.copy2(img_path, backup_path)
        
        # Correct main image
        correction_meta = process_and_correct(img_path, img_path, bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
        
        # Verify corrected main image
        w_expected = correction_meta["new_width_pct"]
        h_expected = correction_meta["new_height_pct"]
        ymin_new, xmin_new, ymax_new, xmax_new = correction_meta["new_bbox"]
        y_expected_center = (ymin_new + ymax_new) / 2.0
            
        print("    Querying Gemini Vision API for verification...")
        verified, reason = call_gemini_verification(
            img_path, category, w_expected, h_expected, y_expected_center, is_centered,
            is_round_table=is_round_table_override, scaled_by=correction_meta.get("scaled_by"), prod_name=prod_name
        )
        
        if not verified:
            if has_fix_match:
                print(f"    ✓ Verification failed but this is a manual white background fix folder image. Overriding verification failure to approve.")
                status_db[db_key] = {
                    "status": "auto-corrected",
                    "category": category,
                    "bbox": bbox,
                    "image_type": image_type,
                    "target_w": target_w,
                    "target_h": target_h,
                    "reason": f"Auto-corrected (Fix folder override of verification fail: {reason})",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                
                # Sync correction to small (liten) and zoom_1 if they exist in input
                liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
                input_liten_file = os.path.join(INPUT_DIR, "artiklar", "liten", f"{sku}_S.jpg")
                if os.path.exists(input_liten_file):
                    shutil.copy2(input_liten_file, liten_file)
                    liten_backup = os.path.join(BACKUP_DIR, f"{sku}_S.jpg")
                    shutil.copy2(liten_file, liten_backup)
                    process_and_correct(liten_file, liten_file, bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                    if image_type == "detail_shot":
                        make_square_by_cropping(liten_file, get_target_size(liten_file), bbox=bbox)
                    else:
                        ensure_square_canvas(liten_file, get_target_size(liten_file), category=category)
                    print(f"    ✓ Synced correction to liten: {os.path.basename(liten_file)}")
                    
                zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
                input_zoom1_file = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_1.jpg")
                if os.path.exists(input_zoom1_file):
                    shutil.copy2(input_zoom1_file, zoom1_file)
                    zoom1_backup = os.path.join(BACKUP_DIR, f"{sku}_1.jpg")
                    shutil.copy2(zoom1_file, zoom1_backup)
                    process_and_correct(zoom1_file, zoom1_file, bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                    if image_type == "detail_shot":
                        make_square_by_cropping(zoom1_file, get_target_size(zoom1_file), bbox=bbox)
                    else:
                        ensure_square_canvas(zoom1_file, get_target_size(zoom1_file), category=category)
                    print(f"    ✓ Synced correction to zoom: {os.path.basename(zoom1_file)}")
                    
                return "auto-corrected"
            # Check if the failure reason indicates it's a detail shot or close-up
            reason_lower = reason.lower()
            is_detail_reason = any(x in reason_lower for x in [
                "detail shot", "detail view", "close-up", "closeup", 
                "fabric texture", "material texture", "zoom view", "zoomed view",
                "not a full product", "not the full product", 
                "only shows a part", "only shows a portion", "close up",
                "overhead view", "top-down view", "top down view",
                "underside", "upside down", "legs pointing", "standalone product",
                "single standalone", "nesting", "set of", "cut off", "cut-off",
                "not centered", "not horizontally centered", "shifted", "margin",
                "imbalance", "floating", "occupies too much", "too small", "width",
                "height"
            ])
            is_lifestyle_reason = any(x in reason_lower for x in [
                "room setting", "room environment", "lifestyle image", "lifestyle setting",
                "textured wall", "textured floor", "textured rug", "grey wall", "concrete wall",
                "concrete floor", "curtain", "curtains", "decorations", "decorative items",
                "not a clean, uniform", "not a clean white", "uneven background", "uneven areas on the floor",
                "rectangular background", "rectangular border", "crop box", "background seam", "background seams"
            ])
            
            if is_detail_reason:
                print(f"    ✓ Verification failed but identified as a detail/close-up view. Approving as-is.")
                shutil.copy2(backup_path, img_path)
                status_db[db_key] = {
                    "status": "approved",
                    "category": category,
                    "bbox": bbox,
                    "image_type": "detail_shot",
                    "reason": f"Approved as close-up/detail shot: {reason}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
                return "approved"
            elif is_lifestyle_reason:
                print(f"    ✓ Verification failed but identified as lifestyle/room setting. Skipping.")
                if os.path.exists(img_path):
                    try: os.remove(img_path)
                    except Exception: pass
                status_db[db_key] = {
                    "status": "skipped",
                    "category": category,
                    "reason": f"Skipped based on QA background review: {reason}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                return "skipped"
            else:
                print(f"    ✗ Verification failed: {reason}. Reverting to original.")
                # Revert main image
                shutil.copy2(backup_path, img_path)
                status_db[db_key] = {
                    "status": "verification_failed",
                    "category": category,
                    "reason": reason,
                    "original_bbox": bbox,
                    "image_type": image_type,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                # Save status_db
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                if image_type == "detail_shot":
                    make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
                else:
                    ensure_square_canvas(img_path, get_target_size(img_path), category=category)
                return "verification_failed"
        else:
            print(f"    ✓ Verification success: Corrected image approved!")
            # Sync correction to small (liten) and zoom_1 if they exist in input
            liten_file = os.path.join(liten_dir, f"{sku}_S.jpg")
            input_liten_file = os.path.join(INPUT_DIR, "artiklar", "liten", f"{sku}_S.jpg")
            if os.path.exists(input_liten_file):
                shutil.copy2(input_liten_file, liten_file)
                liten_backup = os.path.join(BACKUP_DIR, f"{sku}_S.jpg")
                shutil.copy2(liten_file, liten_backup)
                process_and_correct(liten_file, liten_file, bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                if image_type == "detail_shot":
                    make_square_by_cropping(liten_file, get_target_size(liten_file), bbox=bbox)
                else:
                    ensure_square_canvas(liten_file, get_target_size(liten_file), category=category)
                print(f"    ✓ Synced correction to liten: {sku}_S.jpg")
                
            zoom1_file = os.path.join(zoom_dir, f"{sku}_1.jpg")
            input_zoom1_file = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_1.jpg")
            if os.path.exists(input_zoom1_file):
                shutil.copy2(input_zoom1_file, zoom1_file)
                zoom1_backup = os.path.join(BACKUP_DIR, f"{sku}_1.jpg")
                shutil.copy2(zoom1_file, zoom1_backup)
                process_and_correct(zoom1_file, zoom1_file, bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                if image_type == "detail_shot":
                    make_square_by_cropping(zoom1_file, get_target_size(zoom1_file), bbox=bbox)
                else:
                    ensure_square_canvas(zoom1_file, get_target_size(zoom1_file), category=category)
                print(f"    ✓ Synced correction to zoom: {sku}_1.jpg")
                
            status_db[db_key] = {
                "status": "auto-corrected",
                "category": category,
                "original_bbox": bbox,
                "image_type": image_type,
                "target_w": target_w,
                "target_h": target_h,
                "correction_metadata": correction_meta,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                json.dump(status_db, sf, indent=2)
            if image_type == "detail_shot":
                make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
            else:
                ensure_square_canvas(img_path, get_target_size(img_path), category=category)
            return "auto-corrected"

def process_single_zoom_image(f, idx, total_count, sku_to_prod, status_db, zoom_dir, force_correction=False):
    if f.lower().endswith('_1.jpg'):
        m = re.match(r"^(.+?)_1\.jpg$", f, re.IGNORECASE)
        if m:
            sku = m.group(1)
            main_db_key = f"artiklar/{sku}.jpg"
            main_entry = status_db.get(main_db_key.lower(), {})
            if main_entry.get("status") == "skipped":
                img_path = os.path.join(zoom_dir, f)
                if os.path.exists(img_path):
                    try: os.remove(img_path)
                    except Exception: pass
        return "skipped"
        
    m = re.match(r"^(.+?)_\d+\.jpg$", f)
    if not m:
        return "skipped"
    sku = m.group(1)
    sku_lower = sku.lower()
    
    if sku_lower not in sku_to_prod:
        return "skipped"
        
    slug, prod_name = sku_to_prod[sku_lower]
    category = classify_and_size_product(prod_name)
    
    # Check if this SKU has a match in the manual white background fix folder
    slot = 1
    fn = os.path.basename(f)
    m_slot = re.search(r'_(\d+)\.[a-z]+$', fn.lower())
    if m_slot:
        slot = int(m_slot.group(1))
    src_image = find_original_source_image(sku, prod_name, slot=slot)
    has_fix_match = src_image is not None and "white background fix" in src_image.lower()
    
    # Check if the product has a manual white background fix folder
    prod_norm = normalize_name(prod_name)
    has_wb_fix_folder = prod_norm in WB_FIX_FOLDERS
                
    if has_wb_fix_folder and not has_fix_match:
        db_key = f"zoom/{f}"
        print(f"[{idx+1}/{total_count}] Zoom SKU: {sku} - Excluded: Product has a fix folder but slot {slot} is not in it. Deleting.")
        img_path = os.path.join(zoom_dir, f)
        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass
        status_db[db_key] = {
            "status": "skipped",
            "reason": f"Excluded: Product has a fix folder but slot {slot} is not in it",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        return "skipped"
    
    db_key = f"zoom/{f}"
    input_img_path = os.path.join(INPUT_DIR, "artiklar", "zoom", f)
    img_path = os.path.join(zoom_dir, f)
    
    target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS[category]
    target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
    category_info = (category, target_w, target_h, floor_pct, is_centered)

    is_bad_crop = (f.lower() in BAD_CROPS) or (f"{sku}.jpg".lower() in BAD_CROPS)
    force_this_correction = force_correction or is_bad_crop
    
    if db_key in status_db and not force_this_correction:
        status = status_db[db_key].get("status")
        # Use cache even if there is a manual white background fix match (if already processed)
        if status in ("approved", "auto-corrected", "skipped", "verification_failed"):
            print(f"[{idx+1}/{total_count}] Zoom SKU: {sku} File: {f} - Already {status.upper()}. Restoring (Cached)...")
            if status == "skipped":
                img_path = os.path.join(zoom_dir, f)
                if os.path.exists(img_path):
                    try: os.remove(img_path)
                    except Exception: pass
                return "skipped"
            if status in ("approved", "auto-corrected", "verification_failed"):
                entry = status_db.get(db_key, {})
                original_bbox = entry.get("original_bbox")
                is_detail = (entry.get("image_type") == "detail_shot") or ("closeup" in entry.get("reason", "").lower()) or ("detail" in entry.get("reason", "").lower())
                
                # Check if we should copy directly from SRC_DIR (already approved, no raw original_bbox, or detail shot)
                copy_from_src = (status in ("approved", "verification_failed")) or (not original_bbox) or is_detail
                
                if copy_from_src:
                    src_zoom_rel = f"artiklar/zoom/{f}"
                    src_zoom_path = find_case_insensitive(SRC_DIR, src_zoom_rel)
                    if src_zoom_path and os.path.exists(src_zoom_path):
                        shutil.copy2(src_zoom_path, img_path)
                    elif os.path.exists(input_img_path):
                        shutil.copy2(input_img_path, img_path)
                        ensure_square_canvas(img_path, get_target_size(img_path), category=category)
                else:
                    # status == "auto-corrected" and original_bbox is present: local correction from raw
                    if not os.path.exists(img_path) and os.path.exists(input_img_path):
                        shutil.copy2(input_img_path, img_path)
                        try:
                            with Image.open(img_path) as img_temp:
                                _, bg_color = is_white_background_robust(img_temp)
                                if not bg_color:
                                    bg_color = (255, 255, 255)
                            process_and_correct(img_path, img_path, original_bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
                        except Exception as e:
                            print(f"      [Cache Warning] Local correction failed, fallback to canvas padding: {e}")
                            ensure_square_canvas(img_path, get_target_size(img_path), category=category)
            return status
            
    if os.path.exists(input_img_path):
        shutil.copy2(input_img_path, img_path)
    
    try:
        with Image.open(img_path) as img:
            is_wb, bg_color = is_white_background_robust(img)
            W, H = img.size
    except Exception as e:
        print(f"    ✗ Failed to open or read image file {img_path}: {e}")
        status_db[db_key] = {
            "status": "file_error",
            "reason": f"Failed to open image file: {e}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        sys.exit(f"CRITICAL_FAILURE: Image open failed for {db_key} - {e}")
        
    if not is_wb:
        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass
        status_db[db_key] = {
            "status": "skipped",
            "reason": "Lifestyle image (no white background)",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        return "skipped"
    target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS[category]
    target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
    category_info = (category, target_w, target_h, floor_pct, is_centered)
    
    query_img_path = src_image if (src_image and os.path.exists(src_image)) else img_path
    print(f"[{idx+1}/{total_count}] Zoom SKU: {sku} File: {f} | Cat: {category}")
    print(f"    Querying Gemini Vision API for bounding box on {os.path.basename(query_img_path)}...")
    bbox, image_type = call_gemini_vision(query_img_path, category, prod_name)

    if image_type == "lifestyle_shot":
        print(f"    [Lifestyle Detected] Gemini classified zoom image as lifestyle_shot. Skipping.")
        img_path = os.path.join(zoom_dir, f)
        if os.path.exists(img_path):
            try: os.remove(img_path)
            except Exception: pass
        status_db[db_key] = {
            "status": "skipped",
            "reason": "Lifestyle image (Gemini classified)",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        return "skipped"

    if not bbox:
        print(f"    ✗ Failed to get bounding box from Gemini API for {db_key}.")
        status_db[db_key] = {
            "status": "api_failed",
            "reason": "Failed to get bounding box from Gemini API",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        sys.exit(f"CRITICAL_FAILURE: Bounding box API call failed for {db_key}")

    if image_type == "detail_shot":
        reason_text = "Detail close-up (cropped to square full-bleed)"
        print(f"    ✓ Approved. {reason_text}")
        status_db[db_key] = {
            "status": "approved",
            "category": category,
            "bbox": bbox,
            "image_type": image_type,
            "target_w": target_w,
            "target_h": target_h,
            "reason": reason_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        if src_image and os.path.exists(src_image):
            print(f"    [Source Match] Copying raw original image to zoom before cropping: {src_image}")
            shutil.copy2(src_image, img_path)
        make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
        return "approved"
        
    # Trim bbox to actual product pixels to eliminate loose margins
    try:
        with Image.open(img_path) as img_check:
            bbox = trim_bbox_to_pixels(img_check, bbox)
    except Exception:
        pass
        
    ymin, xmin, ymax, xmax = bbox
    w_curr = xmax - xmin
    h_curr = ymax - ymin
    cx_curr = (xmin + xmax) / 2
    cy_curr = (ymin + ymax) / 2
    
    # Dynamic adjustment for round/square tables based on bounding box aspect ratio and product name
    aspect_ratio = (w_curr * W) / (h_curr * H) if h_curr > 0 else 1.0
    m_cross = re.search(r'(\d+)\s*x\s*(\d+)', prod_name.lower())
    is_square = False
    if m_cross:
        is_square = (m_cross.group(1) == m_cross.group(2))
    is_round_or_oval = any(x in prod_name.lower() for x in ["runt", "rund", "ovalt", "oval", "ø", "diam"]) or is_square or (aspect_ratio < 1.35)
    is_round_table_override = False
    if category == "table_coffee" and is_round_or_oval and aspect_ratio < 1.3:
        is_rect = any(x in prod_name.lower() for x in ["skrivbord", "avlastningsbord", "120x", "140x", "160x", "180x", "200x"])
        if not is_rect:
            target_w = 0.68
            target_h = 0.68
            category_info = (category, target_w, target_h, floor_pct, is_centered)
            is_round_table_override = True
    elif category == "table_dining" and is_round_or_oval and aspect_ratio < 1.3:
        is_rect = any(x in prod_name.lower() for x in ["140x", "160x", "180x", "200x", "220x"])
        if not is_rect:
            target_w = 0.78
            target_h = 0.78
            category_info = (category, target_w, target_h, floor_pct, is_centered)
            is_round_table_override = True
            
    # If the table or desk is rectangular but photographed from the short end (square-ish bounding box)
    # we increase target_h to prevent it from being scaled down to a tiny width.
    if not is_round_table_override:
        if category == "table_dining" and aspect_ratio < 1.4:
            target_h = 0.78
            category_info = (category, target_w, target_h, floor_pct, is_centered)
        elif category == "table_coffee" and aspect_ratio < 1.4:
            target_h = 0.72
            category_info = (category, target_w, target_h, floor_pct, is_centered)
        elif category == "desk" and aspect_ratio < 1.4:
            target_h = 0.75
            category_info = (category, target_w, target_h, floor_pct, is_centered)
            
    # Adjust target dimensions for square-ish chests of drawers, cabinets, and bookshelves
    if category in ["chest_of_drawers", "cabinet_large", "bookshelf_floor"] and 0.80 <= aspect_ratio <= 1.25:
        target_h = 0.70
        target_w = 0.70
        category_info = (category, target_w, target_h, floor_pct, is_centered)
        print(f"    [Size Adjustment] Square-ish furniture detected (aspect_ratio={aspect_ratio:.2f}). Adjusting target size to 0.70.")

    scale_needed = calculate_scale(category, w_curr, h_curr, target_w, target_h, floor_pct, is_centered)
    cx_dev = abs(cx_curr - 0.50)
    
    if not is_centered:
        target_bottom = 1.0 - floor_pct
        bottom_dev = abs(ymax - target_bottom)
    else:
        bottom_dev = abs(cy_curr - 0.50)
        
    tolerance = 0.05
    is_ok = (0.95 <= scale_needed <= 1.05) and (cx_dev <= tolerance) and (bottom_dev <= tolerance)
    if has_fix_match:
        print(f"    [Fix Match Force] Zoom SKU has a manual white background fix match. Forcing auto-correction flow...")
        is_ok = False
    
    # Rule-based is_closeup override disabled for zoom images to prevent false positives on tight crops.
    is_closeup = False
        
    is_tabletop_only = False
    
    if force_correction:
        print(f"    [Force Option] Bypassing normal checks to force auto-correction flow...")
        is_ok = False
        is_closeup = False
        is_tabletop_only = False
            
    if is_ok or is_closeup or is_tabletop_only:
        if is_tabletop_only:
            reason_text = "Approved (Tabletop-only detection due to white-on-white, preserved as-is)"
        else:
            reason_text = "Approved (Within tolerance)" if not is_closeup else "Detail close-up image (preserved as-is)"
        print(f"    ✓ Approved. {reason_text}")
        status_db[db_key] = {
            "status": "approved",
            "category": category,
            "bbox": bbox,
            "target_w": target_w,
            "target_h": target_h,
            "reason": reason_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
            json.dump(status_db, sf, indent=2)
        ensure_square_canvas(img_path, get_target_size(img_path), category=category)
        return "approved"
    else:
        print(f"    ✗ Fails alignment. Width={w_curr:.2f} (target {target_w:.2f}), Bottom={ymax:.2f} (target {1.0-floor_pct if not is_centered else 0.50:.2f}). Autocorrecting...")
        
        backup_path = os.path.join(BACKUP_DIR, f)
        shutil.copy2(img_path, backup_path)
        
        correction_meta = process_and_correct(img_path, img_path, bbox, category_info, bg_color, sku=sku, prod_name=prod_name)
        
        # Verify corrected zoom image
        w_expected = correction_meta["new_width_pct"]
        h_expected = correction_meta["new_height_pct"]
        ymin_new, xmin_new, ymax_new, xmax_new = correction_meta["new_bbox"]
        y_expected_center = (ymin_new + ymax_new) / 2.0
            
        print("    Querying Gemini Vision API for verification...")
        verified, reason = call_gemini_verification(
            img_path, category, w_expected, h_expected, y_expected_center, is_centered,
            is_round_table=is_round_table_override, scaled_by=correction_meta.get("scaled_by"), prod_name=prod_name
        )
        
        if not verified:
            if has_fix_match:
                print(f"    ✓ Verification failed but this is a manual white background fix folder image. Overriding verification failure to approve.")
                status_db[db_key] = {
                    "status": "auto-corrected",
                    "category": category,
                    "bbox": bbox,
                    "image_type": image_type,
                    "target_w": target_w,
                    "target_h": target_h,
                    "reason": f"Auto-corrected (Fix folder override of verification fail: {reason})",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                return "auto-corrected"
            # Check if the failure reason indicates it's a detail shot or close-up
            reason_lower = reason.lower()
            is_detail_reason = any(x in reason_lower for x in [
                "detail shot", "detail view", "close-up", "closeup", 
                "fabric texture", "material texture", "zoom view", "zoomed view",
                "not a full product", "not the full product", 
                "only shows a part", "only shows a portion", "close up",
                "overhead view", "top-down view", "top down view",
                "cut off", "cut-off", "not centered", "not horizontally centered",
                "shifted", "margin", "imbalance", "floating", "occupies too much",
                "too small", "width", "height", "underside", "upside down",
                "legs pointing", "standalone product", "single standalone",
                "nesting", "set of"
            ])
            is_lifestyle_reason = any(x in reason_lower for x in [
                "room setting", "room environment", "lifestyle image", "lifestyle setting",
                "textured wall", "textured floor", "textured rug", "grey wall", "concrete wall",
                "concrete floor", "curtain", "curtains", "decorations", "decorative items",
                "not a clean, uniform", "not a clean white", "uneven background", "uneven areas on the floor",
                "rectangular background", "rectangular border", "crop box", "background seam", "background seams"
            ])
            
            if is_detail_reason:
                print(f"    ✓ Verification failed but identified as a detail/close-up view. Approving as-is.")
                shutil.copy2(backup_path, img_path)
                status_db[db_key] = {
                    "status": "approved",
                    "category": category,
                    "bbox": bbox,
                    "image_type": "detail_shot",
                    "reason": f"Approved as close-up/detail shot: {reason}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
                return "approved"
            elif is_lifestyle_reason:
                print(f"    ✓ Verification failed but identified as lifestyle/room setting. Skipping.")
                shutil.copy2(backup_path, img_path)
                status_db[db_key] = {
                    "status": "skipped",
                    "category": category,
                    "reason": f"Skipped based on QA background review: {reason}",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                return "skipped"
            else:
                print(f"    ✗ Verification failed: {reason}. Reverting to original.")
                shutil.copy2(backup_path, img_path)
                status_db[db_key] = {
                    "status": "verification_failed",
                    "category": category,
                    "reason": reason,
                    "original_bbox": bbox,
                    "image_type": image_type,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                # Save status_db
                with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                    json.dump(status_db, sf, indent=2)
                if image_type == "detail_shot":
                    make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
                else:
                    ensure_square_canvas(img_path, get_target_size(img_path), category=category)
                return "verification_failed"
        else:
            print(f"    ✓ Verification success: Corrected image approved!")
            status_db[db_key] = {
                "status": "auto-corrected",
                "category": category,
                "original_bbox": bbox,
                "image_type": image_type,
                "target_w": target_w,
                "target_h": target_h,
                "correction_metadata": correction_meta,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(STATUS_FILE, 'w', encoding='utf-8') as sf:
                json.dump(status_db, sf, indent=2)
            if image_type == "detail_shot":
                make_square_by_cropping(img_path, get_target_size(img_path), bbox=bbox)
            else:
                ensure_square_canvas(img_path, get_target_size(img_path), category=category)
            return "auto-corrected"

def precalculate_sku_scales(sku_list, sku_to_prod, status_db):
    sku_common_scales = {}
    sku_common_cys = {}
    
    input_artiklar_dir = os.path.join(INPUT_DIR, "artiklar")
    input_zoom_dir = os.path.join(input_artiklar_dir, "zoom")
    
    all_main_files = []
    if os.path.exists(input_artiklar_dir):
        all_main_files = [f for f in os.listdir(input_artiklar_dir) if f.lower().endswith('.jpg')]
        
    all_zoom_files = []
    if os.path.exists(input_zoom_dir):
        all_zoom_files = [f for f in os.listdir(input_zoom_dir) if f.lower().endswith('.jpg')]
        
    # Group the input SKU list by base SKU
    base_skus = set(get_base_sku(sku) for sku in sku_list)
    
    for base_sku in base_skus:
        prod_name = None
        category = None
        for sku_lower, (slug, name) in sku_to_prod.items():
            if get_base_sku(sku_lower) == base_sku:
                prod_name = name
                category = classify_and_size_product(name)
                break
                
        if not category:
            continue
            
        target_w, target_h, floor_pct, is_centered = CATEGORY_TARGETS.get(category, (0.87, 0.87, 0.50, True))
        target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
        
        sku_files = []
        for f in all_main_files:
            f_sku = f[:-4].lower()
            if get_base_sku(f_sku) == base_sku:
                sku_files.append(("artiklar", f))
                
        for f in all_zoom_files:
            m = re.match(r"^(.+?)_\d+\.jpg$", f, re.IGNORECASE)
            if m:
                f_sku = m.group(1).lower()
                if get_base_sku(f_sku) == base_sku:
                    sku_files.append(("zoom", f))
                    
        scales = []
        cys = []
        for img_type, fn in sku_files:
            db_key = f"{img_type}/{fn}"
            entry = status_db.get(db_key.lower(), {})
            status = entry.get("status")
            reason = entry.get("reason", "").lower()
            img_type_db = entry.get("image_type", "")
            
            is_lifestyle = "lifestyle" in reason or "room setting" in reason or "room environment" in reason or (status == "skipped" and not entry.get("original_bbox"))
            is_detail = img_type_db == "detail_shot" or "closeup" in reason or "detail" in reason
            
            if is_lifestyle or is_detail:
                continue
                
            bbox = entry.get("original_bbox")
            if not bbox:
                continue
                
            img_path = os.path.join(INPUT_DIR, img_type, fn)
            if not os.path.exists(img_path) and img_type == "zoom":
                img_path = os.path.join(input_zoom_dir, fn)
            
            if not os.path.exists(img_path):
                continue
                
            try:
                with Image.open(img_path) as img:
                    W, H = img.size
                    
                    ymin_gem = int(bbox[0] * H)
                    xmin_gem = int(bbox[1] * W)
                    ymax_gem = int(bbox[2] * H)
                    xmax_gem = int(bbox[3] * W)
                    
                    is_wb, sampled_bg = is_white_background_robust(img)
                    bg_val = sum(sampled_bg) / 3.0 if sampled_bg else 255.0
                    
                    # Determine pixel-based boundaries for refinement
                    gray_np = np.array(img.convert('L'))
                    threshold = 251.0 if bg_val > 250.0 else (bg_val - 8.0)
                    non_white = (gray_np < threshold)
                    
                    # Search area margins
                    if not is_centered:
                        margin_w = max(100, int(W * 0.30))
                        margin_h = max(50, int(H * 0.15))
                        search_ymax = min(H, ymax_gem + max(100, int(H * 0.25)))
                    else:
                        margin_w = max(50, int(W * 0.12))
                        margin_h = max(50, int(H * 0.12))
                        search_ymax = min(H, ymax_gem + margin_h)
                        
                    search_ymin = max(0, ymin_gem - margin_h)
                    search_xmin = max(0, xmin_gem - margin_w)
                    search_xmax = min(W, xmax_gem + margin_w)
                    
                    search_mask = np.zeros_like(non_white, dtype=bool)
                    search_mask[search_ymin:search_ymax, search_xmin:search_xmax] = True
                    non_white_constrained = non_white & search_mask
                    
                    coords = np.argwhere(non_white_constrained)
                    if coords.size > 0:
                        ymin_px = int(coords[:, 0].min())
                        ymax_px = int(coords[:, 0].max())
                        xmin_px = int(coords[:, 1].min())
                        xmax_px = int(coords[:, 1].max())
                    else:
                        ymin_px, ymax_px, xmin_px, xmax_px = ymin_gem, ymax_gem, xmin_gem, xmax_gem
                        
                    is_fix_image = "white background fix" in img_path.lower()
                    if is_centered or is_fix_image:
                        ymin_gem = min(ymin_gem, ymin_px)
                        ymax_gem = max(ymax_gem, ymax_px)
                        xmin_gem = min(xmin_gem, xmin_px)
                        xmax_gem = max(xmax_gem, xmax_px)
                    else:
                        ymin_gem = min(ymin_gem, ymin_px)
                        col_min = max(0, xmin_gem)
                        col_max = min(W, xmax_gem)
                        search_bottom = min(H, ymax_gem + int(H * 0.25))
                        leg_threshold = max(160, int(bg_val - 12)) if bg_val > 240.0 else 160
                        dark_pixels = (gray_np[ymax_gem:search_bottom, col_min:col_max] < leg_threshold)
                        if np.any(dark_pixels):
                            relative_y = np.argwhere(dark_pixels)[:, 0].max()
                            ymax_gem = ymax_gem + relative_y
                            
                    body_w = max(1, xmax_gem - xmin_gem)
                    body_h = max(1, ymax_gem - ymin_gem)
                    
                    body_ratio = body_w / body_h if body_h > 0 else 1.0
                    narrow_categories = ["chair_dining", "armchair", "barstool", "stool"]
                    if category in narrow_categories and body_ratio > 1.20:
                        continue
                        
                    target_size = 1000
                    wide_categories = ["sofa_2_seat", "sofa_3_seat", "bench_hallway", "table_dining", "table_coffee", "desk", "sideboard_credenza", "shelf_hanging"]
                    if category in wide_categories:
                        scale = (target_size * target_w) / body_w
                    else:
                        scale = (target_size * target_h) / body_h
                        if body_w * scale > target_size * target_w:
                            scale = (target_size * target_w) / body_w
                            
                    scale = min(scale, (target_size * (1.0 - 2*0.04)) / body_w)
                    scales.append(scale)
                    
                    if is_centered:
                        cy_prod = (ymin_gem + ymax_gem) / 2.0
                        cys.append(cy_prod)
            except Exception:
                pass
                
        if scales:
            median_scale = float(np.median(scales))
            sku_common_scales[base_sku] = median_scale
            print(f"    [Scale Alignment] Precalculated common scale for base SKU {base_sku} ({prod_name}): {median_scale:.4f} based on {len(scales)} images.")
            
        if cys:
            median_cy = float(np.median(cys))
            sku_common_cys[base_sku] = median_cy
            print(f"    [Height Alignment] Precalculated common vertical center (cy_prod) for base SKU {base_sku}: {median_cy:.1f} based on {len(cys)} images.")
            
    return sku_common_scales, sku_common_cys

def main():
    print("==================================================")
    print("      VISION-BASED QUALITY REVIEW & CORRECTION     ")
    print("==================================================")
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    if not os.path.exists(BRAND_DICT_PATH):
        print(f"[ERROR] Brand SKU dict not found at {BRAND_DICT_PATH}")
        return
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
    print(f"Loaded {len(brand_sku_dict)} products from brand_sku_dict.")
    
    sku_to_prod = {}
    for slug, info in brand_sku_dict.items():
        sku = info.get("sku", "").strip().lower()
        if sku:
            sku_to_prod[sku] = (slug, info.get("name", slug))
            
    status_db = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                status_db = {k.lower(): v for k, v in json.load(f).items()}
            print(f"Loaded {len(status_db)} entries from existing review_status.json.")
        except Exception as e:
            print(f"Could not load review_status.json: {e}. Starting fresh.")
            
    global GLOBAL_STATUS_DB
    GLOBAL_STATUS_DB = status_db
            
    input_artiklar_dir = os.path.join(INPUT_DIR, "artiklar")
    input_zoom_dir = os.path.join(input_artiklar_dir, "zoom")
    
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    os.makedirs(artiklar_dir, exist_ok=True)
    os.makedirs(liten_dir, exist_ok=True)
    os.makedirs(zoom_dir, exist_ok=True)
    
    if not os.path.exists(input_artiklar_dir):
        print(f"[ERROR] Input Artiklar directory not found at {input_artiklar_dir}")
        return
        
    main_files = [f for f in os.listdir(input_artiklar_dir) if f.lower().endswith('.jpg') and os.path.isfile(os.path.join(input_artiklar_dir, f))]
    print(f"Found {len(main_files)} main images in input /artiklar/.")
    
    # Parse command line arguments
    limit = None
    batch_size = None
    skus_filter = None
    force_correction = "--force" in sys.argv
    for arg in sys.argv:
        if arg.startswith("--limit="):
            try:
                limit = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg.startswith("--batch-size="):
            try:
                batch_size = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg.startswith("--skus="):
            skus_filter = [s.strip().lower() for s in arg.split("=")[1].split(",")]

    # Get all unreviewed main files
    unreviewed_main = []
    for f in main_files:
        db_key = f"artiklar/{f}"
        dest_file = os.path.join(artiklar_dir, f)
        is_bad_crop = f.lower() in BAD_CROPS
        if force_correction or is_bad_crop:
            unreviewed_main.append(f)
        elif not os.path.exists(dest_file):
            unreviewed_main.append(f)
        elif db_key not in status_db:
            unreviewed_main.append(f)
        else:
            status = status_db[db_key].get("status")
            if status not in ("approved", "auto-corrected", "skipped"):
                unreviewed_main.append(f)

    if skus_filter is not None:
        unreviewed_main = [f for f in unreviewed_main if f[:-4].lower() in skus_filter]
        print(f"Filtered to {len(unreviewed_main)} SKUs matching filter: {skus_filter}")

    max_to_process = batch_size if batch_size is not None else limit
    if max_to_process is not None:
        main_files = unreviewed_main[:max_to_process]
        print(f"Limiting execution to first {max_to_process} unreviewed main images.")
        zoom_files = []
    else:
        main_files = unreviewed_main
        # Get all unreviewed zoom files
        unreviewed_zoom = []
        if os.path.exists(input_zoom_dir):
            all_zoom_files = [f for f in os.listdir(input_zoom_dir) if f.lower().endswith('.jpg') and os.path.isfile(os.path.join(input_zoom_dir, f))]
            for f in all_zoom_files:
                db_key = f"zoom/{f}"
                dest_file = os.path.join(zoom_dir, f)
                if skus_filter is not None:
                    m = re.match(r"^(.+?)_\d+\.jpg$", f)
                    if not m or m.group(1).lower() not in skus_filter:
                        continue
                m = re.match(r"^(.+?)_\d+\.jpg$", f)
                sku = m.group(1) if m else None
                is_bad_crop = (f.lower() in BAD_CROPS) or (sku and f"{sku}.jpg".lower() in BAD_CROPS)
                if force_correction or is_bad_crop:
                    unreviewed_zoom.append(f)
                elif not os.path.exists(dest_file):
                    unreviewed_zoom.append(f)
                elif db_key not in status_db:
                    unreviewed_zoom.append(f)
                else:
                    status = status_db[db_key].get("status")
                    if status not in ("approved", "auto-corrected", "skipped"):
                        unreviewed_zoom.append(f)
        zoom_files = unreviewed_zoom
        print(f"Processing all {len(main_files)} main images and {len(zoom_files)} zoom images.")

    # Precalculate common scales and vertical centers for all SKUs we are about to process
    skus_to_calc = set()
    for f in main_files:
        skus_to_calc.add(f[:-4].lower())
    for f in zoom_files:
        m = re.match(r"^(.+?)_\d+\.jpg$", f)
        if m:
            skus_to_calc.add(m.group(1).lower())
            
    if skus_to_calc:
        print(f"\n--- PRE-CALCULATING COMMON SCALES/HEIGHTS FOR {len(skus_to_calc)} SKUS ---")
        common_scales, common_cys = precalculate_sku_scales(list(skus_to_calc), sku_to_prod, status_db)
        SKU_COMMON_SCALES.update(common_scales)
        SKU_COMMON_CYS.update(common_cys)
        print(f"Loaded {len(SKU_COMMON_SCALES)} common scales and {len(SKU_COMMON_CYS)} common centers globally.\n")

    approved_count = 0
    corrected_count = 0
    skipped_count = 0
    failures = []
    
    print("\n--- PHASE 1: Reviewing Main Images ---")
    for idx, f in enumerate(main_files):
        res = process_single_main_image(f, idx, len(main_files), sku_to_prod, status_db, artiklar_dir, liten_dir, zoom_dir, force_correction=force_correction)
        if res == "approved":
            approved_count += 1
        elif res == "auto-corrected":
            corrected_count += 1
        elif res == "skipped":
            skipped_count += 1
        elif res == "verification_failed":
            failures.append(f"artiklar/{f}")
            
    print("\n--- PHASE 2: Reviewing Secondary Zoom Images ---")
    for idx, f in enumerate(zoom_files):
        res = process_single_zoom_image(f, idx, len(zoom_files), sku_to_prod, status_db, zoom_dir, force_correction=force_correction)
        if res == "approved":
            approved_count += 1
        elif res == "auto-corrected":
            corrected_count += 1
        elif res == "skipped":
            skipped_count += 1
        elif res == "verification_failed":
            failures.append(f"zoom/{f}")

    print("\n==================================================")
    print("           VISION REVIEW COMPLETE!                ")
    print("==================================================")
    print(f"✓ Approved as-is: {approved_count}")
    print(f"🛠 Automatically corrected: {corrected_count}")
    print(f"ℹ Skipped (lifestyle): {skipped_count}")
    print(f"✗ Verification failures: {len(failures)}")
    print("==================================================")

    failures_file = os.path.join(REFORMA_DIR, "verification_failures.json")
    if failures:
        with open(failures_file, 'w', encoding='utf-8') as f_out:
            json.dump(failures, f_out, indent=2)
        print(f"\n[INFO] Wrote {len(failures)} verification failures to {failures_file}")
        sys.exit(2)
    else:
        if os.path.exists(failures_file):
            try:
                os.remove(failures_file)
            except Exception:
                pass
        sys.exit(0)

if __name__ == "__main__":
    main()
