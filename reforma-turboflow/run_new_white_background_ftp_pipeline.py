import os
import sys
import re
import shutil
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

# Paths
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped")

# Fallback for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

def get_beautiful_name(folder_name):
    name = re.sub(r'^\d+\s*', '', folder_name)
    name = name.replace('_', ' ').replace('-', ' ').strip()
    name = re.sub(r'\s+', ' ', name)
    return name

def classify_folder(cat_name, folder_name):
    cat_lower = cat_name.lower()
    folder_lower = folder_name.lower()
    
    # 1. Sofa classification
    is_sofa = False
    if "sofa" in cat_lower or "soff" in cat_lower:
        if "soffbord" not in folder_lower and "soffbord" not in cat_lower:
            is_sofa = True
    elif ("soffa" in folder_lower or "sofa" in folder_lower or "baddsoffa" in folder_lower or "bäddsoffa" in folder_lower or "modulsoffa" in folder_lower or "schaslong" in folder_lower) and "soffbord" not in folder_lower:
        is_sofa = True
        
    if is_sofa:
        return "sofa"
        
    # 2. Chairs and Armchairs classification (Excluding armchairs, stools, and barstools)
    is_chair = False
    is_excluded_chair = False
    if "armchair" in cat_lower:
        is_excluded_chair = True
    elif any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "pall", "barstol"]):
        is_excluded_chair = True
        
    if not is_excluded_chair:
        if "chair" in cat_lower or "stol" in cat_lower:
            is_chair = True
        elif any(x in folder_lower for x in ["stol", "karmstol", "pinnstol"]):
            is_chair = True
        
    if is_chair:
        return "chair_armchair"
        
    # 3. Tables classification (excluding Dining Tables)
    is_table = False
    if any(x in folder_lower for x in ["soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord"]):
        is_table = True
    elif "table" in cat_lower:
        is_dining = any(x in folder_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"])
        if not is_dining:
            is_table = True
            
    if is_table:
        return "table_non_dining"
        
    return "default"

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

def crop_and_resize(img_path, target_size=2000, category='default', slot=1, is_zoom=False):
    with Image.open(img_path) as img:
        width, height = img.size
        
        # Ensure the source image is at least target_size
        max_dim = max(width, height)
        if max_dim < target_size:
            scale = float(target_size) / max_dim
            new_w = int(width * scale)
            new_h = int(height * scale)
            img = img.resize((new_w, new_h), RESAMPLING_METHOD)
            width, height = img.size
            
        is_wb, bg_color = is_white_background_robust(img)
        
        bbox = None
        cleaned_shadow = img
        coords = None
        
        if is_wb and category != 'default' and bg_color is not None:
            # 1. Clean background/shadows
            cleaned_shadow = clean_offwhite_background(img, bg_color)
            
            # Detect shadow bounding box
            arr_shadow_arr = np.array(cleaned_shadow)
            product_pixels_shadow = np.any(arr_shadow_arr[5:-5, 5:-5] < 254, axis=-1)
            coords_shadow = np.argwhere(product_pixels_shadow)
            
            if coords_shadow.size > 0:
                y_min_raw = coords_shadow[:, 0].min() + 5
                y_max_raw = coords_shadow[:, 0].max() + 5
                x_min_raw = coords_shadow[:, 1].min() + 5
                x_max_raw = coords_shadow[:, 1].max() + 5
                
                # Detect body bounding box (tolerance 25)
                img_rgb = img.convert('RGB')
                arr = np.array(img_rgb)
                diff = np.sum(np.abs(arr - bg_color), axis=-1)
                mask_body = (diff < 25) & (arr[:,:,0] > 180) & (arr[:,:,1] > 180) & (arr[:,:,2] > 180)
                arr_body = arr.copy()
                arr_body[mask_body] = [255, 255, 255]
                product_pixels_body = np.any(arr_body[5:-5, 5:-5] < 254, axis=-1)
                coords = np.argwhere(product_pixels_body)
                
                if coords.size > 0:
                    y_min_clean = coords[:, 0].min() + 5
                    y_max_clean = coords[:, 0].max() + 5
                    x_min_clean = coords[:, 1].min() + 5
                    x_max_clean = coords[:, 1].max() + 5
                else:
                    y_min_clean, y_max_clean, x_min_clean, x_max_clean = y_min_raw, y_max_raw, x_min_raw, x_max_raw
                    
                bbox = (x_min_clean, y_min_clean, x_max_clean, y_max_clean)
            else:
                coords = np.array([])
                
        if bbox is not None:
            x_min_clean, y_min_clean, x_max_clean, y_max_clean = bbox
            
            if is_zoom:
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
                    return canvas.resize((target_size, target_size), RESAMPLING_METHOD)
            else:
                if category == 'chair_armchair':
                    # Floor-aligned composition engine for chairs (71.5% height fill target)
                    # Find solid horizontal bounds from upper 60% of detected vertical height
                    y_cutoff = y_min_clean + int(0.6 * (y_max_clean - y_min_clean))
                    solid_coords = coords[coords[:, 0] <= (y_cutoff - 5)] if coords.size > 0 else np.array([])
                    if solid_coords.size > 0:
                        x_min_solid = solid_coords[:, 1].min() + 5
                        x_max_solid = solid_coords[:, 1].max() + 5
                    else:
                        x_min_solid, x_max_solid = x_min_clean, x_max_clean
                    
                    W_p = x_max_solid - x_min_solid
                    H_p = y_max_clean - y_min_clean
                    
                    cropped = cleaned_shadow.crop((x_min_raw, y_min_raw, x_max_raw, y_max_raw))
                    
                    target_w_fill = 0.76
                    target_h_fill = 0.68
                    floor_pct = 0.10
                    
                    scale = min((target_w_fill * target_size) / W_p, (target_h_fill * target_size) / H_p)
                    
                    # Ensure it fits on canvas with the floor line
                    max_h_allowed = int(target_size - (floor_pct * target_size) - 20)
                    new_h_body = int(H_p * scale)
                    if new_h_body > max_h_allowed:
                        scale = max_h_allowed / H_p
                        new_h_body = int(H_p * scale)
                        
                    new_w_body = int(W_p * scale)
                    
                    # Resize the cropped image
                    new_w_crop = int((x_max_raw - x_min_raw) * scale)
                    new_h_crop = int((y_max_raw - y_min_raw) * scale)
                    cropped_resized = cropped.resize((new_w_crop, new_h_crop), RESAMPLING_METHOD)
                    
                    # Create white canvas
                    canvas = Image.new("RGB", (target_size, target_size), (255, 255, 255))
                    
                    # Target positions for chair body
                    paste_x_body = (target_size - new_w_body) // 2
                    paste_y_body = int(target_size - (floor_pct * target_size) - new_h_body)
                    
                    # Calculate paste offset for crop
                    offset_x = x_min_solid - x_min_raw
                    offset_y = y_min_clean - y_min_raw
                    
                    paste_x = paste_x_body - int(offset_x * scale)
                    paste_y = paste_y_body - int(offset_y * scale)
                    
                    canvas.paste(cropped_resized, (paste_x, paste_y))
                    return canvas
                else:
                    # Centered cropping logic for sofas, tables, and others (keeps shadow)
                    min_dim = min(width, height)
                    center_x = width / 2
                    center_y = height / 2
                    
                    # Compute minimum S required to fit the product centered on the image center
                    def get_min_centered_size(margin):
                        dx = max(abs(center_x - x_min_clean), abs(x_max_clean - center_x))
                        dy = max(abs(center_y - y_min_clean), abs(y_max_clean - center_y))
                        return 2 * max(dx, dy) + 2 * margin
                    
                    if category == 'sofa':
                        S = 0.93 * min_dim
                        S_min_5 = get_min_centered_size(5)
                        if S < S_min_5:
                            S = 0.95 * min_dim
                            if S < S_min_5:
                                S = get_min_centered_size(2)
                        S = min(S, min_dim)
                    elif category == 'table_non_dining':
                        S = 0.93 * min_dim
                        S_min_5 = get_min_centered_size(5)
                        if S < S_min_5:
                            S = S_min_5
                        S = min(S, min_dim)
                    else:
                        S = min_dim
                        
                    left = center_x - S / 2
                    top = center_y - S / 2
                    right = center_x + S / 2
                    bottom = center_y + S / 2
                    
                    left = max(0.0, left)
                    top = max(0.0, top)
                    right = min(float(width), right)
                    bottom = min(float(height), bottom)
                    
                    cropped = cleaned_shadow.crop((left, top, right, bottom))
                    return cropped.resize((target_size, target_size), RESAMPLING_METHOD)
                    
        # Fallback centered square crop if not white background or bbox detection fails
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        cropped = img.crop((left, top, right, bottom))
        return cropped.resize((target_size, target_size), RESAMPLING_METHOD)

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

def normalize_name(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
        
    # Strip parentheses
    text = re.sub(r'\(.*?\)', '', text)
    # Strip category prefixes
    text = re.sub(r'^\d+\s*', '', text)
    
    # Text-level translation synonyms
    text = text.replace('sofa bed', 'baddsoffa')
    text = text.replace('bed sofa', 'baddsoffa')
    text = text.replace('bed armchair', 'baddfatolj')
    text = text.replace('sofabed', 'baddsoffa')
    text = text.replace('bedsofa', 'baddsoffa')
    text = text.replace('bedarmchair', 'baddfatolj')
    text = text.replace('seater sofa', 'sitssoffa')
    text = text.replace('seatersofa', 'sitssoffa')
    text = text.replace('sofa', 'soffa')
    text = text.replace('module', 'modul')
    text = text.replace('eucalyptus', 'eukalyptus')
    text = text.replace('cape verde', 'kap verde')
    text = text.replace('3-seater', '3-sits')
    text = text.replace('2-seater', '2-sits')
    text = text.replace('3 seater', '3 sits')
    text = text.replace('2 seater', '2 sits')
    text = text.replace('off-white', 'vit')
    text = text.replace('off white', 'vit')
    text = text.replace('offwhite', 'vit')
    text = text.replace('mintgron', 'gron')
    text = text.replace('ongom', 'angom')
    text = text.replace('ängom', 'angom')
    
    # Strip all non-alphanumeric
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

# Hardcoded corrections for complex edge cases (maps normalized name to another normalized name)
hardcoded_map = {
    'barstoltarnsjsvart': 'barstoltarnsjobrun',
    'barstoltarnsjovalnot': 'barstoltarnsjosvart',
    'stolgalsvart': 'stolgalgrasvart',
    'karmstolrottingsvart': 'karmstolrottingblack',
    'stolaltabeigevitpigmenterad': 'stolaltavitpigmenterad',
    'modulmessina118x110cmvit': 'modulmessina118x110cmbenvit',
    'soffabaddkapverdekapverdebeige': 'baddsoffakapverdebeige',
    'soffabaddklippanbeige': 'baddsoffaklippanbeige',
    'soffabaddsanfranciscodarkgrey': 'baddfatoljsanfranciscomorkgra',
    'soffabaddtexasdarkgrey': 'baddsoffatexasmorkgra',
    'soffabaddtexaslightgrey': 'baddsoffatexasljusgra',
    'soffabaddtexasbeige': 'baddsoffatexasbeige',
    'matbordfager135cmnatur': 'matbordelsa135cmvitpigmenterad',
    'soffbordtwin2delarnatur': 'soffbordtwinx2natursvart',
    'soffbordruntnagano2delarek': 'soffbordruntnagano2setek',
    'matbordmodena180220x90cmbrun': 'matbordmodena180cmbrun',
    'sidobordsapri45x60cmvalnottravertin': 'sidobordsangbordsapri45x60cmvalnottravertin',
    'soffbordcremerunt75cmvalnot': 'soffbordcremerund75cmvalnot',
    'soffbordcremerunt75cmvitpigmenterad': 'soffbordcremerund75cmvitpigmenterad',
    'soffbordprimes2delarvalnot': 'soffbordprimesvalnot',
    'soffbordcremerunt55cmvitpigmenterad': 'soffbordcremerund55cmvitpigmenterad',
    'line180x90': 'matbordline180x90cmvitpigmenterad',
    'saba120x165': 'matbordsabaovaltrunt120165x120cmek',
    'saba180x90': 'matbordsaba180x90cmek',
    'sidobordtorekovvalnot': 'sidobordtorekovljusvalnot',
    'soffbordnagano2delarek': 'soffbordnagano2setek',
    'sideboardhagaviksvart': 'sideboardhagavik2sektionersvartmassing',
    'tvbankmyshultlnatur': 'tvbankmyshult200x55cmnatur',
    'tvbankmyshultsnatur': 'tvbankmyshult160x55cmnatur',
    
    # Ängom Ljusbeige -> Ängom Beige
    'stolangomljusbeige': 'stolangombeige',
}

# Hardcoded overrides to map normalized folder names directly to SKUs
hardcoded_sku_map = {
    'baddsoffasanfranciscodarkgrey': 'MLM-502390-Darkgrey',
    'baddsoffatexasdarkgrey': 'MLM-502580',
    'baddsoffatexaslightgrey': 'MLM-502580-lightgrey',
    'adventsstjarnaoslo60cmvit': 'WW-advent-star-white-2',
    'stolmontmartrevintagesvart': 'SM-1027C-sblack',
    'stolmontmartrevintagesvartantik': 'SM-1027C-sBlackgold',
    'stolmontmartrevintagekoppar': 'SM-1027C-scopper',
    'stolmontmartrevitlackad': 'SM-1027C-white',
    'stolmontmartrerodlackad': 'SM-1027C-red',
    'stolmontmartrerustikstal': 'SM-1027C-steel',
    'stolmontmartregullackad': 'SM-1027C-yellow',
    'stolmontmartresvartlack': 'SM-1027C-Black',
    'stolmontmartreorangelack': 'SM-1027C-orange',
    'stolvintageladerjarn': 'MA0215',
    'stolvintageladerjarnnhweb': 'MA0215',
    'vagghyllahydra24cmsvartnatur': '79420',
    'vagghyllahydra114cmsvartnatur': '75966',
    'stolmidnattsammet': 'SC-264F',
    'stolmidnattsammetnhweb': 'SC-264F',
}

def is_processed_image(filename):
    fn_lower = filename.lower()
    if not fn_lower.endswith(('.jpg', '.jpeg', '.png')):
        return False
    if re.search(r'-\d+-\d+\.', fn_lower):
        return False
    return True

def is_white_background_robust(img):
    try:
        img_rgb = img.convert('RGB')
        arr = np.array(img_rgb)
        h, w, _ = arr.shape
        # Define 4 corner patches of size 10x10, inset by 10px to avoid 1px black edges
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

def is_white_background(img_path):
    try:
        with Image.open(img_path) as img:
            is_wb, _ = is_white_background_robust(img)
            return is_wb
    except Exception:
        return False


def extract_slot_number(filename, folder_name):
    fn_lower = filename.lower()
    folder_words = folder_name.lower().replace('_', ' ').replace('-', ' ').split()
    cleaned_fn = fn_lower
    for w in folder_words:
        if w.strip() and w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', 'byra', 'skap', 'skänk', 'skank', 'hylla', 'bänk'):
            cleaned_fn = cleaned_fn.replace(w, '')
            
    cleaned_fn = re.sub(r'\d+cm', '', cleaned_fn)
    cleaned_fn = re.sub(r'\d+\s*sits', '', cleaned_fn)
    cleaned_fn = re.sub(r'^\d+\s*', '', cleaned_fn)
    
    m = re.search(r'[-_]\d+[-_](\d+)[-_]', cleaned_fn)
    if m:
        return int(m.group(1))
    m = re.search(r'[-_]\d+[-_](\d+)\.[a-zA-Z]+$', cleaned_fn)
    if m:
        return int(m.group(1))
    m = re.search(r'[-_](\d+)[-_]', cleaned_fn)
    if m:
        return int(m.group(1))
    m = re.search(r'[-_](\d+)\.[a-zA-Z]+$', cleaned_fn)
    if m:
        return int(m.group(1))
        
    if fn_lower.endswith(('-w.jpg', '-w.jpeg', '-w.png', '-wonder-w.jpg', '-wonder-w.jpeg', '-w-wonder.jpg', '-w-wonder.jpeg', '-wonder-w.png')):
        return 1
    return None

def main():
    print("==================================================")
    print("   NEW EXCLUSIVE WHITE BG ASKÅS FTP PIPELINE")
    print("==================================================")
    
    # Validate directories
    if not os.path.exists(NEW_WHITE_BG_DIR):
        print(f"[ERROR] Renders directory not found: {NEW_WHITE_BG_DIR}")
        return
    if not os.path.exists(ORIG_DIR):
        print(f"[ERROR] Original product images directory not found: {ORIG_DIR}")
        return
        
    # Scan all product folders in Refoma white background fix (categorized by subdirectory)
    categories = [d for d in os.listdir(NEW_WHITE_BG_DIR) if os.path.isdir(os.path.join(NEW_WHITE_BG_DIR, d))]
    render_folders = []
    for cat in categories:
        cat_path = os.path.join(NEW_WHITE_BG_DIR, cat)
        
        # Handle the nested White background directory in the cabinet category
        if cat.lower() == "cabinet":
            nested_path = os.path.join(cat_path, "White background")
            if os.path.exists(nested_path) and os.path.isdir(nested_path):
                cat_path = nested_path
                
        prods = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
        for p in prods:
            render_folders.append((cat, p, os.path.join(cat_path, p)))
            
    print(f"[INFO] Found {len(render_folders)} total product folders to process across {len(categories)} categories.")
    
    # List original folders (used solely for SKU resolution)
    orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]
    print(f"[INFO] Loaded {len(orig_folders)} reference product folders in {ORIG_DIR} to resolve SKUs.")
    
    # Set up output staging folders
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    print("\n[STAGE 1] Cleaning old staging directories...")
    for d in (artiklar_dir, liten_dir, zoom_dir):
        if os.path.exists(d):
            print(f"  Cleaning: {d}")
            for filename in os.listdir(d):
                file_p = os.path.join(d, filename)
                if os.path.isfile(file_p):
                    try: os.unlink(file_p)
                    except Exception: pass
        else:
            os.makedirs(d, exist_ok=True)
            
    processed_count = 0
    skipped_count = 0
    default_skipped_count = 0
    unmapped_folders = []
    
    print("\n[STAGE 2] Processing and packaging products...")
    
    for idx, (cat, r_folder, prod_path) in enumerate(render_folders):
        category = classify_folder(cat, r_folder)
        if category == "default":
            default_skipped_count += 1
            continue
            
        r_norm = normalize_name(r_folder)
        
        sku = None
        if r_norm in hardcoded_sku_map:
            sku = hardcoded_sku_map[r_norm]
        else:
            if r_norm in hardcoded_map:
                r_norm = hardcoded_map[r_norm]
                
            found_orig = None
            for o_folder in orig_folders:
                o_norm = normalize_name(o_folder)
                if r_norm == o_norm:
                    found_orig = o_folder
                    break
                    
            if not found_orig:
                for o_folder in orig_folders:
                    o_norm = normalize_name(o_folder)
                    if r_norm in o_norm or o_norm in r_norm:
                        found_orig = o_folder
                        break
                        
            if not found_orig:
                r_words = set(r_folder.lower().replace('_', ' ').replace('-', ' ').split())
                for o_folder in orig_folders:
                    o_words = set(o_folder.lower().replace('_', ' ').replace('-', ' ').split())
                    sig_r = {w for w in r_words if w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', '3', '2', 'pack', 'byra', 'skap', 'skänk', 'skank', 'hylla', 'bänk')}
                    sig_o = {w for w in o_words if w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', '3', '2', 'pack', 'byra', 'skap', 'skänk', 'skank', 'hylla', 'bänk')}
                    if sig_r and sig_o and sig_r == sig_o:
                        found_orig = o_folder
                        break
                        
            if not found_orig:
                print(f"✗ [{idx+1}/{len(render_folders)}] UNMAPPED: '{r_folder}' in category '{cat}'")
                unmapped_folders.append((cat, r_folder))
                skipped_count += 1
                continue
                
            sku_match = re.search(r'\(([^)]+)\)', found_orig)
            if not sku_match:
                print(f"✗ [{idx+1}/{len(render_folders)}] NO SKU in original folder name: '{found_orig}'")
                unmapped_folders.append((cat, r_folder))
                skipped_count += 1
                continue
                
            sku = sku_match.group(1).strip()
            
        print(f"✓ [{idx+1}/{len(render_folders)}] MAPPED: '{r_folder}' -> SKU: '{sku}'")
        
        # Process files
        files = [f for f in os.listdir(prod_path) if os.path.isfile(os.path.join(prod_path, f))]
        image_files = [f for f in files if is_processed_image(f)]
        
        white_bg_files = []
        interior_files = []
        for f in image_files:
            if is_white_background(os.path.join(prod_path, f)):
                white_bg_files.append(f)
            else:
                interior_files.append(f)
                
        # Group white bg by slot
        white_bg_groups = {}
        for f in white_bg_files:
            slot = extract_slot_number(f, r_folder)
            if slot is not None:
                if slot not in white_bg_groups:
                    white_bg_groups[slot] = []
                white_bg_groups[slot].append(f)
                
        selected_white_bg = {}
        for slot, candidates in white_bg_groups.items():
            best_cand = candidates[0]
            best_score = -1
            for cand in candidates:
                cand_lower = cand.lower()
                score = 0
                if cand_lower.endswith(('-w.jpg', '-w.jpeg', '-v2.jpg', '-v2.jpeg', '-v2.png')):
                    score = 10
                elif cand_lower.endswith(('-wonder-w.jpg', '-wonder-w.jpeg', '-w-wonder.jpg', '-w-wonder.jpeg')):
                    score = 8
                elif 'wonder' in cand_lower:
                    score = 5
                elif 'v2' in cand_lower:
                    score = 4
                elif 'v1' in cand_lower:
                    score = 3
                if score > best_score:
                    best_score = score
                    best_cand = cand
            selected_white_bg[slot] = best_cand
            
        # Group interior by slot
        interior_groups = {}
        for f in interior_files:
            slot = extract_slot_number(f, r_folder)
            if slot is not None:
                if slot not in interior_groups:
                    interior_groups[slot] = []
                interior_groups[slot].append(f)
                
        selected_interior = {}
        for slot, candidates in interior_groups.items():
            best_cand = candidates[0]
            best_score = -1
            for cand in candidates:
                cand_lower = cand.lower()
                score = 0
                if cand_lower.endswith(('-w.jpg', '-w.jpeg', '-v2.jpg', '-v2.jpeg', '-v2.png')):
                    score = 10
                elif cand_lower.endswith(('-wonder-w.jpg', '-wonder-w.jpeg', '-w-wonder.jpg', '-w-wonder.jpeg')):
                    score = 8
                elif 'wonder' in cand_lower:
                    score = 5
                elif 'v2' in cand_lower:
                    score = 4
                elif 'v1' in cand_lower:
                    score = 3
                if score > best_score:
                    best_score = score
                    best_cand = cand
            selected_interior[slot] = best_cand
            
        # Select main image
        main_img = None
        main_slot_num = 1
        if 1 in selected_white_bg:
            main_img = selected_white_bg[1]
            main_slot_num = 1
        elif selected_white_bg:
            main_slot_num = min(selected_white_bg.keys())
            main_img = selected_white_bg[main_slot_num]
            
        if not main_img:
            print(f"    ⚠️ Warning: No valid white background images found in folder!")
            skipped_count += 1
            continue
            
        # Build zoom sequence: interior first, then remaining white bg
        zoom_sequence = []
        for slot in sorted(selected_interior.keys()):
            zoom_sequence.append((selected_interior[slot], slot))
        for slot in sorted(selected_white_bg.keys()):
            f = selected_white_bg[slot]
            if f != main_img:
                zoom_sequence.append((f, slot))
                
        try:
            main_normal_resized = crop_and_resize(os.path.join(prod_path, main_img), target_size=1000, category=category, slot=main_slot_num, is_zoom=False)
            
            dest_normal = os.path.join(artiklar_dir, f"{sku}.jpg")
            save_as_jpg(main_normal_resized, dest_normal, 1000, quality=90)
            
            dest_liten = os.path.join(liten_dir, f"{sku}_S.jpg")
            save_as_jpg(main_normal_resized, dest_liten, 400, quality=85)
            
            # Zoom output bypassed per user request
            # main_zoom_resized = crop_and_resize(os.path.join(prod_path, main_img), target_size=2000, category=category, slot=main_slot_num, is_zoom=True)
            # dest_zoom1 = os.path.join(zoom_dir, f"{sku}_1.jpg")
            # save_as_jpg(main_zoom_resized, dest_zoom1, 2000, quality=92)
            # 
            # for s_idx, (img_file, slot_num) in enumerate(zoom_sequence):
            #     src_path = os.path.join(prod_path, img_file)
            #     dest_zoom = os.path.join(zoom_dir, f"{sku}_{s_idx + 2}.jpg")
            #     resized_img = crop_and_resize(src_path, target_size=2000, category=category, slot=slot_num, is_zoom=True)
            #     save_as_jpg(resized_img, dest_zoom, 2000, quality=92)
        except Exception as e:
            print(f"    ❌ Error processing images for SKU {sku}: {e}")
            
        processed_count += 1
        
    print("\n==================================================")
    print("          FTP STRUCTURE PACKAGING COMPLETED!      ")
    print("==================================================")
    print(f"📂 Output Staging folder: {FTP_UPLOAD_DIR}")
    print(f"  └─ /artiklar/      (Normal images, 1000px): {len(os.listdir(artiklar_dir)) - 1} files")
    print(f"  └─ /artiklar/liten/ (Small images, 400px):  {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (Zoom/Renders, 2000px): {len(os.listdir(zoom_dir))} files")
    print("--------------------------------------------------")
    print(f"✓ Products successfully processed & packaged: {processed_count}")
    print(f"✗ Products unmapped or skipped: {skipped_count}")
    print(f"ℹ Unmodified products skipped: {default_skipped_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
