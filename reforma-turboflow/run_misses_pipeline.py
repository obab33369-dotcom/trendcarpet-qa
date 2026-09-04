import os
import sys
import re
import json
import numpy as np
from PIL import Image

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

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
            arr[10:20, 10:20],
            arr[10:20, -20:-10],
            arr[-20:-10, 10:20],
            arr[-20:-10, -20:-10]
        ]
        means = [np.mean(pat, axis=(0,1)) for pat in patches]
        means.sort(key=lambda c: np.sum(c))
        bg_color = np.mean(means[1:], axis=0) # average of top 3 corners
        bg_mean = np.mean(bg_color)
        return bg_mean > 235, bg_color
    except Exception:
        return False, None

def is_white_background(img):
    is_wb, _ = is_white_background_robust(img)
    return is_wb

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
    
    # 1. SOFA
    is_sofa = False
    if "soffa" in folder_lower or "sofa" in folder_lower or "baddsoffa" in folder_lower or "bäddsoffa" in folder_lower or "schaslong" in folder_lower:
        is_sofa = True
        
    if is_sofa:
        is_2_seat = any(x in folder_lower for x in ["2-sits", "2-seater", "2sits", "2seater", "loveseat", "love-seat", "baddfatolj", "bäddfåtölj"])
        if is_2_seat:
            return "sofa_2_seat", 0.76, 0.369, 0.1309, False
        else:
            return "sofa_3_seat", 0.86, 0.369, 0.1309, False

    # 2. CHAIRS, ARMCHAIRS, BARSTOOLS, STOOLS
    is_chair = any(x in folder_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"])
    if is_chair:
        if any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol"]):
            return "armchair", 0.74, 0.65, 0.10, False
        elif "barstol" in folder_lower:
            return "barstool", 0.50, 0.75, 0.10, False
        elif any(x in folder_lower for x in ["pall", "puff", "sittpuff"]):
            return "stool", 0.65, 0.65, 0.10, False
        else:
            return "chair_dining", 0.76, 0.68, 0.10, False

    # 3. TABLES
    is_table = any(x in folder_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord"])
    if is_table:
        is_dining = any(x in folder_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"])
        if is_dining:
            return "table_large", 0.82, 0.45, 0.113, False
        else:
            return "table_small", 0.685, 0.52, 0.113, False

    # 4. CABINETS
    is_cabinet = any(x in folder_lower for x in ["skap", "skåp", "byra", "byrå", "sideboard", "skank", "skänk", "garderob", "tv-bank", "tv-bänk", "vinhylla"])
    if is_cabinet:
        is_large = any(x in folder_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ"]) or ("skap" in folder_lower or "skåp" in folder_lower) and not any(x in folder_lower for x in ["sido", "litet", "byra", "byrå"])
        if is_large:
            return "cabinet_large", 0.60, 0.80, 0.10, False
        else:
            return "cabinet_small", 0.75, 0.55, 0.10, False

    # 5. SHELVES
    is_shelf = any(x in folder_lower for x in ["hylla", "hyllor", "vagghylla", "vägghylla", "vagghyllor", "vägghyllor"])
    if is_shelf:
        is_wall = any(x in folder_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"])
        if is_wall:
            return "shelf_hanging", 0.60, 0.35, 0.50, True
        else:
            return "shelf_floor", 0.65, 0.75, 0.10, False

    # 6. LIGHTING
    is_lamp = any(x in folder_lower for x in ["lamp", "lampa", "belysning", "ljus", "stjarna", "stjärna", "advent"])
    if is_lamp:
        if "golv" in folder_lower:
            return "lamp_floor", 0.40, 0.78, 0.10, False
        elif "bord" in folder_lower:
            return "lamp_table", 0.35, 0.45, 0.50, True
        elif any(x in folder_lower for x in ["taklampa", "pendel", "krona", "plafond", "adventstjarna", "adventstjärna", "stjarna", "stjärna", "oslo", "sally", "lotus"]):
            return "lamp_pendant", 0.50, 0.50, 0.50, True
        elif "vagg" in folder_lower or "vägg" in folder_lower:
            return "lamp_wall", 0.40, 0.40, 0.50, True
        else:
            return "lamp_pendant", 0.50, 0.50, 0.50, True

    # 7. DEFAULT
    return "default", 0.65, 0.65, 0.50, True

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
        target_w = max(0.55, min(0.90, target_w))
    elif category == "shelf_hanging":
        width = 75
        for num in map(int, numbers):
            if 15 <= num <= 150:
                width = num
                break
        scale = width / 75.0
        target_w = target_w * scale
        target_w = max(0.35, min(0.85, target_w))
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
        target_h = max(0.50, min(0.88, target_h))
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

def process_image(img_path_or_bytes, category, target_w_fill, target_h_fill, floor_pct, is_centered, slot=1):
    if isinstance(img_path_or_bytes, Image.Image):
        img = img_path_or_bytes
    else:
        img = Image.open(img_path_or_bytes)
        
    img = load_and_ensure_size(img)
    w, h = img.size
    
    is_wb, bg_color = is_white_background_robust(img)
    
    bbox = None
    cleaned_shadow = img
    coords_body = None
    
    if is_wb and bg_color is not None:
        # Clean background
        cleaned_shadow = clean_offwhite_background(img, bg_color)
        
        # Detect shadow bounding box with 80px border mask
        arr_shadow_arr = np.array(cleaned_shadow).copy()
        arr_shadow_arr[:80, :, :] = [255, 255, 255]
        arr_shadow_arr[-80:, :, :] = [255, 255, 255]
        arr_shadow_arr[:, :80, :] = [255, 255, 255]
        arr_shadow_arr[:, -80:, :] = [255, 255, 255]
        
        product_pixels_shadow = np.any(arr_shadow_arr < 254, axis=-1)
        coords_shadow = np.argwhere(product_pixels_shadow)
        
        if coords_shadow.size > 0:
            y_min_raw = coords_shadow[:, 0].min()
            y_max_raw = coords_shadow[:, 0].max()
            x_min_raw = coords_shadow[:, 1].min()
            x_max_raw = coords_shadow[:, 1].max()
            
            # Detect body bounding box with 80px border mask
            img_rgb = img.convert('RGB')
            arr = np.array(img_rgb)
            diff = np.sum(np.abs(arr - bg_color), axis=-1)
            mask_body = (diff < 25) & (arr[:,:,0] > 180) & (arr[:,:,1] > 180) & (arr[:,:,2] > 180)
            arr_body = arr.copy()
            arr_body[mask_body] = [255, 255, 255]
            
            arr_body[:80, :, :] = [255, 255, 255]
            arr_body[-80:, :, :] = [255, 255, 255]
            arr_body[:, :80, :] = [255, 255, 255]
            arr_body[:, -80:, :] = [255, 255, 255]
            
            product_pixels_body = np.any(arr_body < 254, axis=-1)
            coords_body = np.argwhere(product_pixels_body)
            
            if coords_body.size > 0:
                y_min_clean = coords_body[:, 0].min()
                y_max_clean = coords_body[:, 0].max()
                x_min_clean = coords_body[:, 1].min()
                x_max_clean = coords_body[:, 1].max()
            else:
                y_min_clean, y_max_clean, x_min_clean, x_max_clean = y_min_raw, y_max_raw, x_min_raw, x_max_raw
                
            bbox = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
        else:
            coords_body = np.array([])
            
    if bbox is not None:
        x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox
        
        if slot > 1:
            # Zoom/Detail shot: Crop to shadow bbox and pad to square
            crop_w = x_max_raw - x_min_raw
            crop_h = y_max_raw - y_min_raw
            if crop_w > 5 and crop_h > 5:
                cropped = cleaned_shadow.crop((x_min_raw, y_min_raw, x_max_raw, y_max_raw))
                side = max(crop_w, crop_h)
                canvas = Image.new("RGB", (side, side), (255, 255, 255))
                paste_x = (side - crop_w) // 2
                paste_y = (side - crop_h) // 2
                canvas.paste(cropped, (paste_x, paste_y))
                return canvas.resize((2000, 2000), RESAMPLING_METHOD)
        else:
            # Main image (slot 1)
            y_cutoff = y_min_clean + int(0.6 * (y_max_clean - y_min_clean))
            solid_coords = coords_body[coords_body[:, 0] <= y_cutoff] if coords_body.size > 0 else np.array([])
            if solid_coords.size > 0:
                x_min_solid = solid_coords[:, 1].min()
                x_max_solid = solid_coords[:, 1].max()
            else:
                x_min_solid, x_max_solid = x_min_clean, x_max_clean
                
            if not is_centered:
                W_p = x_max_solid - x_min_solid
                H_p = y_max_clean - y_min_clean
            else:
                W_p = x_max_clean - x_min_clean
                H_p = y_max_clean - y_min_clean
                
            crop_x_min = x_min_raw if not is_centered else x_min_clean
            crop_x_max = x_max_raw if not is_centered else x_max_clean
            crop_y_min = y_min_raw if not is_centered else y_min_clean
            crop_y_max = y_max_raw if not is_centered else y_max_clean
            
            cropped = cleaned_shadow.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))
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
                
            if not is_centered:
                offset_x = x_min_solid - crop_x_min
                offset_y = y_min_clean - crop_y_min
            else:
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
        
    if img_copy.size != (target_size, target_size):
        img_copy = img_copy.resize((target_size, target_size), RESAMPLING_METHOD)
    img_copy.save(dest_path, "JPEG", quality=quality)

def main():
    print("==================================================")
    print("       MISSED PRODUCTS PROCESSING PIPELINE        ")
    print("==================================================")
    
    if not os.path.exists(JSON_PATH):
        print(f"[ERROR] JSON file not found: {JSON_PATH}")
        return
        
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        missed_dict = json.load(f)
        
    print(f"Loaded {len(missed_dict)} missed products from list.")
    
    # Staging dirs
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    for d in (artiklar_dir, liten_dir, zoom_dir):
        os.makedirs(d, exist_ok=True)
        
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
            
    processed_count = 0
    
    for idx, (prod_name, sku) in enumerate(missed_dict.items()):
        if prod_name not in topaz_products:
            print(f"[{idx+1}/{len(missed_dict)}] Skipped '{prod_name}': files not in TEST TOPAZ.")
            continue
            
        print(f"[{idx+1}/{len(missed_dict)}] Processing: '{prod_name}' -> SKU: {sku}")
        
        # Load files
        files_list = topaz_products[prod_name]
        processed_slots = {}
        for slot, filename in files_list:
            path = os.path.join(TOPAZ_DIR, filename)
            try:
                img = Image.open(path)
                processed_slots[slot] = img
            except Exception as e:
                print(f"  Error loading {filename}: {e}")
                
        if not processed_slots:
            continue
            
        # Classify and size product
        category, target_w, target_h, floor_pct, is_centered = classify_and_size_product(prod_name)
        target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
        
        # Staging splits
        white_bg_slots = {}
        interior_slots = {}
        for slot, img in sorted(processed_slots.items()):
            img_resized = load_and_ensure_size(img)
            if is_white_background(img_resized):
                white_bg_slots[slot] = img
            else:
                interior_slots[slot] = img
                
        # Main normal & zoom selection
        main_img = None
        main_slot_num = 1
        
        # Override to force slot 1 for Lionel chair (SKU 1100476) since other slots are close-ups or fabric swatches
        if sku == "1100476" or "lionel" in prod_name.lower():
            if 1 in processed_slots:
                main_img = processed_slots[1]
                main_slot_num = 1
                print(f"  [OVERRIDE] Forcing slot 1 as main image for SKU: {sku} ({prod_name})")
                
        if main_img is None:
            if 1 in white_bg_slots:
                main_img = white_bg_slots[1]
                main_slot_num = 1
            elif white_bg_slots:
                main_slot_num = min(white_bg_slots.keys())
                main_img = white_bg_slots[main_slot_num]
                
            if main_img is None:
                if 1 in processed_slots:
                    main_slot_num = 1
                    main_img = processed_slots[1]
                else:
                    main_slot_num = min(processed_slots.keys())
                    main_img = processed_slots[main_slot_num]
                
        # Zoom sequence: interior first, then remaining white bg
        zoom_sequence = []
        for slot in sorted(interior_slots.keys()):
            zoom_sequence.append((interior_slots[slot], slot))
        for slot in sorted(white_bg_slots.keys()):
            if white_bg_slots[slot] != main_img:
                zoom_sequence.append((white_bg_slots[slot], slot))
                
        # Process composition
        try:
            main_canvas = process_image(main_img, category, target_w, target_h, floor_pct, is_centered, slot=1)
            
            # Save normal, liten, zoom1
            save_as_jpg(main_canvas, os.path.join(artiklar_dir, f"{sku}.jpg"), 1000, quality=90)
            save_as_jpg(main_canvas, os.path.join(liten_dir, f"{sku}_S.jpg"), 400, quality=85)
            
            # Zoom output bypassed per user request
            # save_as_jpg(main_canvas, os.path.join(zoom_dir, f"{sku}_1.jpg"), 2000, quality=92)
            # for s_idx, (z_img, z_slot) in enumerate(zoom_sequence):
            #     z_canvas = process_image(z_img, category, target_w, target_h, floor_pct, is_centered, slot=z_slot)
            #     save_as_jpg(z_canvas, os.path.join(zoom_dir, f"{sku}_{s_idx + 2}.jpg"), 2000, quality=92)
                
            print(f"  Successfully processed '{prod_name}' to SKU: {sku} (liten & normal images staged).")
            processed_count += 1
        except Exception as e:
            print(f"  Error processing '{prod_name}': {e}")
            
    print("\n==================================================")
    print("        MISSED PRODUCTS PROCESSING COMPLETED!     ")
    print("==================================================")
    print(f"Output staging folder: {FTP_UPLOAD_DIR}")
    print(f"  └─ /artiklar/      (Normal images, 1000px): {len(os.listdir(artiklar_dir)) - 1} files")
    print(f"  └─ /artiklar/liten/ (Small images, 400px):  {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (Zoom/Renders, 2000px): {len(os.listdir(zoom_dir))} files")
    print("--------------------------------------------------")
    print(f"✓ Total missed products processed: {processed_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
