import os
import sys
import re
import json
import numpy as np
import torch
import shutil
from PIL import Image

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from ultralytics.models.sam import SAM3SemanticPredictor
    print("SAM3SemanticPredictor imported successfully.")
except Exception as e:
    print("Error importing SAM3SemanticPredictor:", e)
    exit(1)

# Check GPU
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device Name:", torch.cuda.get_device_name(0))
else:
    print("GPU NOT AVAILABLE! SAM 3 must run on CUDA GPU.")
    exit(1)

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full")
BRAND_DICT_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\brand_sku_dict.json"

# Fallback for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

def normalize_name(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def is_white_background_robust(img):
    try:
        img_rgb = img.convert('RGB')
        arr = np.array(img_rgb)
        h, w, _ = arr.shape
        patches = [
            arr[10:25, 10:25],
            arr[10:25, -25:-10],
            arr[-25:-10, 10:25],
            arr[-25:-10, -25:-10]
        ]
        means = [np.mean(pat, axis=(0,1)) for pat in patches]
        means.sort(key=lambda c: np.sum(c))
        
        bg_color = np.mean(means[1:], axis=0)
        bg_mean = np.mean(bg_color)
        
        grays = [0.299*m[0] + 0.587*m[1] + 0.114*m[2] for m in means[1:]]
        std_dev = np.std(grays)
        
        is_studio = (bg_mean > 210) and (std_dev < 15.0)
        return is_studio, bg_color
    except Exception:
        return False, None

def is_white_background(img):
    is_wb, _ = is_white_background_robust(img)
    return is_wb

def resize_max_dim(img, max_dim):
    w, h = img.size
    longest = max(w, h)
    if longest > max_dim:
        scale = float(max_dim) / longest
        new_w = int(w * scale)
        new_h = int(h * scale)
        return img.resize((new_w, new_h), RESAMPLING_METHOD)
    return img

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

def classify_and_size_product(folder_name):
    folder_lower = folder_name.lower()
    
    # SOFA
    is_sofa = False
    if "soffa" in folder_lower or "sofa" in folder_lower or "baddsoffa" in folder_lower or "bäddsoffa" in folder_lower or "schaslong" in folder_lower:
        is_sofa = True
        
    if is_sofa:
        is_2_seat = any(x in folder_lower for x in ["2-sits", "2-seater", "2sits", "2seater", "loveseat", "love-seat", "baddfatolj", "bäddfåtölj"])
        if is_2_seat:
            return "sofa_2_seat", 0.92, 0.42, 0.1309, False
        else:
            return "sofa_3_seat", 0.94, 0.42, 0.1309, False

    # CHAIRS, ARMCHAIRS, BARSTOOLS, STOOLS
    is_chair = any(x in folder_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"])
    if is_chair:
        if any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol"]):
            return "armchair", 0.92, 0.75, 0.10, False
        elif "barstol" in folder_lower:
            return "barstool", 0.75, 0.86, 0.10, False
        elif any(x in folder_lower for x in ["pall", "puff", "sittpuff"]):
            return "stool", 0.48, 0.52, 0.10, False
        else:
            return "chair_dining", 0.90, 0.78, 0.10, False

    # TABLES
    is_table = any(x in folder_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord"])
    if is_table:
        is_dining = any(x in folder_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"])
        if is_dining:
            return "table_large", 0.92, 0.52, 0.113, False
        else:
            return "table_small", 0.83, 0.60, 0.113, False

    # CABINETS
    is_cabinet = any(x in folder_lower for x in ["skap", "skåp", "byra", "byrå", "sideboard", "skank", "skänk", "garderob", "tv-bank", "tv-bänk", "vinhylla"])
    if is_cabinet:
        is_large = any(x in folder_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ"]) or ("skap" in folder_lower or "skåp" in folder_lower) and not any(x in folder_lower for x in ["sido", "litet", "byra", "byrå"])
        if is_large:
            return "cabinet_large", 0.83, 0.92, 0.10, False
        else:
            return "cabinet_small", 0.92, 0.63, 0.10, False

    # SHELVES
    is_shelf = any(x in folder_lower for x in ["hylla", "hyllor", "vagghylla", "vägghylla", "vagghyllor", "vägghyllor"])
    if is_shelf:
        is_wall = any(x in folder_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"])
        if is_wall:
            return "shelf_hanging", 0.81, 0.40, 0.50, True
        else:
            return "shelf_floor", 0.86, 0.86, 0.10, False

    # LIGHTING
    is_lamp = any(x in folder_lower for x in ["lamp", "lampa", "belysning", "ljus", "stjarna", "stjärna", "advent"])
    if is_lamp:
        if "golv" in folder_lower:
            return "lamp_floor", 0.63, 0.90, 0.10, False
        elif "bord" in folder_lower:
            return "lamp_table", 0.38, 0.44, 0.50, True
        elif any(x in folder_lower for x in ["taklampa", "pendel", "krona", "plafond", "adventstjarna", "adventstjärna", "stjarna", "stjärna", "oslo", "sally", "lotus"]):
            return "lamp_pendant", 0.70, 0.58, 0.50, True
        elif "vagg" in folder_lower or "vägg" in folder_lower:
            return "lamp_wall", 0.58, 0.46, 0.50, True
        else:
            return "lamp_pendant", 0.70, 0.58, 0.50, True

    # DEFAULT
    return "default", 0.86, 0.90, 0.50, True

def adjust_size_by_name(category, name, target_w, target_h):
    name_lower = name.lower()
    name_clean = re.sub(r'(202[0-9]|26u)', '', name_lower)
    numbers = re.findall(r'\d+', name_clean)
    m_cross = re.search(r'(\d+)\s*x\s*(\d+)', name_clean)
    
    if category == "table_large":
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

def load_and_ensure_size(img):
    w, h = img.size
    max_dim = max(w, h)
    if max_dim < 2000:
        scale = 2000.0 / max_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), RESAMPLING_METHOD)
    return img

def get_sam3_text_prompt(category, prod_name):
    prompts = ["furniture"]
    prod_name_lower = prod_name.lower()
    
    if "soffa" in prod_name_lower or "sofa" in prod_name_lower or "schaslong" in prod_name_lower:
        prompts = ["sofa", "couch", "furniture"]
    elif "stol" in prod_name_lower or "chair" in prod_name_lower or "armchair" in prod_name_lower:
        prompts = ["chair", "armchair", "furniture"]
    elif "pall" in prod_name_lower or "puff" in prod_name_lower or "stool" in prod_name_lower:
        prompts = ["stool", "pouffe", "furniture"]
    elif "bord" in prod_name_lower or "table" in prod_name_lower or "desk" in prod_name_lower:
        prompts = ["table", "desk", "furniture"]
    elif "skåp" in prod_name_lower or "skap" in prod_name_lower or "byrå" in prod_name_lower or "byra" in prod_name_lower or "sideboard" in prod_name_lower or "skänk" in prod_name_lower or "tv-bänk" in prod_name_lower or "tv-bank" in prod_name_lower or "cabinet" in prod_name_lower:
        prompts = ["cabinet", "sideboard", "cupboard", "furniture"]
    elif "vinhylla" in prod_name_lower or "wine" in prod_name_lower:
        prompts = ["wine rack", "cabinet", "furniture"]
    elif "hylla" in prod_name_lower or "shelf" in prod_name_lower or "shelves" in prod_name_lower or "bookcase" in prod_name_lower:
        prompts = ["shelf", "bookcase", "shelves", "furniture"]
    elif "lampa" in prod_name_lower or "lamp" in prod_name_lower or "belysning" in prod_name_lower:
        prompts = ["lamp", "light fixture", "furniture"]
        
    return prompts

def process_image_sam3(predictor, img_path_or_pil, category, target_w_fill, target_h_fill, floor_pct, is_centered, text_prompts, slot=1):
    if isinstance(img_path_or_pil, Image.Image):
        img = img_path_or_pil
    else:
        img = Image.open(img_path_or_pil)
    img = load_and_ensure_size(img)
    w, h = img.size
    
    is_wb, bg_color = is_white_background_robust(img)
    cleaned_shadow = img
    
    if is_wb and bg_color is not None:
        cleaned_shadow = clean_offwhite_background(img, bg_color)
        
    bbox_clean = None
    
    try:
        with torch.no_grad():
            results = predictor(img, text=text_prompts)
        if len(results) > 0 and results[0].masks is not None:
            masks_tensor = results[0].masks.data
            combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy()
            
            combined_mask[:15, :] = False
            combined_mask[-15:, :] = False
            combined_mask[:, :15] = False
            combined_mask[:, -15:] = False
            
            coords_body = np.argwhere(combined_mask > 0)
            if coords_body.size > 0:
                y_min_clean = coords_body[:, 0].min()
                y_max_clean = coords_body[:, 0].max()
                x_min_clean = coords_body[:, 1].min()
                x_max_clean = coords_body[:, 1].max()
                bbox_clean = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
                print(f"  [SAM3] Detected Body BBox: x_min={x_min_clean}, y_min={y_min_clean}, x_max={x_max_clean}, y_max={y_max_clean}")
    except Exception as e:
        print(f"  [SAM3 Warning] SAM 3 body detection failed: {e}")
    finally:
        if 'masks_tensor' in locals():
            del masks_tensor
        if 'results' in locals():
            del results
        import gc
        gc.collect()
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
        
    if bbox_clean is None and is_wb and bg_color is not None:
        print("  [Fallback] Running pixel diffing body detection...")
        img_rgb = img.convert('RGB')
        arr = np.array(img_rgb)
        diff = np.sum(np.abs(arr - bg_color), axis=-1)
        mask_body = (diff < 25) & (arr[:,:,0] > 180) & (arr[:,:,1] > 180) & (arr[:,:,2] > 180)
        arr_body = arr.copy()
        arr_body[mask_body] = [255, 255, 255]
        
        arr_body[:15, :, :] = [255, 255, 255]
        arr_body[-15:, :, :] = [255, 255, 255]
        arr_body[:, :15, :] = [255, 255, 255]
        arr_body[:, -15:, :] = [255, 255, 255]
        
        product_pixels_body = np.any(arr_body < 254, axis=-1)
        coords_body = np.argwhere(product_pixels_body)
        if coords_body.size > 0:
            y_min_clean = coords_body[:, 0].min()
            y_max_clean = coords_body[:, 0].max()
            x_min_clean = coords_body[:, 1].min()
            x_max_clean = coords_body[:, 1].max()
            bbox_clean = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
            print(f"  [Fallback] Body BBox: x_min={x_min_clean}, y_min={y_min_clean}, x_max={x_max_clean}, y_max={y_max_clean}")

    if bbox_clean is not None:
        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox_clean
        
        # Check if the product body touches the top edge, or touches both left and right edges, or occupies almost the entire frame.
        # This is a signature of a close-up/detail shot.
        is_detail_shot = False
        margin_x = int(0.085 * w)
        margin_y = int(0.085 * h)
        if (y_min_clean <= margin_y) or \
           (x_min_clean <= margin_x) or \
           (x_max_clean >= w - margin_x) or \
           (x_max_clean - x_min_clean) >= 0.88 * w or \
           (y_max_clean - y_min_clean) >= 0.88 * h:
            is_detail_shot = True
            print(f"  [SAM3] Detected close-up/detail shot (bbox: {bbox_clean} vs w={w}, h={h}). Bypassing SAM3 cropping.")
            return None
        
        # Detect shadow by finding non-white pixels in cleaned_shadow
        arr = np.array(cleaned_shadow.convert('RGB'))
        non_white = np.any(arr < 254, axis=-1)
        # Avoid 5px border
        non_white[:5, :] = False
        non_white[-5:, :] = False
        non_white[:, :5] = False
        non_white[:, -5:] = False
        
        coords_shadow = np.argwhere(non_white)
        if coords_shadow.size > 0:
            y_min_raw = coords_shadow[:, 0].min()
            y_max_raw = coords_shadow[:, 0].max()
            x_min_raw = coords_shadow[:, 1].min()
            x_max_raw = coords_shadow[:, 1].max()
            print(f"  [Composition] Shadow BBox: x_min={x_min_raw}, y_min={y_min_raw}, x_max={x_max_raw}, y_max={y_max_raw}")
        else:
            y_min_raw, y_max_raw, x_min_raw, x_max_raw = y_min_clean, y_max_clean, x_min_clean, x_max_clean
            
        crop_x_min = max(0, x_min_raw - 10)
        crop_y_min = max(0, y_min_raw - 10)
        crop_x_max = min(w, x_max_raw + 10)
        crop_y_max = min(h, y_max_raw + 10)
        
        cropped = cleaned_shadow.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
        W_p = x_max_clean - x_min_clean
        H_p = y_max_clean - y_min_clean
        
        scale = min((target_w_fill * 2000.0) / W_p, (target_h_fill * 2000.0) / H_p)
        new_w_body = int(W_p * scale)
        new_h_body = int(H_p * scale)
        
        if not is_centered:
            max_h_allowed = int(2000 - (floor_pct * 2000) - 50)
            if new_h_body > max_h_allowed:
                scale = max_h_allowed / H_p
                new_w_body = int(W_p * scale)
                new_h_body = int(H_p * scale)
        else:
            if new_h_body > 1900:
                scale = 1900.0 / H_p
                new_w_body = int(W_p * scale)
                new_h_body = int(H_p * scale)
                
        new_w_crop = int((crop_x_max - crop_x_min) * scale)
        new_h_crop = int((crop_y_max - crop_y_min) * scale)
        cropped_resized = cropped.resize((new_w_crop, new_h_crop), RESAMPLING_METHOD)
        
        canvas = Image.new("RGB", (2000, 2000), (255, 255, 255))
        paste_x_body = (2000 - new_w_body) // 2
        
        if not is_centered:
            paste_y_body = int(2000 - (floor_pct * 2000) - new_h_body)
        else:
            paste_y_body = (2000 - new_h_body) // 2
            
        offset_x = x_min_clean - crop_x_min
        offset_y = y_min_clean - crop_y_min
        
        paste_x = paste_x_body - int(offset_x * scale)
        paste_y = paste_y_body - int(offset_y * scale)
        
        canvas.paste(cropped_resized, (paste_x, paste_y))
        return canvas
            
    # Fallback centered square crop
    w_curr, h_curr = img.size
    min_dim = min(w_curr, h_curr)
    left = (w_curr - min_dim) // 2
    top = (h_curr - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    cropped = img.crop((left, top, right, bottom))
    return cropped.resize((2000, 2000), RESAMPLING_METHOD)

def save_as_jpg(pil_img, dest_path, target_size, quality=90):
    img_copy = pil_img.copy()
    if img_copy.mode in ('RGBA', 'LA') or (img_copy.mode == 'P' and 'transparency' in img_copy.info):
        background = Image.new("RGB", img_copy.size, (255, 255, 255))
        background.paste(img_copy, mask=img_copy.split()[3] if img_copy.mode == 'RGBA' else None)
        img_copy = background
    else:
        img_copy = img_copy.convert("RGB")
        
    img_resized = resize_max_dim(img_copy, target_size)
    img_resized.save(dest_path, "JPEG", quality=quality)

def extract_slot_from_filename(filename):
    fn_lower = filename.lower()
    
    # If it contains wonder and is a double index, e.g. -01-1-wonder.jpeg, the slot is the second index
    m_double_wonder = re.search(r'-(\d+)-(\d+)-wonder', fn_lower)
    if m_double_wonder:
        return int(m_double_wonder.group(2))
        
    m_double_w_wonder = re.search(r'-(\d+)-(\d+)-w-wonder', fn_lower)
    if m_double_w_wonder:
        return int(m_double_w_wonder.group(2))
        
    # Standard slot patterns
    m_w_wonder = re.search(r'-(\d+)-w-wonder', fn_lower)
    if m_w_wonder:
        return int(m_w_wonder.group(1))
        
    m_wonder_w = re.search(r'-(\d+)-wonder-w', fn_lower)
    if m_wonder_w:
        return int(m_wonder_w.group(1))
        
    m_w = re.search(r'-(\d+)-w', fn_lower)
    if m_w:
        return int(m_w.group(1))
        
    # Fallbacks
    m_digit = re.search(r'[-_](\d+)\.[a-z]+$', fn_lower)
    if m_digit:
        return int(m_digit.group(1))
        
    return None

def is_processed_render(filename):
    fn_lower = filename.lower()
    
    # Exclude if it has a double index like -01-1-W.jpg and does NOT contain "wonder"
    has_double_index = re.search(r'-(\d+)-(\d+)-?w?', fn_lower) is not None
    has_wonder = 'wonder' in fn_lower
    
    if fn_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
        if has_wonder:
            return True
        if not has_double_index:
            if '-w-' in fn_lower or '-w.' in fn_lower or fn_lower.endswith(('-w.jpg', '-w.jpeg')):
                return True
    return False

def main():
    print("==================================================")
    print("   SAM 3 FULL CATALOG PIPELINE (ZARA STYLE)       ")
    print("==================================================")
    
    is_dry_run = "--dry-run" in sys.argv
    
    if not os.path.exists(BRAND_DICT_PATH):
        print(f"[ERROR] Brand dictionary not found: {BRAND_DICT_PATH}")
        return
        
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
        
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    if not is_dry_run:
        print(f"Ensuring staging directories exist: {FTP_UPLOAD_DIR}")
        for d in (artiklar_dir, liten_dir, zoom_dir):
            os.makedirs(d, exist_ok=True)
            for f in os.listdir(d):
                p_file = os.path.join(d, f)
                if os.path.isfile(p_file):
                    try:
                        os.remove(p_file)
                    except Exception:
                        pass
    else:
        print("\n*** RUNNING IN DRY-RUN MODE (first 10 items processed, no output files written) ***")
        
    # Initialize SAM 3 Predictor
    print("Initializing SAM 3 semantic predictor on CUDA...")
    try:
        overrides = dict(model="sam3.pt", conf=0.10, device="cuda")
        predictor = SAM3SemanticPredictor(overrides=overrides)
        print("SAM 3 Predictor successfully loaded on GPU.")
    except Exception as e:
        print(f"Error loading SAM 3 predictor: {e}")
        return

    # 1. Scan Refoma white background fix (1st priority)
    print("\nScanning Refoma white background fix directory...")
    wb_fix_folders = {}
    if os.path.exists(NEW_WHITE_BG_DIR):
        for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
            for d in dirs:
                dir_path = os.path.join(root, d)
                has_img = any(f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)))
                if has_img:
                    norm = normalize_name(d)
                    wb_fix_folders[norm] = dir_path
    print(f"  Found {len(wb_fix_folders)} folders in Refoma white background fix.")

    # 2. Scan TEST TOPAZ (2nd priority - fallback)
    print("\nScanning TEST TOPAZ directory...")
    topaz_files = {}
    if os.path.exists(TOPAZ_DIR):
        for f in os.listdir(TOPAZ_DIR):
            if f.lower().endswith('.webp'):
                m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
                if m:
                    prod_name = m.group(1)
                    slot = int(m.group(2))
                    norm = normalize_name(prod_name)
                    if norm not in topaz_files:
                        topaz_files[norm] = []
                    topaz_files[norm].append((slot, os.path.join(TOPAZ_DIR, f)))
    print(f"  Found {len(topaz_files)} products in TEST TOPAZ.")

    # 3. Scan reforma_original_images_by_product (3rd priority - final fallback)
    print("\nScanning reforma_original_images_by_product database...")
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
                    sku = sku_match.group(1).strip().lower()
                    orig_sku_folders[sku] = p
    print(f"  Found {len(orig_folders)} folders in reforma_original_images_by_product.")

    # Process products
    processed_count = 0
    skipped_count = 0
    
    products_to_process = list(brand_sku_dict.items())
    
    # Filter by SKU if provided
    limit_sku = None
    for arg in sys.argv:
        if arg.startswith("--sku="):
            limit_sku = arg.split("=")[1].strip()
            
    if limit_sku:
        products_to_process = [(name, info) for name, info in products_to_process if info['sku'].strip().lower() == limit_sku.lower()]
        print(f"Limiting processing to SKU: {limit_sku}. Found matches: {len(products_to_process)}")
    elif is_dry_run:
        products_to_process = products_to_process[:10]
        
    print(f"\nProcessing {len(products_to_process)} total catalog products...")
    
    for idx, (prod_name, info) in enumerate(products_to_process):
        sku = info['sku']
        sku_clean = sku.strip()
        
        # Exclude discontinued Lionel
        if sku_clean == "1100476" or "lionel" in prod_name.lower():
            print(f"[{idx+1}/{len(products_to_process)}] Skipping Lionel Chair (SKU: {sku_clean}) - Discontinued.")
            continue
            
        # Exclude rugs/carpets
        if any(x in prod_name.lower() for x in ["matta", "mattor", "rug", "carpet"]):
            print(f"[{idx+1}/{len(products_to_process)}] Skipping Rug (SKU: {sku_clean}) - '{prod_name}'.")
            continue
            
        print(f"\n[{idx+1}/{len(products_to_process)}] Mapping product: '{prod_name}' -> SKU: {sku_clean}")
        prod_norm = normalize_name(prod_name)
        
        processed_slots = {}
        
        # 1. Load Baseline Fallback (3rd priority)
        dir_path = None
        if prod_norm in orig_folders:
            dir_path = orig_folders[prod_norm]
        elif sku_clean.lower() in orig_sku_folders:
            dir_path = orig_sku_folders[sku_clean.lower()]
            
        used_orig = False
        if dir_path:
            for f in os.listdir(dir_path):
                p = os.path.join(dir_path, f)
                if os.path.isfile(p) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    processed_slots[1] = p
                    used_orig = True
            zoom_dir_path = os.path.join(dir_path, "zoom")
            if os.path.isdir(zoom_dir_path):
                for f in os.listdir(zoom_dir_path):
                    p = os.path.join(zoom_dir_path, f)
                    if os.path.isfile(p) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        slot = 2
                        slot_m = re.search(r'[-_](\d+)\.[a-zA-Z]+$', f)
                        if slot_m:
                            slot = int(slot_m.group(1))
                        processed_slots[slot] = p
                        used_orig = True
                        
        # 2. Overlay TEST TOPAZ (2nd priority)
        used_topaz = False
        if prod_norm in topaz_files:
            for slot, path in topaz_files[prod_norm]:
                processed_slots[slot] = path
                used_topaz = True
                
        # 3. Overlay Refoma white background fix (1st priority)
        found_wb_fix_dir = None
        if prod_norm in wb_fix_folders:
            found_wb_fix_dir = wb_fix_folders[prod_norm]
        else:
            for f_norm, d_path in wb_fix_folders.items():
                if prod_norm == f_norm or prod_norm in f_norm or f_norm in prod_norm:
                    found_wb_fix_dir = d_path
                    break
                    
        used_wb_fix = False
        if found_wb_fix_dir:
            files = [f for f in os.listdir(found_wb_fix_dir) if os.path.isfile(os.path.join(found_wb_fix_dir, f))]
            # Filter to processed JPG/JPEG renders first
            processed_renders = [f for f in files if is_processed_render(f)]
            slots_candidates = {}
            for f in processed_renders:
                slot = extract_slot_from_filename(f)
                if slot is not None:
                    if slot not in slots_candidates:
                        slots_candidates[slot] = []
                    slots_candidates[slot].append(f)
            
            for slot, candidates in slots_candidates.items():
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
                processed_slots[slot] = os.path.join(found_wb_fix_dir, best_cand)
                used_wb_fix = True
                
        # Determine source used description
        sources = []
        if used_wb_fix:
            sources.append("White Background Fix")
        if used_topaz:
            sources.append("TEST TOPAZ")
        if used_orig:
            sources.append("Baseline Fallback")
        source_used = " + ".join(sources) if sources else "None"

        if not processed_slots:
            print(f"  ❌ Skipped: Could not find any images in any source folder for '{prod_name}'")
            skipped_count += 1
            continue
            
        print(f"  Source: {source_used} | Slots found: {sorted(processed_slots.keys())}")
        
        # Sizing and classification
        category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
        target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
        print(f"  Category: {category} | Target W: {target_w:.3f} | Target H: {target_h:.3f} | Centered: {is_centered} | Floor: {floor_pct:.3f}")
        
        if category == "lamp_pendant":
            print("  Category is lamp_pendant. Bypassing cropping to preserve ceiling cables.")
            
        # Determine main image
        if 1 in processed_slots:
            main_slot_num = 1
            main_img_path = processed_slots[1]
        else:
            main_slot_num = min(processed_slots.keys())
            main_img_path = processed_slots[main_slot_num]
            
        text_prompts = get_sam3_text_prompt(category, prod_name)
        
        # Process main image
        main_img_raw = None
        main_img_resized = None
        main_canvas = None
        sec_img_raw = None
        sec_img_resized = None
        try:
            main_img_raw = Image.open(main_img_path)
            main_img_resized = load_and_ensure_size(main_img_raw)
            
            is_main_wb = is_white_background(main_img_resized)
            if category == "lamp_pendant":
                is_main_wb = False
                
            normal_dest = os.path.join(artiklar_dir, f"{sku_clean}.jpg")
            liten_dest = os.path.join(liten_dir, f"{sku_clean}_S.jpg")
            zoom_dest = os.path.join(zoom_dir, f"{sku_clean}_1.jpg")
            
            if not is_dry_run:
                if is_main_wb:
                    print("  Main image has white background. Processing with SAM 3 and preserving shadow.")
                    main_canvas = process_image_sam3(
                        predictor=predictor,
                        img_path_or_pil=main_img_resized,
                        category=category,
                        target_w_fill=target_w,
                        target_h_fill=target_h,
                        floor_pct=floor_pct,
                        is_centered=is_centered,
                        text_prompts=text_prompts,
                        slot=1
                    )
                    if main_canvas is None:
                        print("  [SAM3] Detail/close-up shot detected for main image. Saving uncropped.")
                        save_as_jpg(main_img_resized, normal_dest, 1000, quality=90)
                        save_as_jpg(main_img_resized, liten_dest, 400, quality=85)
                        save_as_jpg(main_img_resized, zoom_dest, 2000, quality=92)
                        print(f"  Saved main image for SKU: {sku_clean} - Uncropped (Detail shot)")
                    else:
                        save_as_jpg(main_canvas, normal_dest, 1000, quality=90)
                        save_as_jpg(main_canvas, liten_dest, 400, quality=85)
                        save_as_jpg(main_canvas, zoom_dest, 2000, quality=92)
                        print(f"  Saved main image for SKU: {sku_clean} - Cropped/Zara (Shadow preserved)")
                else:
                    print("  Main image is lifestyle/interior/cable-lamp. Saving uncropped.")
                    save_as_jpg(main_img_resized, normal_dest, 1000, quality=90)
                    save_as_jpg(main_img_resized, liten_dest, 400, quality=85)
                    save_as_jpg(main_img_resized, zoom_dest, 2000, quality=92)
                    print(f"  Saved main image for SKU: {sku_clean} - Uncropped")
            else:
                print(f"  [DRY-RUN] Main image processed successfully (WB={is_main_wb}).")
                
            # Process secondary slots
            for slot, path in sorted(processed_slots.items()):
                if slot == main_slot_num:
                    continue
                    
                print(f"  Processing secondary image: Slot {slot}")
                sec_img_raw = Image.open(path)
                sec_img_resized = load_and_ensure_size(sec_img_raw)
                
                is_sec_wb = is_white_background(sec_img_resized)
                if category == "lamp_pendant":
                    is_sec_wb = False
                    
                sec_zoom_dest = os.path.join(zoom_dir, f"{sku_clean}_{slot}.jpg")
                if not is_dry_run:
                    if is_sec_wb:
                        print(f"  Secondary image Slot {slot} has white background. Processing with SAM 3 and sizing to target fills.")
                        sec_canvas = process_image_sam3(
                            predictor=predictor,
                            img_path_or_pil=sec_img_resized,
                            category=category,
                            target_w_fill=target_w,
                            target_h_fill=target_h,
                            floor_pct=floor_pct,
                            is_centered=is_centered,
                            text_prompts=text_prompts,
                            slot=slot
                        )
                        if sec_canvas is None:
                            print(f"  [SAM3] Detail/close-up shot detected for secondary Slot {slot}. Saving uncropped.")
                            save_as_jpg(sec_img_resized, sec_zoom_dest, 2000, quality=92)
                        else:
                            save_as_jpg(sec_canvas, sec_zoom_dest, 2000, quality=92)
                            try:
                                sec_canvas.close()
                            except Exception:
                                pass
                    else:
                        print(f"  Secondary image Slot {slot} is lifestyle/interior. Saving uncropped.")
                        save_as_jpg(sec_img_resized, sec_zoom_dest, 2000, quality=92)
                else:
                    print(f"  [DRY-RUN] Secondary image Slot {slot} processed successfully (WB={is_sec_wb}).")
                    
                try:
                    sec_img_raw.close()
                except Exception:
                    pass
                try:
                    sec_img_resized.close()
                except Exception:
                    pass
                sec_img_raw = None
                sec_img_resized = None
                
            processed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error processing images for '{prod_name}': {e}")
            import traceback
            traceback.print_exc()
        finally:
            if main_img_raw is not None:
                try:
                    main_img_raw.close()
                except Exception:
                    pass
            if main_img_resized is not None:
                try:
                    main_img_resized.close()
                except Exception:
                    pass
            if main_canvas is not None:
                try:
                    main_canvas.close()
                except Exception:
                    pass
            if sec_img_raw is not None:
                try:
                    sec_img_raw.close()
                except Exception:
                    pass
            if sec_img_resized is not None:
                try:
                    sec_img_resized.close()
                except Exception:
                    pass
            
            main_img_raw = None
            main_img_resized = None
            main_canvas = None
            sec_img_raw = None
            sec_img_resized = None
            
            import gc
            gc.collect()
            if torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                    
    print("\n==================================================")
    print("         SAM 3 FULL CATALOG COMPLETED             ")
    print("==================================================")
    if not is_dry_run:
        print(f"Output folder: {FTP_UPLOAD_DIR}")
        print(f"  └─ /artiklar/       (1000x1000): {len(os.listdir(artiklar_dir))} files")
        print(f"  └─ /artiklar/liten/   (400x400): {len(os.listdir(liten_dir))} files")
        print(f"  └─ /artiklar/zoom/  (2000x2000): {len(os.listdir(zoom_dir))} files")
    print("--------------------------------------------------")
    print(f"✓ Processed {processed_count} products.")
    print(f"✗ Skipped {skipped_count} products (no images found).")
    print("==================================================")

if __name__ == "__main__":
    main()
