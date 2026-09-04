import os
import sys
import re
from PIL import Image

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel"
DEST_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"

# Determine safe Pillow filter based on version
if hasattr(Image, 'Resampling'):
    LANCZOS_FILTER = Image.Resampling.LANCZOS
elif hasattr(Image, 'LANCZOS'):
    LANCZOS_FILTER = Image.LANCZOS
else:
    LANCZOS_FILTER = Image.ANTIALIAS

def crop_and_upscale_images():
    print("==================================================")
    print("     STARTING IMAGE 1:1 CROPPER & 2000PX UPSCALER  ")
    print("==================================================")
    
    if not os.path.exists(SRC_DIR):
        print(f"❌ Error: Source directory not found: {SRC_DIR}")
        return
        
    os.makedirs(DEST_DIR, exist_ok=True)
    
    # Scan source directory structure
    categories = sorted([d for d in os.listdir(SRC_DIR) if os.path.isdir(os.path.join(SRC_DIR, d))])
    print(f"📂 Found {len(categories)} unique product folders in source.")
    
    total_processed = 0
    total_errors = 0
    
    for idx, cat in enumerate(categories, 1):
        src_cat_path = os.path.join(SRC_DIR, cat)
        dest_cat_path = os.path.join(DEST_DIR, cat)
        
        files = sorted([f for f in os.listdir(src_cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        if not files:
            continue
            
        os.makedirs(dest_cat_path, exist_ok=True)
        
        print(f"📦 [{idx}/{len(categories)}] Processing '{cat}' ({len(files)} files)...")
        
        for f in files:
            src_file_path = os.path.join(src_cat_path, f)
            dest_file_path = os.path.join(dest_cat_path, f)
            
            try:
                with Image.open(src_file_path) as img:
                    width, height = img.size
                    
                    # 1. Perform high-quality Center Crop to 1:1
                    min_dim = min(width, height)
                    left = (width - min_dim) / 2
                    top = (height - min_dim) / 2
                    right = (width + min_dim) / 2
                    bottom = (height + min_dim) / 2
                    
                    cropped_img = img.crop((left, top, right, bottom))
                    
                    # 2. Upscale to exactly 2000x2000 pixels using LANCZOS filter
                    upscaled_img = cropped_img.resize((2000, 2000), LANCZOS_FILTER)
                    
                    # 3. Save keeping original format/parameters
                    # Preserve format (PNG, JPEG, WEBP)
                    img_format = img.format if img.format else "PNG"
                    
                    if img_format == "JPEG":
                        upscaled_img.save(dest_file_path, format=img_format, quality=95, subsampling=0)
                    elif img_format == "WEBP":
                        upscaled_img.save(dest_file_path, format=img_format, quality=95)
                    else:
                        upscaled_img.save(dest_file_path, format=img_format)
                        
                total_processed += 1
            except Exception as e:
                print(f"   ❌ Error processing file '{f}': {e}")
                total_errors += 1
                
    print("\n==================================================")
    print("              PROCESSING COMPLETED!               ")
    print("==================================================")
    print(f"📂 Output folder: {DEST_DIR}")
    print(f"🖼️ Successfully cropped & upscaled to 2000x2000px: {total_processed} files")
    if total_errors > 0:
        print(f"⚠️ Errors encountered: {total_errors}")
    print("==================================================")

if __name__ == "__main__":
    crop_and_upscale_images()
