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

BATCH2_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter"
SORTERAT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel"
UPSCALED_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\sorterat_efter_mobel_1x1_2000px"

METADATA_FILES = [
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow_batch2.json",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready_batch2.json",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready_batch2.csv",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_ready_batch2.txt",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\prompts_only_batch2.txt",
    r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\turboflow_tracking_log_batch2.csv"
]

def convert_images():
    print("==================================================")
    print("        CONVERTING WEBP IMAGES TO PNG             ")
    print("==================================================")
    
    # --- 1. Convert turboflow_batch2_produkter ---
    if os.path.exists(BATCH2_DIR):
        print(f"Scanning Batch 2 folder: {BATCH2_DIR}")
        files = [f for f in os.listdir(BATCH2_DIR) if f.lower().endswith(".webp")]
        print(f"Found {len(files)} webp files to convert to PNG...")
        
        converted_b2 = 0
        for f in files:
            src_path = os.path.join(BATCH2_DIR, f)
            dest_path = os.path.join(BATCH2_DIR, os.path.splitext(f)[0] + ".png")
            
            try:
                with Image.open(src_path) as img:
                    img.save(dest_path, format="PNG")
                os.remove(src_path)
                converted_b2 += 1
            except Exception as e:
                print(f"   Error converting {f}: {e}")
        print(f"Successfully converted and cleaned: {converted_b2} files.")
    else:
        print("Warning: Batch 2 folder not found.")
        
    # --- 2. Convert original references in sorterat_efter_mobel ---
    if os.path.exists(SORTERAT_DIR):
        print(f"\nScanning sorted folder: {SORTERAT_DIR}")
        categories = sorted([d for d in os.listdir(SORTERAT_DIR) if os.path.isdir(os.path.join(SORTERAT_DIR, d))])
        
        converted_sort = 0
        for cat in categories:
            cat_path = os.path.join(SORTERAT_DIR, cat)
            webps = [f for f in os.listdir(cat_path) if f.lower().endswith(".webp") and f.startswith("00_ORIGINAL_")]
            
            for f in webps:
                src_path = os.path.join(cat_path, f)
                dest_path = os.path.join(cat_path, os.path.splitext(f)[0] + ".png")
                try:
                    with Image.open(src_path) as img:
                        img.save(dest_path, format="PNG")
                    os.remove(src_path)
                    converted_sort += 1
                except Exception as e:
                    print(f"   Error converting '{f}' in '{cat}': {e}")
        print(f"Successfully converted and cleaned: {converted_sort} files.")
    else:
        print("Warning: Sorted folder not found.")

    # --- 3. Convert original references in sorterat_efter_mobel_1x1_2000px ---
    if os.path.exists(UPSCALED_DIR):
        print(f"\nScanning upscaled folder: {UPSCALED_DIR}")
        categories = sorted([d for d in os.listdir(UPSCALED_DIR) if os.path.isdir(os.path.join(UPSCALED_DIR, d))])
        
        converted_up = 0
        for cat in categories:
            cat_path = os.path.join(UPSCALED_DIR, cat)
            webps = [f for f in os.listdir(cat_path) if f.lower().endswith(".webp") and f.startswith("00_ORIGINAL_")]
            
            for f in webps:
                src_path = os.path.join(cat_path, f)
                dest_path = os.path.join(cat_path, os.path.splitext(f)[0] + ".png")
                try:
                    with Image.open(src_path) as img:
                        img.save(dest_path, format="PNG")
                    os.remove(src_path)
                    converted_up += 1
                except Exception as e:
                    print(f"   Error converting '{f}' in '{cat}': {e}")
        print(f"Successfully converted and cleaned: {converted_up} files.")
    else:
        print("Warning: Upscaled folder not found.")

    # --- 4. Update file extensions in metadata files ---
    print("\nUpdating webp references to png in Batch 2 metadata files...")
    updated_files = 0
    for path in METADATA_FILES:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Replace any instance of .webp with .png
                new_content = re.sub(r'\.webp\b', '.png', content)
                
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"   Updated file: {os.path.basename(path)}")
                updated_files += 1
            except Exception as e:
                print(f"   Error updating '{path}': {e}")
        else:
            print(f"   Warning: File not found: {path}")

    print("\n==================================================")
    print("             CONVERSION COMPLETED!                ")
    print("==================================================")
    print(f"Successfully converted all WebP reference files to PNG.")
    print(f"Metadata references updated: {updated_files} files.")
    print("==================================================")

if __name__ == "__main__":
    convert_images()
