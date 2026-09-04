import os
import sys
import re
import shutil
import json
from PIL import Image

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths
WORKSPACE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"

WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background-")
CABINET_BG_DIR = os.path.join(ONEDRIVE_DIR, "white back ground and fix 4 image cabinet", "White background")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload")

# Fallback for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

def get_beautiful_name(folder_name):
    # Strip numbers at beginning
    name = re.sub(r'^\d+\s*', '', folder_name)
    # Clean underscores and trim
    name = name.replace('_', ' ').replace('-', ' ').strip()
    # Collapse double spaces
    name = re.sub(r'\s+', ' ', name)
    return name

def crop_and_resize(img_path, target_size=2000):
    with Image.open(img_path) as img:
        width, height = img.size
        min_dim = min(width, height)
        
        # Centered crop
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        
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
    # Lowercase & replace swedish chars
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
        
    # Strip parentheses
    text = re.sub(r'\(.*?\)', '', text)
    # Strip category prefixes
    text = re.sub(r'^\d+\s*', '', text)
    
    # Text-level translation synoynms
    text = text.replace('sofa bed', 'baddsoffa')
    text = text.replace('bed sofa', 'baddsoffa')
    text = text.replace('bed armchair', 'baddfatolj')
    text = text.replace('sofabed', 'baddsoffa')
    text = text.replace('bedsofa', 'baddsoffa')
    text = text.replace('bedarmchair', 'baddfatolj')
    text = text.replace('seater sofa', 'sitssoffa')
    text = text.replace('seatersofa', 'sitssoffa')
    text = text.replace('sofa', 'soffa')  # standalone sofa -> soffa
    text = text.replace('module', 'modul')  # standalone module -> modul
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

# Hardcoded corrections for complex edge cases
hardcoded_map = {
    'barstoltarnsjsvart': 'barstoltarnsjobrun',  # Tärnsjö valnöt -> Tärnsjö svart
    'barstoltarnsjovalnot': 'barstoltarnsjosvart',  # Tärnsjö valnöt -> Tärnsjö svart
    'stolgalsvart': 'stolgalgrasvart',  # Gal Svart -> Gal Grå/Svart
    'karmstolrottingsvart': 'karmstolrottingblack',  # Rotting Svart -> Rotting Black
    'stolaltabeigevitpigmenterad': 'stolaltavitpigmenterad',  # Alta Beige/Vit -> Alta Vitpigmenterad
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
    # Cabinet Specific overrides
    'sideboardhagaviksvart': 'sideboardhagavik2sektionersvartmassing',
    'tvbankmyshultlnatur': 'tvbankmyshult200x55cmnatur',
    'tvbankmyshultsnatur': 'tvbankmyshult160x55cmnatur',
}

def is_processed_image(filename):
    fn_lower = filename.lower()
    if not fn_lower.endswith(('.jpg', '.jpeg', '.png')):
        return False
    # Avoid original raw files that have double index like -01-1 or -01-2
    if re.search(r'-\d+-\d+\.', fn_lower):
        return False
    return True

def extract_slot_number(filename, folder_name):
    fn_lower = filename.lower()
    
    # Try to find -(\d+)- or _(\d+)_ or -(\d+)_ or _(\d+)- or -(\d+).
    m = re.search(r'[-_](\d+)[-_]', fn_lower)
    if m:
        return int(m.group(1))
    
    # Fallback to any trailing number before extension
    m = re.search(r'[-_](\d+)\.[a-zA-Z]+$', fn_lower)
    if m:
        return int(m.group(1))
        
    return None

def main():
    print("==================================================")
    print("   UNIVERSAL EXCLUSIVE WHITE BG ASKÅS FTP PIPELINE")
    print("==================================================")
    
    # Validate directories
    if not os.path.exists(WHITE_BG_DIR):
        print(f"[ERROR] Renders directory not found: {WHITE_BG_DIR}")
        return
    if not os.path.exists(CABINET_BG_DIR):
        print(f"[ERROR] Cabinet renders directory not found: {CABINET_BG_DIR}")
        return
    if not os.path.exists(ORIG_DIR):
        print(f"[ERROR] Original product images directory not found: {ORIG_DIR}")
        return
        
    # Scan product folders in Refoma white background- (categorized)
    categories = [d for d in os.listdir(WHITE_BG_DIR) if os.path.isdir(os.path.join(WHITE_BG_DIR, d))]
    render_folders = []
    for cat in categories:
        cat_path = os.path.join(WHITE_BG_DIR, cat)
        prods = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
        for p in prods:
            render_folders.append((cat, p, os.path.join(cat_path, p)))
            
    print(f"[INFO] Found {len(render_folders)} product folders in {WHITE_BG_DIR}.")
    
    # Scan product folders in cabinet White background (uncategorized)
    cab_prods = [d for d in os.listdir(CABINET_BG_DIR) if os.path.isdir(os.path.join(CABINET_BG_DIR, d))]
    for p in cab_prods:
        render_folders.append(("cabinet", p, os.path.join(CABINET_BG_DIR, p)))
        
    print(f"[INFO] Total product folders to process (including {len(cab_prods)} cabinets): {len(render_folders)}.")
    
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
    unmapped_folders = []
    
    print("\n[STAGE 2] Processing and packaging products...")
    
    for idx, (cat, r_folder, prod_path) in enumerate(render_folders):
        r_norm = normalize_name(r_folder)
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
            # Word subset check fallback
            r_words = set(r_folder.lower().replace('_', ' ').replace('-', ' ').split())
            for o_folder in orig_folders:
                o_words = set(o_folder.lower().replace('_', ' ').replace('-', ' ').split())
                sig_r = {w for w in r_words if w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', '3', '2', 'pack', 'byra', 'skap', 'skänk', 'skank')}
                sig_o = {w for w in o_words if w not in ('stol', 'soffbord', 'bord', 'lampa', 'sofa', 'seater', '3', '2', 'pack', 'byra', 'skap', 'skänk', 'skank')}
                if sig_r and sig_o and sig_r == sig_o:
                    found_orig = o_folder
                    break
                    
        if not found_orig:
            print(f"✗ [{idx+1}/{len(render_folders)}] UNMAPPED: '{r_folder}' in category '{cat}'")
            unmapped_folders.append((cat, r_folder))
            skipped_count += 1
            continue
            
        # Extract SKU from the original folder's parenthesized suffix
        sku_match = re.search(r'\(([^)]+)\)', found_orig)
        if not sku_match:
            print(f"✗ [{idx+1}/{len(render_folders)}] NO SKU in original folder name: '{found_orig}'")
            unmapped_folders.append((cat, r_folder))
            skipped_count += 1
            continue
            
        sku = sku_match.group(1).strip()
        print(f"✓ [{idx+1}/{len(render_folders)}] MAPPED: '{r_folder}' -> SKU: '{sku}'")
        
        # Process product directory files
        files = [f for f in os.listdir(prod_path) if os.path.isfile(os.path.join(prod_path, f))]
        processed_files = [f for f in files if is_processed_image(f)]
        
        # Group by slot
        slots = {}
        for f in processed_files:
            slot = extract_slot_number(f, r_folder)
            if slot is not None:
                if slot not in slots:
                    slots[slot] = []
                slots[slot].append(f)
                
        # Deduplicate slots (favoring cropped 2000px JPEGs ending exactly in -W.jpg/jpeg or -V2.jpg/jpeg)
        selected_slots = {}
        for slot, candidates in slots.items():
            best_cand = candidates[0]
            best_score = -1
            for cand in candidates:
                cand_lower = cand.lower()
                score = 0
                if cand_lower.endswith(('-w.jpg', '-w.jpeg', '-v2.jpg', '-v2.jpeg', '-v2.png')):
                    score = 10
                elif cand_lower.endswith(('-wonder-w.jpg', '-wonder-w.jpeg')):
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
            selected_slots[slot] = best_cand
            
        sorted_slots = sorted(selected_slots.keys())
        if not sorted_slots:
            print(f"    ⚠️ Warning: No valid white background images found in folder!")
            skipped_count += 1
            continue
            
        # Package image slots
        for s_idx, slot in enumerate(sorted_slots):
            img_file = selected_slots[slot]
            src_path = os.path.join(prod_path, img_file)
            
            try:
                # 1:1 square crop & upscale in-memory
                resized_img = crop_and_resize(src_path, target_size=2000)
                
                # First slot in sorted list is Slot 1 (Main product view)
                if s_idx == 0:
                    # Save normal photo (1000px)
                    dest_normal = os.path.join(artiklar_dir, f"{sku}.jpg")
                    save_as_jpg(resized_img, dest_normal, 1000, quality=90)
                    
                    # Save liten photo (400px)
                    dest_liten = os.path.join(liten_dir, f"{sku}_S.jpg")
                    save_as_jpg(resized_img, dest_liten, 400, quality=85)
                    
                    # Save zoom photo 1 (2000px)
                    dest_zoom1 = os.path.join(zoom_dir, f"{sku}_1.jpg")
                    save_as_jpg(resized_img, dest_zoom1, 2000, quality=92)
                else:
                    # Additional views (Slot 2, 3, etc.)
                    # Preserve original slot numbers to replace them slot-for-slot on live
                    dest_zoom = os.path.join(zoom_dir, f"{sku}_{slot}.jpg")
                    save_as_jpg(resized_img, dest_zoom, 2000, quality=92)
            except Exception as e:
                print(f"    ❌ Error processing slot {slot} ('{img_file}'): {e}")
                
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
    print("==================================================")

if __name__ == "__main__":
    main()
