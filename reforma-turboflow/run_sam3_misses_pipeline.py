import os
import sys
import re
import json
import numpy as np
import torch
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
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "missed-products-upload")
JSON_PATH = os.path.join(ONEDRIVE_DIR, "turboflow", "missed_products.json")

# Fallback for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

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
        
        # bg_color is average of 3 brightest corners to avoid shadow/product intersection
        bg_color = np.mean(means[1:], axis=0)
        bg_mean = np.mean(bg_color)
        
        # Calculate standard deviation of top 3 corners to verify uniformity (studio shot backdrop)
        grays = [0.299*m[0] + 0.587*m[1] + 0.114*m[2] for m in means[1:]]
        std_dev = np.std(grays)
        
        # We classify as studio backdrop if mean > 210 and std_dev of corners is < 15.0
        is_studio = (bg_mean > 210) and (std_dev < 15.0)
        return is_studio, bg_color
    except Exception:
        return False, None

def is_white_background(img):
    is_wb, _ = is_white_background_robust(img)
    return is_wb

def crop_center_square(img):
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    return img.crop((left, top, right, bottom))

def pad_to_square(img):
    w, h = img.size
    max_dim = max(w, h)
    canvas = Image.new("RGB", (max_dim, max_dim), (255, 255, 255))
    paste_x = (max_dim - w) // 2
    paste_y = (max_dim - h) // 2
    canvas.paste(img, (paste_x, paste_y))
    return canvas

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
            return "sofa_2_seat", 0.84, 0.369, 0.1309, False
        else:
            return "sofa_3_seat", 0.90, 0.369, 0.1309, False

    # CHAIRS, ARMCHAIRS, BARSTOOLS, STOOLS
    is_chair = any(x in folder_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"])
    if is_chair:
        if any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol"]):
            return "armchair", 0.80, 0.65, 0.10, False
        elif "barstol" in folder_lower:
            return "barstool", 0.65, 0.75, 0.10, False
        elif any(x in folder_lower for x in ["pall", "puff", "sittpuff"]):
            return "stool", 0.42, 0.45, 0.10, False
        else:
            return "chair_dining", 0.78, 0.68, 0.10, False

    # TABLES
    is_table = any(x in folder_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord"])
    if is_table:
        is_dining = any(x in folder_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"])
        if is_dining:
            return "table_large", 0.88, 0.45, 0.113, False
        else:
            return "table_small", 0.72, 0.52, 0.113, False

    # CABINETS
    is_cabinet = any(x in folder_lower for x in ["skap", "skåp", "byra", "byrå", "sideboard", "skank", "skänk", "garderob", "tv-bank", "tv-bänk", "vinhylla"])
    if is_cabinet:
        is_large = any(x in folder_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ"]) or ("skap" in folder_lower or "skåp" in folder_lower) and not any(x in folder_lower for x in ["sido", "litet", "byra", "byrå"])
        if is_large:
            return "cabinet_large", 0.72, 0.85, 0.10, False
        else:
            return "cabinet_small", 0.80, 0.55, 0.10, False

    # SHELVES
    is_shelf = any(x in folder_lower for x in ["hylla", "hyllor", "vagghylla", "vägghylla", "vagghyllor", "vägghyllor"])
    if is_shelf:
        is_wall = any(x in folder_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"])
        if is_wall:
            return "shelf_hanging", 0.70, 0.35, 0.50, True
        else:
            return "shelf_floor", 0.75, 0.75, 0.10, False

    # LIGHTING
    is_lamp = any(x in folder_lower for x in ["lamp", "lampa", "belysning", "ljus", "stjarna", "stjärna", "advent"])
    if is_lamp:
        if "golv" in folder_lower:
            return "lamp_floor", 0.55, 0.78, 0.10, False
        elif "bord" in folder_lower:
            return "lamp_table", 0.40, 0.45, 0.50, True
        elif any(x in folder_lower for x in ["taklampa", "pendel", "krona", "plafond", "adventstjarna", "adventstjärna", "stjarna", "stjärna", "oslo", "sally", "lotus"]):
            return "lamp_pendant", 0.60, 0.50, 0.50, True
        elif "vagg" in folder_lower or "vägg" in folder_lower:
            return "lamp_wall", 0.50, 0.40, 0.50, True
        else:
            return "lamp_pendant", 0.60, 0.50, 0.50, True

    # DEFAULT
    return "default", 0.75, 0.78, 0.50, True

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
        target_w = max(0.65, min(0.92, target_w))
    elif category == "shelf_hanging":
        width = 75
        for num in map(int, numbers):
            if 15 <= num <= 150:
                width = num
                break
        scale = width / 75.0
        target_w = target_w * scale
        target_w = max(0.55, min(0.92, target_w))
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
        target_h = max(0.60, min(0.92, target_h))
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
        
    bbox = None
    coords_body = None
    
    # Try SAM 3 segmentation first
    try:
        with torch.no_grad():
            results = predictor(img, text=text_prompts)
        if len(results) > 0 and results[0].masks is not None:
            masks_tensor = results[0].masks.data
            combined_mask = torch.any(masks_tensor, dim=0).cpu().numpy()
            
            # Exclude 15px border to avoid Topaz upscaling artifacts/borders
            combined_mask[:15, :] = False
            combined_mask[-15:, :] = False
            combined_mask[:, :15] = False
            combined_mask[:, -15:] = False
            
            # Clean off-white background outside the product mask
            img_arr = np.array(cleaned_shadow.convert('RGB'))
            bg_pixels = (~combined_mask) & (np.min(img_arr, axis=-1) > 215)
            img_arr[bg_pixels] = [255, 255, 255]
            cleaned_shadow = Image.fromarray(img_arr)
            
            coords_body = np.argwhere(combined_mask > 0)
            if coords_body.size > 0:
                y_min_clean = coords_body[:, 0].min()
                y_max_clean = coords_body[:, 0].max()
                x_min_clean = coords_body[:, 1].min()
                x_max_clean = coords_body[:, 1].max()
                bbox = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
                print(f"  [SAM3] Detected BBox: x_min={x_min_clean}, y_min={y_min_clean}, x_max={x_max_clean}, y_max={y_max_clean}")
    except Exception as e:
        print(f"  [SAM3 Warning] SAM 3 detection failed, falling back to pixel diffing: {e}")
    finally:
        # Explicit memory cleanup
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
        
    # Fallback to pixel diffing if SAM 3 didn't find a bbox
    if bbox is None and is_wb and bg_color is not None:
        print("  [Fallback] Running pixel diffing bbox detection...")
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
        
        # Clean off-white background outside the product mask
        img_arr = np.array(cleaned_shadow.convert('RGB'))
        bg_pixels = (~product_pixels_body) & (np.min(img_arr, axis=-1) > 215)
        img_arr[bg_pixels] = [255, 255, 255]
        cleaned_shadow = Image.fromarray(img_arr)
        
        coords_body = np.argwhere(product_pixels_body)
        if coords_body.size > 0:
            y_min_clean = coords_body[:, 0].min()
            y_max_clean = coords_body[:, 0].max()
            x_min_clean = coords_body[:, 1].min()
            x_max_clean = coords_body[:, 1].max()
            bbox = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
            print(f"  [Fallback] BBox: x_min={x_min_clean}, y_min={y_min_clean}, x_max={x_max_clean}, y_max={y_max_clean}")

    if bbox is not None:
        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox
        
        # Crop coordinates with a tight 10px padding
        crop_x_min = max(0, x_min_clean - 10)
        crop_y_min = max(0, y_min_clean - 10)
        crop_x_max = min(w, x_max_clean + 10)
        crop_y_max = min(h, y_max_clean + 10)
        
        cropped = cleaned_shadow.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
        W_p = x_max_clean - x_min_clean
        H_p = y_max_clean - y_min_clean
        
        if slot > 1:
            # Zoom/Detail shot: Crop to shadow bbox and pad to square
            crop_w = crop_x_max - crop_x_min
            crop_h = crop_y_max - crop_y_min
            if crop_w > 5 and crop_h > 5:
                side = max(crop_w, crop_h)
                canvas = Image.new("RGB", (side, side), (255, 255, 255))
                paste_x = (side - crop_w) // 2
                paste_y = (side - crop_h) // 2
                canvas.paste(cropped, (paste_x, paste_y))
                return canvas.resize((2000, 2000), RESAMPLING_METHOD)
        else:
            # Main image (slot 1)
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

def main():
    print("==================================================")
    print("     SAM 3 GPU CROP PIPELINE (ZARA STYLE)        ")
    print("==================================================")
    
    is_test_mode = "--test" in sys.argv
    is_batch20_mode = "--batch20" in sys.argv
    
    if not os.path.exists(JSON_PATH):
        print(f"[ERROR] JSON file not found: {JSON_PATH}")
        return
        
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        missed_dict = json.load(f)
        
    # Choose output folder based on test mode or full mode
    if is_test_mode:
        output_base_dir = os.path.join(FTP_UPLOAD_DIR, "zara_style_test")
        print("Running in TEST mode (processing representative SKUs only).")
    elif is_batch20_mode:
        output_base_dir = os.path.join(FTP_UPLOAD_DIR, "zara_style_batch20")
        print("Running in BATCH20 mode (processing first 20 products).")
    else:
        output_base_dir = os.path.join(FTP_UPLOAD_DIR, "zara_style")
        print("Running in FULL mode (processing all missed products).")
        
    artiklar_dir = os.path.join(output_base_dir, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    for d in (output_base_dir, artiklar_dir, liten_dir, zoom_dir):
        os.makedirs(d, exist_ok=True)
        
    # Initialize SAM 3 Predictor
    print("Initializing SAM 3 semantic predictor on CUDA...")
    try:
        overrides = dict(model="sam3.pt", conf=0.10, device="cuda")
        predictor = SAM3SemanticPredictor(overrides=overrides)
        print("SAM 3 Predictor successfully loaded on GPU.")
    except Exception as e:
        print(f"Error loading SAM 3 predictor: {e}")
        return
        
    # Scan TEST TOPAZ WebP files
    print("Scanning TEST TOPAZ files...")
    topaz_files = [f for f in os.listdir(TOPAZ_DIR) if os.path.isfile(os.path.join(TOPAZ_DIR, f)) and f.lower().endswith('.webp')]
    topaz_products = {}
    for filename in topaz_files:
        m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", filename)
        if m:
            prod_name = m.group(1)
            slot = int(m.group(2))
            if prod_name not in topaz_products:
                topaz_products[prod_name] = []
            topaz_products[prod_name].append((slot, filename))
            
    # If in test mode, only process the specific requested representative SKUs:
    # (Removed 1100476 because it is discontinued)
    test_skus = {"4100081", "1400040", "3200459", "3100237"}
    
    processed_count = 0
    
    for idx, (prod_name, sku) in enumerate(missed_dict.items()):
        # Exclude discontinued Lionel chair
        if sku == "1100476" or "lionel" in prod_name.lower():
            print(f"[{idx+1}/{len(missed_dict)}] Skipping Lionel Chair (SKU: {sku}) - Discontinued.")
            continue
            
        if is_test_mode and sku not in test_skus:
            continue
            
        if is_batch20_mode and processed_count >= 20:
            print("Reached limit of 20 products for batch test.")
            break
            
        if prod_name not in topaz_products:
            print(f"[{idx+1}/{len(missed_dict)}] Skipped '{prod_name}': files not found in TEST TOPAZ.")
            continue
            
        print(f"\n[{idx+1}/{len(missed_dict)}] Processing: '{prod_name}' -> SKU: {sku}")
        
        # Load files for this product
        files_list = topaz_products[prod_name]
        processed_slots = {}
        for slot, filename in files_list:
            path = os.path.join(TOPAZ_DIR, filename)
            processed_slots[slot] = path
            
        if not processed_slots:
            continue
            
        # Classify and size product (with expanded ZARA style target fills)
        category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
        target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
        
        print(f"  Category: {category} | Target W: {target_w:.3f} | Target H: {target_h:.3f} | Centered: {is_centered} | Floor: {floor_pct:.3f}")
        
        # Determine main image slot: Slot 1 is always preferred as main view if available
        if 1 in processed_slots:
            main_slot_num = 1
            main_img_path = processed_slots[1]
        else:
            main_slot_num = min(processed_slots.keys())
            main_img_path = processed_slots[main_slot_num]
                    
        print(f"  Selected main image path: {main_img_path} (Slot {main_slot_num})")
        
        # Determine SAM 3 text prompt
        text_prompts = get_sam3_text_prompt(category, prod_name)
        print(f"  Using SAM 3 text prompts: {text_prompts}")
        
        # Process composition using SAM 3 or resize lifestyle
        main_img_raw = None
        main_img_resized = None
        main_canvas = None
        sec_img_raw = None
        sec_img_resized = None
        try:
            main_img_raw = Image.open(main_img_path)
            main_img_resized = load_and_ensure_size(main_img_raw)
            is_main_wb = is_white_background(main_img_resized)
            
            normal_dest = os.path.join(artiklar_dir, f"{sku}.jpg")
            liten_dest = os.path.join(liten_dir, f"{sku}_S.jpg")
            zoom_dest = os.path.join(zoom_dir, f"{sku}_1.jpg")
            
            if is_main_wb:
                print("  Main image has white background. Processing with SAM 3.")
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
                save_as_jpg(main_canvas, normal_dest, 1000, quality=90)
                save_as_jpg(main_canvas, liten_dest, 400, quality=85)
                save_as_jpg(main_canvas, zoom_dest, 2000, quality=92)
                print(f"  Saved main image for SKU: {sku} (1000px, 400px, 2000px zoom) - Cropped/Zara")
            else:
                print("  Main image is lifestyle/interior. Saving uncropped (preserving aspect ratio).")
                save_as_jpg(main_img_resized, normal_dest, 1000, quality=90)
                save_as_jpg(main_img_resized, liten_dest, 400, quality=85)
                save_as_jpg(main_img_resized, zoom_dest, 2000, quality=92)
                print(f"  Saved main image for SKU: {sku} (1000px, 400px, 2000px zoom) - Uncropped")
                
            processed_count += 1
            
            # Process secondary slots
            for slot, path in sorted(processed_slots.items()):
                if slot == main_slot_num:
                    continue
                
                print(f"  Processing secondary image: Slot {slot}")
                sec_img_raw = Image.open(path)
                sec_img_resized = load_and_ensure_size(sec_img_raw)
                
                sec_zoom_dest = os.path.join(zoom_dir, f"{sku}_{slot}.jpg")
                save_as_jpg(sec_img_resized, sec_zoom_dest, 2000, quality=92)
                print(f"  Saved secondary zoom image for SKU: {sku} slot {slot} (2000px max, uncropped)")
                
                # Close files for secondary slots
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
                
        except Exception as e:
            print(f"  Error processing product '{prod_name}': {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up image files
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
    print("         SAM 3 PIPELINE RUN COMPLETED             ")
    print("==================================================")
    print(f"Output folder: {output_base_dir}")
    print(f"  └─ /artiklar/       (1000x1000): {len([f for f in os.listdir(artiklar_dir) if os.path.isfile(os.path.join(artiklar_dir, f))])} files")
    print(f"  └─ /artiklar/liten/   (400x400): {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (2000x2000): {len(os.listdir(zoom_dir))} files")
    print("--------------------------------------------------")
    print(f"✓ Processed {processed_count} products.")
    print("==================================================")

if __name__ == "__main__":
    main()
