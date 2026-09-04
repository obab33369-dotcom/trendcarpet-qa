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
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "chairs_cropped2")

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
    
    # Dining chairs only (Excluding armchairs, stools, and barstools)
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
        
    return "default"

def crop_and_resize(img_path, target_size=2000, is_zoom=False):
    with Image.open(img_path) as img:
        width, height = img.size
        min_dim = min(width, height)
        
        is_wb = is_white_background(img_path)
        
        bbox = None
        if is_wb:
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                gray = bg.convert("L")
            else:
                gray = img.convert("L")
                
            arr = np.array(gray)
            non_white_coords = np.argwhere(arr < 250)
            if non_white_coords.size > 0:
                y_min, x_min = non_white_coords.min(axis=0)
                y_max, x_max = non_white_coords.max(axis=0)
                if (x_max - x_min > 5) and (y_max - y_min > 5):
                    bbox = (x_min, y_min, x_max, y_max)
                    
        center_x = width / 2
        center_y = height / 2
        
        if bbox is not None:
            x_min, y_min, x_max, y_max = bbox
            
            # Compute minimum S required to fit the product centered on the image center
            def get_min_centered_size(margin):
                dx = max(abs(center_x - x_min), abs(x_max - center_x))
                dy = max(abs(center_y - y_min), abs(y_max - center_y))
                return 2 * max(dx, dy) + 2 * margin
            
            if is_zoom:
                # Zoom (2000px): Make 15% bigger. S = 0.90 / 1.15 = 0.783
                S = 0.783 * min_dim
                S_min_5 = get_min_centered_size(5)
                if S < S_min_5:
                    S = S_min_5
                S = min(S, min_dim)
            else:
                # Normal & Small (1000px & 400px): Make 20% bigger. S = 0.87 / 1.20 = 0.725
                S = 0.725 * min_dim
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
        
        # Ensure coordinates are within image boundaries
        left = max(0.0, left)
        top = max(0.0, top)
        right = min(float(width), right)
        bottom = min(float(height), bottom)
        
        cropped = img.crop((left, top, right, bottom))
        resized = cropped.resize((target_size, target_size), RESAMPLING_METHOD)
        return resized

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
        
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'^\d+\s*', '', text)
    
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
    
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

# Hardcoded maps (same as main script)
hardcoded_map = {
    'barstoltarnsjsvart': 'barstoltarnsjobrun',
    'barstoltarnsjovalnot': 'barstoltarnsjosvart',
    'stolgalsvart': 'stolgalgrasvart',
    'karmstolrottingsvart': 'karmstolrottingblack',
    'stolaltabeigevitpigmenterad': 'stolaltavitpigmenterad',
    'stolangomljusbeige': 'stolangombeige',
}

hardcoded_sku_map = {
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

def is_white_background(img_path):
    try:
        with Image.open(img_path) as img:
            img_rgb = img.convert('RGB')
            arr = np.array(img_rgb)
            h, w, _ = arr.shape
            border_pixels = []
            border_pixels.extend(arr[0:5, :, :].reshape(-1, 3))
            border_pixels.extend(arr[-5:, :, :].reshape(-1, 3))
            border_pixels.extend(arr[5:-5, 0:5, :].reshape(-1, 3))
            border_pixels.extend(arr[5:-5, -5:, :].reshape(-1, 3))
            mean_val = np.mean(border_pixels)
            return mean_val > 245
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
    print("   CHAIRS CROPPED2 FTP STAGING PIPELINE")
    print("==================================================")
    
    if not os.path.exists(NEW_WHITE_BG_DIR):
        print(f"[ERROR] Renders directory not found: {NEW_WHITE_BG_DIR}")
        return
    if not os.path.exists(ORIG_DIR):
        print(f"[ERROR] Original product images directory not found: {ORIG_DIR}")
        return
        
    # Scan all product folders
    categories = [d for d in os.listdir(NEW_WHITE_BG_DIR) if os.path.isdir(os.path.join(NEW_WHITE_BG_DIR, d))]
    render_folders = []
    for cat in categories:
        cat_path = os.path.join(NEW_WHITE_BG_DIR, cat)
        if cat.lower() == "cabinet":
            nested_path = os.path.join(cat_path, "White background")
            if os.path.exists(nested_path) and os.path.isdir(nested_path):
                cat_path = nested_path
                
        prods = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
        for p in prods:
            render_folders.append((cat, p, os.path.join(cat_path, p)))
            
    print(f"[INFO] Found {len(render_folders)} total product folders to classify.")
    
    # List original folders (used solely for SKU resolution)
    orig_folders = [d for d in os.listdir(ORIG_DIR) if os.path.isdir(os.path.join(ORIG_DIR, d))]
    
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
    
    print("\n[STAGE 2] Processing and packaging chairs...")
    
    for idx, (cat, r_folder, prod_path) in enumerate(render_folders):
        category = classify_folder(cat, r_folder)
        if category != "chair_armchair":
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
                skipped_count += 1
                continue
                
            sku_match = re.search(r'\(([^)]+)\)', found_orig)
            if not sku_match:
                print(f"✗ [{idx+1}/{len(render_folders)}] NO SKU in original folder name: '{found_orig}'")
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
        if 1 in selected_white_bg:
            main_img = selected_white_bg[1]
        elif selected_white_bg:
            main_img = selected_white_bg[min(selected_white_bg.keys())]
            
        if not main_img:
            print(f"    ⚠️ Warning: No valid white background images found in folder!")
            skipped_count += 1
            continue
            
        # Build zoom sequence: interior first, then remaining white bg
        zoom_sequence = []
        for slot in sorted(selected_interior.keys()):
            zoom_sequence.append(selected_interior[slot])
        for slot in sorted(selected_white_bg.keys()):
            f = selected_white_bg[slot]
            if f != main_img:
                zoom_sequence.append(f)
                
        try:
            # 1000px / 400px: 20% bigger
            main_normal_resized = crop_and_resize(os.path.join(prod_path, main_img), target_size=1000, is_zoom=False)
            
            dest_normal = os.path.join(artiklar_dir, f"{sku}.jpg")
            save_as_jpg(main_normal_resized, dest_normal, 1000, quality=90)
            
            dest_liten = os.path.join(liten_dir, f"{sku}_S.jpg")
            save_as_jpg(main_normal_resized, dest_liten, 400, quality=85)
            
            # 2000px: 15% bigger
            main_zoom_resized = crop_and_resize(os.path.join(prod_path, main_img), target_size=2000, is_zoom=True)
            dest_zoom1 = os.path.join(zoom_dir, f"{sku}_1.jpg")
            save_as_jpg(main_zoom_resized, dest_zoom1, 2000, quality=92)
            
            for s_idx, img_file in enumerate(zoom_sequence):
                src_path = os.path.join(prod_path, img_file)
                dest_zoom = os.path.join(zoom_dir, f"{sku}_{s_idx + 2}.jpg")
                resized_img = crop_and_resize(src_path, target_size=2000, is_zoom=True)
                save_as_jpg(resized_img, dest_zoom, 2000, quality=92)
        except Exception as e:
            print(f"    ❌ Error processing images for SKU {sku}: {e}")
            
        processed_count += 1
        
    print("\n==================================================")
    print("          CHAIRS CROPPED2 PIPELINE COMPLETED!     ")
    print("==================================================")
    print(f"📂 Output Staging folder: {FTP_UPLOAD_DIR}")
    print(f"  └─ /artiklar/      (Normal images, 1000px): {len(os.listdir(artiklar_dir)) - 1} files")
    print(f"  └─ /artiklar/liten/ (Small images, 400px):  {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (Zoom/Renders, 2000px): {len(os.listdir(zoom_dir))} files")
    print("--------------------------------------------------")
    print(f"✓ Chairs successfully processed: {processed_count}")
    print(f"✗ Chairs unmapped or skipped: {skipped_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
