import os
import sys
import shutil
import re
from PIL import Image, ImageChops, ImageStat

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

THUMB_SIZE = (64, 64)
MAE_THRESHOLD = 20.0  # Difference threshold (0-255 grayscale difference levels)

# Paths configuration
DEFAULT_DOWNLOADS_DIR = r"C:\Users\AndronikLindgren\Downloads"
DEFAULT_RENDERS_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\26-05-27-p2"
DEFAULT_OUTPUT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\matched_1x1_renders"

def crop_center_square(img):
    """
    Crops a PIL image to a perfect 1:1 centered square.
    """
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) / 2
    top = (height - min_dim) / 2
    right = (width + min_dim) / 2
    bottom = (height + min_dim) / 2
    return img.crop((left, top, right, bottom))

def get_grayscale_thumbnail(img_path, crop_center=False):
    """
    Loads an image, optionally crops it, and returns a 64x64 grayscale thumbnail.
    """
    try:
        with Image.open(img_path) as img:
            if crop_center:
                img = crop_center_square(img)
            # Resize and convert to grayscale (L mode)
            thumb = img.resize(THUMB_SIZE, RESAMPLING_METHOD).convert('L')
            thumb.load()  # Force load pixel data into memory
            return thumb
    except Exception as e:
        print(f"Error loading image '{img_path}': {e}")
        return None

def calculate_mae(thumb1, thumb2):
    """
    Calculates the Mean Absolute Error (MAE) between two grayscale thumbnails.
    """
    diff = ImageChops.difference(thumb1, thumb2)
    stat = ImageStat.Stat(diff)
    return stat.mean[0]

def main():
    print("==================================================")
    print("       TURBOFLOW 1:1 CROP MATCHING & RENAMING     ")
    print("==================================================")
    
    # Prompt the user for custom directories (with easy defaults)
    downloads_dir = input(f"Downloaded 1:1 folder [{DEFAULT_DOWNLOADS_DIR}]: ").strip() or DEFAULT_DOWNLOADS_DIR
    renders_dir = input(f"Original 16:9 renders folder [{DEFAULT_RENDERS_DIR}]: ").strip() or DEFAULT_RENDERS_DIR
    output_dir = input(f"Output folder [{DEFAULT_OUTPUT_DIR}]: ").strip() or DEFAULT_OUTPUT_DIR
    
    # Path validation
    if not os.path.exists(downloads_dir):
        print(f"❌ Error: Downloads directory not found: {downloads_dir}")
        return
    if not os.path.exists(renders_dir):
        print(f"❌ Error: Original renders directory not found: {renders_dir}")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Pre-process and cache original 16:9 renders
    print("\n📂 Step 1: Scanning and caching original 16:9 renders...")
    candidate_files = [f for f in os.listdir(renders_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not candidate_files:
        print("❌ Error: No image files found in original renders directory!")
        return
        
    print(f"Found {len(candidate_files)} candidate renders. Pre-processing thumbnails...")
    candidates_cache = []
    
    for filename in candidate_files:
        path = os.path.join(renders_dir, filename)
        thumb = get_grayscale_thumbnail(path, crop_center=True)
        if thumb:
            candidates_cache.append({
                "filename": filename,
                "thumbnail": thumb
            })
            
    print(f"✓ Cached {len(candidates_cache)} candidate thumbnails in memory.")
    
    # 2. Process downloaded 1:1 files
    print("\n📂 Step 2: Scanning downloaded 1:1 files and matching...")
    download_files = [f for f in os.listdir(downloads_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not download_files:
        print("❌ Error: No image files found in downloads directory!")
        return
        
    print(f"Found {len(download_files)} unorganized images to match.")
    
    matched_count = 0
    unmatched_count = 0
    
    for idx, filename in enumerate(download_files):
        path = os.path.join(downloads_dir, filename)
        print(f"[{idx+1}/{len(download_files)}] Matching '{filename}'...", end="", flush=True)
        
        down_thumb = get_grayscale_thumbnail(path, crop_center=False)
        if not down_thumb:
            print(" [FAILED TO READ]")
            unmatched_count += 1
            continue
            
        best_match = None
        lowest_mae = float('inf')
        
        # Core comparison loop
        for cand in candidates_cache:
            mae = calculate_mae(down_thumb, cand["thumbnail"])
            if mae < lowest_mae:
                lowest_mae = mae
                best_match = cand
                
        # Check against MAE threshold
        if best_match and lowest_mae <= MAE_THRESHOLD:
            matched_filename = best_match["filename"]
            print(f" ✓ MATCHED to '{matched_filename}' (Diff score: {lowest_mae:.2f})")
            
            # Save matched 1:1 image with its correct filename in the output directory
            dest_path = os.path.join(output_dir, matched_filename)
            try:
                shutil.copy2(path, dest_path)
                matched_count += 1
            except Exception as e:
                print(f"\n  ❌ Error copying to '{dest_path}': {e}")
        else:
            if best_match:
                print(f" ⚠️ UNMATCHED (Best candidate: '{best_match['filename']}' but difference score too high: {lowest_mae:.2f})")
            else:
                print(" ⚠️ UNMATCHED (No candidates matched)")
            unmatched_count += 1
            
    print("\n==================================================")
    print("                MATCHING COMPLETED!               ")
    print("==================================================")
    print(f"📂 Matched Output directory: {output_dir}")
    print(f"✓ Successfully matched and renamed: {matched_count}")
    print(f"⚠️ Unmatched files: {unmatched_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
