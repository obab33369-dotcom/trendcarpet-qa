import os
import sys
import json
import re
from PIL import Image

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Fallback for older Pillow versions
try:
    RESAMPLING_METHOD = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_METHOD = Image.ANTIALIAS

SKU_MAP_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\sku_map.json"
DEFAULT_INPUT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"
DEFAULT_STAGING_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload"

def get_beautiful_name(slug):
    words = slug.split('-')
    capitalized_words = []
    for w in words:
        if not w:
            continue
        w_lower = w.lower()
        if w_lower in ('m', 's', 'l'):
            capitalized_words.append(w.upper())
        elif w_lower == 'tv':
            capitalized_words.append('TV')
        elif 'x' in w_lower and re.match(r'^\d+x\d+', w_lower):
            capitalized_words.append(w_lower)
        else:
            capitalized_words.append(w.capitalize())
    return " ".join(capitalized_words)

def get_folder_name_from_db_key(key):
    parts = key.split('_', 1)
    if len(parts) >= 2:
        name_part = os.path.splitext(parts[1])[0]
        # Clean trailing Midjourney hashes
        clean_slug = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', name_part, flags=re.IGNORECASE)
        clean_slug = re.sub(r'-1-\w+-\w+$', '', clean_slug)
        clean_slug = re.sub(r'-\d+-\w+-\w+$', '', clean_slug)
        return get_beautiful_name(clean_slug)
    return None

def save_as_jpg(pil_img, dest_path, target_size, quality=90):
    """
    Safely resizes and saves a PIL Image as an RGB JPEG, handling transparency gracefully.
    """
    img_copy = pil_img.copy()
    
    # Handle transparency (RGBA mode or palette with transparency)
    if img_copy.mode in ('RGBA', 'LA') or (img_copy.mode == 'P' and 'transparency' in img_copy.info):
        # Create solid white background
        background = Image.new("RGB", img_copy.size, (255, 255, 255))
        # Paste using alpha channel as mask
        background.paste(img_copy, mask=img_copy.split()[3] if img_copy.mode == 'RGBA' else None)
        img_copy = background
    else:
        img_copy = img_copy.convert("RGB")
        
    # Resize if necessary
    if img_copy.size != (target_size, target_size):
        img_copy = img_copy.resize((target_size, target_size), RESAMPLING_METHOD)
        
    img_copy.save(dest_path, "JPEG", quality=quality)

def main():
    print("==================================================")
    print("    PREPARING RENDERS & PHOTOS FOR ASKÅS FTP      ")
    print("==================================================")
    
    # Path configuration
    input_dir = input(f"Input processed 1x1 folder [{DEFAULT_INPUT_DIR}]: ").strip() or DEFAULT_INPUT_DIR
    staging_dir = input(f"FTP Staging output folder [{DEFAULT_STAGING_DIR}]: ").strip() or DEFAULT_STAGING_DIR
    
    if not os.path.exists(SKU_MAP_PATH):
        print(f"❌ Error: SKU map not found at {SKU_MAP_PATH}!")
        return
    if not os.path.exists(input_dir):
        print(f"❌ Error: Input directory not found: {input_dir}")
        return
        
    # Create Askås compliant directory structure
    artiklar_dir = os.path.join(staging_dir, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    
    os.makedirs(artiklar_dir, exist_ok=True)
    os.makedirs(liten_dir, exist_ok=True)
    os.makedirs(zoom_dir, exist_ok=True)
    
    # Load SKU Map
    with open(SKU_MAP_PATH, "r", encoding="utf-8") as f:
        sku_map = json.load(f)
        
    print(f"Loaded {len(sku_map)} product SKU mappings.")
    print("Beginning structure packaging...\n")
    
    processed_count = 0
    missing_folders = 0
    error_count = 0
    
    for idx, (db_key, info) in enumerate(sku_map.items()):
        sku = info.get("sku")
        if not sku:
            continue
            
        beautiful_name = get_folder_name_from_db_key(db_key)
        product_folder = os.path.join(input_dir, beautiful_name)
        
        if not os.path.exists(product_folder):
            missing_folders += 1
            continue
            
        print(f"[{idx+1}/{len(sku_map)}] Staging product '{beautiful_name}' -> SKU: '{sku}'")
        
        try:
            # 1. Process ORIGINAL reference photo (Vanlig + Liten + Zoom)
            # Find the original photo inside the product folder (starts with '00_ORIGINAL_')
            original_file = None
            for f in os.listdir(product_folder):
                if f.startswith("00_ORIGINAL_") and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    original_file = f
                    break
                    
            if original_file:
                orig_path = os.path.join(product_folder, original_file)
                with Image.open(orig_path) as img:
                    # A. Normal image: /artiklar/SKU.jpg (1000 x 1000 px)
                    dest_normal = os.path.join(artiklar_dir, f"{sku}.jpg")
                    save_as_jpg(img, dest_normal, 1000, quality=90)
                    
                    # B. Liten image: /artiklar/liten/SKU_S.jpg (400 x 400 px)
                    dest_liten = os.path.join(liten_dir, f"{sku}_S.jpg")
                    save_as_jpg(img, dest_liten, 400, quality=85)
                    
                    # C. Zoom image 1: /artiklar/zoom/SKU_1.jpg (2000 x 2000 px)
                    dest_zoom1 = os.path.join(zoom_dir, f"{sku}_1.jpg")
                    save_as_jpg(img, dest_zoom1, 2000, quality=92)
            else:
                print(f"   ⚠️ Warning: 00_ORIGINAL reference photo not found in folder!")
                
            # 2. Process Shot 1 Render (Extrabild 2 -> zoom/SKU_2.jpg)
            # Find the render ending in '-a-IN.png'
            render_a = None
            for f in os.listdir(product_folder):
                if f.endswith("-a-IN.png") or f.endswith("-a-IN.jpg"):
                    render_a = f
                    break
            
            if render_a:
                render_a_path = os.path.join(product_folder, render_a)
                with Image.open(render_a_path) as img:
                    dest_zoom2 = os.path.join(zoom_dir, f"{sku}_2.jpg")
                    save_as_jpg(img, dest_zoom2, 2000, quality=92)
                    
            # 3. Process Shot 2 Render (Extrabild 3 -> zoom/SKU_3.jpg)
            # Find the render ending in '-b-IN.png'
            render_b = None
            for f in os.listdir(product_folder):
                if f.endswith("-b-IN.png") or f.endswith("-b-IN.jpg"):
                    render_b = f
                    break
                    
            if render_b:
                render_b_path = os.path.join(product_folder, render_b)
                with Image.open(render_b_path) as img:
                    dest_zoom3 = os.path.join(zoom_dir, f"{sku}_3.jpg")
                    save_as_jpg(img, dest_zoom3, 2000, quality=92)
                    
            processed_count += 1
            
        except Exception as e:
            print(f"   ❌ Error packaging product '{beautiful_name}': {e}")
            error_count += 1
            
    print("\n==================================================")
    print("              FTP PACKAGING COMPLETED!            ")
    print("==================================================")
    print(f"📂 Output Staging folder: {staging_dir}")
    print(f"  └─ /artiklar/      (Normal images, 1000px): {len(os.listdir(artiklar_dir)) - 1} files")
    print(f"  └─ /artiklar/liten/ (Small images, 400px):  {len(os.listdir(liten_dir))} files")
    print(f"  └─ /artiklar/zoom/  (Zoom/Renders, 2000px): {len(os.listdir(zoom_dir))} files")
    print("--------------------------------------------------")
    print(f"✓ Products successfully processed: {processed_count}")
    print(f"⚠️ Missing/Not yet processed folders: {missing_folders}")
    if error_count > 0:
        print(f"❌ Errors encountered: {error_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
