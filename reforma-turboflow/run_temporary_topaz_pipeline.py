import os
import sys
import re
import shutil
import json
import urllib.request
import urllib.parse
import time
import numpy as np
from PIL import Image
from bs4 import BeautifulSoup

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "temporary-ftp-upload")
BRAND_DICT_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\brand_sku_dict.json"

# Fallback for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

# Stopwords for core word matching
STOPWORDS = {
    'stol', 'stolar', 'bord', 'borden', 'avlastningsbord', 'barstol', 'barstolar', 
    'hylla', 'hyllor', 'vagghylla', 'vagghyllor', 'vägghylla', 'vägghyllor', 
    'bokhylla', 'bokhyllor', 'soffbord', 'matbord', 'sangbord', 'sängbord', 
    'nattbord', 'konsolbord', 'skrivbord', 'byra', 'byrå', 'skap', 'skåp', 
    'skank', 'skänk', 'soffa', 'soffor', 'pall', 'pallar', 'sits', 'pack', 'set', 
    'lador', 'lådor', 'dörrar', 'dorrar', 'cm', 'x', 'natur', 'svart', 'vit', 
    'gra', 'grå', 'brun', 'beige', 'ek', 'valnot', 'valnöt', 'ask', 'tall', 
    'furu', 'laserad', 'lackad', 'metall', 'tra', 'trä', 'lullabies', '2-pack', 
    '3-pack', '4-pack', 'gron', 'grön', 'bla', 'blå', 'gul', 'rosa', 'rod', 'röd',
    'adventstjarna', 'adventstjärna', 'stjarna', 'stjärna'
}

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
    text = text.replace('3-sitss', '3-sits')
    text = text.replace('2-sitss', '2-sits')
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

def extract_core_words(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    words = re.findall(r'[a-z0-9]+', text)
    core = []
    for w in words:
        if w not in STOPWORDS and len(w) > 2 and not w.isdigit():
            core.append(w)
    return core

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

def is_white_background(img):
    is_wb, _ = is_white_background_robust(img)
    return is_wb

def classify_and_size_product(cat_name, folder_name):
    cat_lower = cat_name.lower()
    folder_lower = folder_name.lower()
    
    # 1. SOFA
    is_sofa = False
    if "sofa" in cat_lower or "soff" in cat_lower:
        if "soffbord" not in folder_lower and "soffbord" not in cat_lower:
            is_sofa = True
    elif ("soffa" in folder_lower or "sofa" in folder_lower or "schaslong" in folder_lower) and "soffbord" not in folder_lower:
        is_sofa = True
        
    if is_sofa:
        is_2_seat = any(x in folder_lower for x in ["2-sits", "2-seater", "2sits", "2seater", "loveseat", "love-seat", "baddfatolj", "bäddfåtölj"])
        if is_2_seat:
            return "sofa_2_seat", 0.76, 0.369, 0.1309, False
        else:
            return "sofa_3_seat", 0.86, 0.369, 0.1309, False

    # 2. CHAIRS, ARMCHAIRS, BARSTOOLS, STOOLS
    is_chair = "chair" in cat_lower or "stol" in cat_lower or "puff" in cat_lower or "pall" in cat_lower
    if any(x in folder_lower for x in ["stol", "karmstol", "pinnstol", "fatolj", "fåtölj", "armchair", "pall", "barstol", "puff", "sittpuff", "gungstol", "loungestol"]):
        is_chair = True
        
    if is_chair:
        if any(x in folder_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol"]) or any(x in cat_lower for x in ["fatolj", "fåtölj", "armchair", "gungstol", "loungestol", "lounge"]):
            return "armchair", 0.74, 0.65, 0.10, False
        elif "barstol" in folder_lower or "barstol" in cat_lower:
            return "barstool", 0.50, 0.75, 0.10, False
        elif any(x in folder_lower for x in ["pall", "puff", "sittpuff"]) or any(x in cat_lower for x in ["pall", "puff", "sittpuff"]):
            return "stool", 0.65, 0.65, 0.10, False
        else:
            return "chair_dining", 0.76, 0.68, 0.10, False

    # 3. TABLES
    is_table = "table" in cat_lower or "bord" in cat_lower
    if any(x in folder_lower for x in ["bord", "soffbord", "sidobord", "avlastningsbord", "skrivbord", "sangbord", "sängbord", "nattbord", "konsolbord", "barbord", "hjulbord", "matbord", "klaffbord", "slagbord"]):
        is_table = True
        
    if is_table:
        is_dining = any(x in folder_lower for x in ["matbord", "klaffbord", "slagbord", "180x", "120x", "160", "135", "115"])
        if is_dining:
            return "table_large", 0.82, 0.45, 0.113, False
        else:
            return "table_small", 0.685, 0.52, 0.113, False

    # 4. CABINETS
    is_cabinet = "cabinet" in cat_lower or "skap" in folder_lower or "skåp" in folder_lower or "byra" in folder_lower or "byrå" in folder_lower or "sideboard" in folder_lower or "skank" in folder_lower or "skänk" in folder_lower or "garderob" in folder_lower or "tv-bank" in folder_lower or "tv-bänk" in folder_lower
    if is_cabinet:
        is_large = any(x in folder_lower for x in ["garderob", "vitrinskap", "vitrinskåp", "kladhangare", "klädhängare", "kladstall", "klädställ"]) or ("skap" in folder_lower or "skåp" in folder_lower) and not any(x in folder_lower for x in ["sido", "litet", "byra", "byrå"])
        if is_large:
            return "cabinet_large", 0.60, 0.80, 0.10, False
        else:
            return "cabinet_small", 0.75, 0.55, 0.10, False

    # 5. SHELVES
    is_shelf = "shelf" in cat_lower or "hylla" in cat_lower or "hyllor" in cat_lower
    if is_shelf:
        is_wall = any(x in folder_lower for x in ["vagghylla", "vägghylla", "vagghyllor", "vägghyllor", "triangle", "mia", "net"])
        if is_wall:
            return "shelf_hanging", 0.60, 0.35, 0.50, True
        else:
            return "shelf_floor", 0.65, 0.75, 0.10, False

    # 6. LIGHTING
    is_lamp = "lamp" in cat_lower or "lampa" in cat_lower or "belysning" in cat_lower or "ljus" in cat_lower or "stjarna" in folder_lower or "stjärna" in folder_lower or "advent" in folder_lower
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

def process_image(img_path_or_bytes, category, target_w_fill, target_h_fill, floor_pct, is_centered, slot=1):
    if isinstance(img_path_or_bytes, Image.Image):
        img = img_path_or_bytes
    elif isinstance(img_path_or_bytes, bytes):
        import io
        img = Image.open(io.BytesIO(img_path_or_bytes))
    else:
        img = Image.open(img_path_or_bytes)
        
    img = load_and_ensure_size(img)
    w, h = img.size
    
    is_wb, bg_color = is_white_background_robust(img)
    
    bbox = None
    cleaned_shadow = img
    coords_body = None
    
    if is_wb and bg_color is not None:
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
            coords_body = np.argwhere(product_pixels_body)
            
            if coords_body.size > 0:
                y_min_clean = coords_body[:, 0].min() + 5
                y_max_clean = coords_body[:, 0].max() + 5
                x_min_clean = coords_body[:, 1].min() + 5
                x_max_clean = coords_body[:, 1].max() + 5
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
            # Main image (slot 1): custom category scaling and alignment
            # Find solid horizontal bounds from upper 60% of detected vertical height (excludes floor shadows)
            y_cutoff = y_min_clean + int(0.6 * (y_max_clean - y_min_clean))
            solid_coords = coords_body[coords_body[:, 0] <= (y_cutoff - 5)] if coords_body.size > 0 else np.array([])
            if solid_coords.size > 0:
                x_min_solid = solid_coords[:, 1].min() + 5
                x_max_solid = solid_coords[:, 1].max() + 5
            else:
                x_min_solid, x_max_solid = x_min_clean, x_max_clean
                
            # Determine product dimensions for scaling/centering
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
            
            # Constrain dimensions so the product fits on the canvas
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
                    
            # Resize cropped image
            new_w_crop = int((crop_x_max - crop_x_min) * scale)
            new_h_crop = int((crop_y_max - crop_y_min) * scale)
            cropped_resized = cropped.resize((new_w_crop, new_h_crop), RESAMPLING_METHOD)
            
            # Create white canvas
            canvas = Image.new("RGB", (2000, 2000), (255, 255, 255))
            
            # Target positions for body
            paste_x_body = (2000 - new_w_body) // 2
            if not is_centered:
                paste_y_body = int(2000 - (floor_pct * 2000) - new_h_body)
            else:
                paste_y_body = (2000 - new_h_body) // 2
                
            # Calculate paste offset for crop
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
    else:
        # Fallback if bbox is invalid (e.g., detail/lifestyle crop to centered square from original img directly)
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

def fetch_product_page_details(slug):
    url = f"https://www.reformasthlm.se/sv/{slug}"
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check brand
        keywords_tag = soup.find(name='meta', attrs={'name': 'keywords'})
        sku = None
        if keywords_tag:
            kw_parts = [p.strip() for p in keywords_tag.get('content', '').split(',')]
            if len(kw_parts) >= 3 and kw_parts[2].lower() == 'reforma':
                sku = kw_parts[1]
                
        if not sku:
            # Fallback 1: Check og:image meta tag
            og_image = soup.find(name='meta', attrs={'property': 'og:image'})
            if og_image:
                og_url = og_image.get('content', '')
                fn = og_url.split('?')[0].split('/')[-1]
                fn_clean = re.sub(r'_[S1-9]$', '', os.path.splitext(fn)[0])
                if fn_clean:
                    sku = fn_clean
                    
        if not sku:
            # Fallback 2: Check image tags
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if 'artiklar' in src:
                    fn = src.split('?')[0].split('/')[-1]
                    slot_match = re.search(r'_(\d+)\.[a-zA-Z]+$', fn)
                    if slot_match:
                        sku = fn[:slot_match.start()]
                        break
                        
        if not sku:
            return None
        
        # Gather all image gallery links
        image_urls = {}
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'artiklar' in src:
                # Find slot
                fn = src.split('?')[0].split('/')[-1]
                slot_match = re.search(r'_(\d+)\.[a-zA-Z]+$', fn)
                slot = int(slot_match.group(1)) if slot_match else 1
                
                # Strip parameters to get clean base path
                base_path = src.split('?')[0]
                if base_path.startswith('/img/'):
                    base_path = base_path[4:]
                if not base_path.startswith('/'):
                    base_path = '/' + base_path
                    
                full_res_url = f"https://www.reformasthlm.se/img{base_path}?w=2000"
                if slot not in image_urls:
                    image_urls[slot] = full_res_url
                    
        return sku, image_urls
    except Exception as e:
        # print(f"Error fetching page {url}: {e}")
        return None

def main():
    print("==================================================")
    print("   TEMPORARY TOPAZ REFORMA BRAND FTP PIPELINE     ")
    print("==================================================")
    
    # 1. Load active catalog
    print("Loading catalog brand dictionary...")
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
    db_norms = {normalize_name(k): (k, v) for k, v in brand_sku_dict.items()}

    # 2. Build exclusion indexes (SKUs and folder names)
    print("Building exclusion scope index...")
    excluded_norms = set()
    if os.path.exists(NEW_WHITE_BG_DIR):
        categories = [d for d in os.listdir(NEW_WHITE_BG_DIR) if os.path.isdir(os.path.join(NEW_WHITE_BG_DIR, d))]
        for cat in categories:
            cat_path = os.path.join(NEW_WHITE_BG_DIR, cat)
            if cat.lower() == "cabinet":
                nested_path = os.path.join(cat_path, "White background")
                if os.path.exists(nested_path) and os.path.isdir(nested_path):
                    cat_path = nested_path
            prods = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
            for p in prods:
                excluded_norms.add(normalize_name(p))
                
    excluded_skus = set()
    ftp_upload_dir_main = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload")
    ftp_upload_cropped_main = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped")
    for d in (ftp_upload_dir_main, ftp_upload_cropped_main):
        art_d = os.path.join(d, "artiklar")
        if os.path.exists(art_d):
            for filename in os.listdir(art_d):
                sku_candidate = os.path.splitext(filename)[0]
                sku_candidate = re.sub(r'_[S1-9]$', '', sku_candidate)
                excluded_skus.add(sku_candidate.lower())
                
    print(f"  Excluded product names: {len(excluded_norms)}")
    print(f"  Excluded SKUs: {len(excluded_skus)}")

    # 3. Scan local TEST TOPAZ files
    print("\nScanning local TEST TOPAZ directory...")
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
            
    print(f"  Total WebP files found: {len(topaz_files)}")
    print(f"  Unique products in Topaz: {len(topaz_products)}")
    
    # 4. Filter new products
    new_products = []
    for prod_name, files in sorted(topaz_products.items()):
        prod_lower = prod_name.lower()
        if any(x in prod_lower for x in ["matta", "mattor", "rug", "carpet"]):
            continue
        prod_norm = normalize_name(prod_name)
        
        is_dup = False
        if prod_norm in excluded_norms:
            is_dup = True
        else:
            for ex_norm in excluded_norms:
                if prod_norm == ex_norm or prod_norm in ex_norm or ex_norm in prod_norm:
                    is_dup = True
                    break
        if not is_dup:
            new_products.append(prod_name)
            
    print(f"  Products remaining after duplicate exclusions: {len(new_products)}")
    
    # 5. Output directories
    artiklar_dir = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    # Run Modes
    DRY_RUN = len(sys.argv) > 1 and sys.argv[1] == '--dry-run'
    if DRY_RUN:
        print("\n*** RUNNING IN DRY-RUN MODE (subset of 5 items) ***")
        new_products = new_products[:5]
    else:
        print("\nCleaning staging directory...")
        for d in (artiklar_dir, liten_dir, zoom_dir):
            if os.path.exists(d):
                for filename in os.listdir(d):
                    file_p = os.path.join(d, filename)
                    if os.path.isfile(file_p):
                        try:
                            os.unlink(file_p)
                        except Exception:
                            pass
            else:
                os.makedirs(d, exist_ok=True)

    processed_count = 0
    skipped_count = 0
    
    print("\nStarting crawler and composition pipeline...")
    
    for idx, prod_name in enumerate(new_products):
        print(f"\n[{idx+1}/{len(new_products)}] Processing: '{prod_name}'")
        prod_norm = normalize_name(prod_name)
        
        # 5.1. Resolve SKU and URL
        match_info = None
        if prod_norm in db_norms:
            match_info = db_norms[prod_norm]
        else:
            for db_norm, info in db_norms.items():
                if prod_norm in db_norm or db_norm in prod_norm:
                    match_info = info
                    break
                    
        # Core word match check
        if not match_info:
            core_words = extract_core_words(prod_name)
            if core_words:
                best_match = None
                best_score = 0
                for db_norm, info in db_norms.items():
                    db_key = info[0]
                    db_core = extract_core_words(db_key)
                    overlap = sum(1 for w in core_words if w in db_core)
                    if overlap > best_score:
                        best_score = overlap
                        best_match = info
                if best_score > 0 and best_match:
                    match_info = best_match
                    
        sku = None
        web_images = {}
        
        if match_info:
            sku = match_info[1]['sku']
            url = match_info[1]['url']
            print(f"  Mapped via DB: SKU: {sku} | URL: {url}")
            
            # Fast-check exclusion list before crawling
            if sku.lower() in excluded_skus:
                print(f"  Skipped: SKU {sku} is in the exclusion lists (fast check).")
                skipped_count += 1
                continue
                
            # Crawl page to get brand, SKU, and all images
            slug = url.split('/')[-1]
            page_details = fetch_product_page_details(slug)
            if page_details:
                sku, web_images = page_details
                print(f"    Dynamic crawler resolved: SKU: {sku} | Images found on page: {list(web_images.keys())}")
            else:
                print("    Skipped: Page crawl failed or product belongs to another brand.")
                skipped_count += 1
                continue
        else:
            # Try to resolve dynamically via URL
            print(f"  Attempting dynamic URL resolution for slug: {prod_name}")
            page_details = fetch_product_page_details(prod_name)
            if page_details:
                sku, web_images = page_details
                print(f"    Dynamic crawler resolved: SKU: {sku} | Images found on page: {list(web_images.keys())}")
            else:
                print("    Skipped: Mapped URL not found or product belongs to another brand.")
                skipped_count += 1
                continue

        # Double-check rug exclusion on resolved URL / name
        is_rug = False
        if match_info:
            db_key = match_info[0].lower()
            db_name = match_info[1].get('name', '').lower()
            db_url = match_info[1].get('url', '').lower()
            if any(x in db_key or x in db_name or x in db_url for x in ["matta", "mattor", "rug", "carpet"]):
                is_rug = True
        else:
            if any(x in prod_name.lower() for x in ["matta", "mattor", "rug", "carpet"]):
                is_rug = True
                
        if is_rug:
            print(f"  Skipped: Rug product '{prod_name}'")
            skipped_count += 1
            continue
            
        # Skip if resolved SKU is already excluded
        if sku.lower() in excluded_skus:
            print(f"  Skipped: SKU {sku} is in the exclusion lists.")
            skipped_count += 1
            continue
            
        # 5.2. Classify and compute target sizes
        category, target_w, target_h, floor_pct, is_centered = classify_and_size_product("default", prod_name)
        target_w, target_h = adjust_size_by_name(category, prod_name, target_w, target_h)
        print(f"  Classification: Category: {category} | Target Fill: W={target_w*100:.1f}%, H={target_h*100:.1f}% | Floor Line: {floor_pct*100:.2f}% | Centered: {is_centered}")

        # 5.3. Load/Download source images for all slots
        local_files = {slot: fn for slot, fn in topaz_products[prod_name]}
        slots_to_process = sorted(set(local_files.keys()) | set(web_images.keys()))
        
        processed_slots = {}
        
        for slot in slots_to_process:
            loaded_img = None
            if slot in local_files:
                # Load from local TEST TOPAZ
                local_path = os.path.join(TOPAZ_DIR, local_files[slot])
                try:
                    loaded_img = Image.open(local_path)
                    print(f"    Slot {slot}: Loaded locally from {local_files[slot]} (Size: {loaded_img.size})")
                except Exception as e:
                    print(f"    Slot {slot}: Error loading local file: {e}")
                    
            if loaded_img is None and slot in web_images:
                # Fallback: Scrape / Download from webpage
                remote_url = web_images[slot]
                print(f"    Slot {slot}: Downloading from webpage: {remote_url}...")
                try:
                    req_headers = {'User-Agent': 'Mozilla/5.0'}
                    req = urllib.request.Request(remote_url, headers=req_headers)
                    with urllib.request.urlopen(req, timeout=15) as res:
                        data = res.read()
                    import io
                    loaded_img = Image.open(io.BytesIO(data))
                    print(f"      Downloaded successfully! Size: {loaded_img.size}")
                except Exception as e:
                    print(f"      Download failed: {e}")
                    
            if loaded_img is not None:
                processed_slots[slot] = loaded_img
                
        if not processed_slots:
            print("  Skipped: No images could be loaded or downloaded.")
            skipped_count += 1
            continue
            
        # 5.4. Crop, align, resize and stage outputs
        # Select slot 1 (or the lowest available slot) as main image
        main_slot = 1 if 1 in processed_slots else min(processed_slots.keys())
        main_img = processed_slots[main_slot]
        
        # Classify if main is white background
        is_wb = is_white_background(load_and_ensure_size(main_img))
        
        # Staging lists
        white_bg_slots = {}
        interior_slots = {}
        
        for slot, img in sorted(processed_slots.items()):
            img_resized = load_and_ensure_size(img)
            if is_white_background(img_resized):
                white_bg_slots[slot] = img
            else:
                interior_slots[slot] = img
                
        # Main is always the primary white background slot
        main_img = None
        main_slot_num = 1
        if 1 in white_bg_slots:
            main_img = white_bg_slots[1]
            main_slot_num = 1
        elif white_bg_slots:
            main_slot_num = min(white_bg_slots.keys())
            main_img = white_bg_slots[main_slot_num]
            
        if main_img is None:
            # Fallback: if no white bg images found, use main interior image
            main_slot_num = main_slot
            main_img = processed_slots[main_slot_num]
            
        # Remaining zoom sequence: interior first, then remaining white bg
        zoom_sequence = []
        for slot in sorted(interior_slots.keys()):
            zoom_sequence.append((interior_slots[slot], slot))
        for slot in sorted(white_bg_slots.keys()):
            if white_bg_slots[slot] != main_img:
                zoom_sequence.append((white_bg_slots[slot], slot))
                
        # Process main normal & small
        try:
            main_canvas = process_image(main_img, category, target_w, target_h, floor_pct, is_centered, slot=1)
            
            if not DRY_RUN:
                save_as_jpg(main_canvas, os.path.join(artiklar_dir, f"{sku}.jpg"), 1000, quality=90)
                save_as_jpg(main_canvas, os.path.join(liten_dir, f"{sku}_S.jpg"), 400, quality=85)
                
                # Main zoom 1 and additional zooms bypassed per user request
                # save_as_jpg(main_canvas, os.path.join(zoom_dir, f"{sku}_1.jpg"), 2000, quality=92)
                # for s_idx, (z_img, z_slot) in enumerate(zoom_sequence):
                #     z_canvas = process_image(z_img, category, target_w, target_h, floor_pct, is_centered, slot=z_slot)
                #     save_as_jpg(z_canvas, os.path.join(zoom_dir, f"{sku}_{s_idx + 2}.jpg"), 2000, quality=92)
                    
            print(f"  Successfully processed main image (liten & normal) for SKU {sku}")
            processed_count += 1
        except Exception as e:
            print(f"  ❌ Error processing composition for SKU {sku}: {e}")
            skipped_count += 1
            
    print("\n==================================================")
    print("             PIPELINE RUN COMPLETED!              ")
    print("==================================================")
    if DRY_RUN:
        print("Dry-run execution completed. No files were written.")
    else:
        print(f"📂 Output Staging folder: {FTP_UPLOAD_DIR}")
        print(f"  └─ /artiklar/      (Normal images, 1000px): {len(os.listdir(artiklar_dir)) - 1} files")
        print(f"  └─ /artiklar/liten/ (Small images, 400px):  {len(os.listdir(liten_dir))} files")
        print(f"  └─ /artiklar/zoom/  (Zoom/Renders, 2000px): {len(os.listdir(zoom_dir))} files")
    print("--------------------------------------------------")
    print(f"✓ Products successfully processed & packaged: {processed_count}")
    print(f"✗ Products skipped or unmapped: {skipped_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
