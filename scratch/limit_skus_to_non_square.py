import os
import json
import glob
from PIL import Image

COMPLETED_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\scratch\completed_skus.json"
BRAND_DICT_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\brand_sku_dict.json"
ART_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar"

def is_image_square(fpath):
    try:
        with Image.open(fpath) as img:
            w, h = img.size
            return w == h
    except Exception:
        return False

def main():
    if not os.path.exists(COMPLETED_PATH):
        print("completed_skus.json not found.")
        return
        
    with open(COMPLETED_PATH, 'r', encoding='utf-8') as f:
        completed = set(json.load(f))
        
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
        
    all_skus = [info['sku'].strip() for info in brand_sku_dict.values()]
    print(f"Total catalog SKUs: {len(all_skus)}")
    print(f"Currently marked completed: {len(completed)}")
    
    skus_to_skip = [] # skus that are already square and can be marked completed
    skus_to_process = [] # skus that have non-square images and must be reprocessed
    
    for sku in all_skus:
        sku_clean = sku.strip()
        if sku_clean in completed:
            continue
            
        # Find all output images for this SKU
        zoom_pattern = os.path.join(ART_DIR, "zoom", f"{sku_clean}_*.jpg")
        zoom_files = glob.glob(zoom_pattern)
        
        main_file = os.path.join(ART_DIR, f"{sku_clean}.jpg")
        liten_file = os.path.join(ART_DIR, "liten", f"{sku_clean}_S.jpg")
        
        all_outputs = []
        if os.path.exists(main_file):
            all_outputs.append(main_file)
        if os.path.exists(liten_file):
            all_outputs.append(liten_file)
        all_outputs.extend(zoom_files)
        
        if not all_outputs:
            # No outputs exist, must process
            skus_to_process.append(sku_clean)
            continue
            
        # Check if all outputs are square
        all_square = True
        for f in all_outputs:
            # Skip checking files that are explicitly detail/lifestyle if they are not meant to be square
            # But the user says "avgränsar detta jobb till de bilder som inte är fyrkantiga"
            # So if ANY output is not square, we reprocess.
            if not is_image_square(f):
                all_square = False
                break
                
        if all_square:
            skus_to_skip.append(sku_clean)
        else:
            skus_to_process.append(sku_clean)
            
    print(f"Found {len(skus_to_skip)} SKUs that are already square. Adding them back to completed.")
    print(f"Remaining SKUs to reprocess (have non-square images): {len(skus_to_process)}")
    
    if skus_to_skip:
        completed.update(skus_to_skip)
        with open(COMPLETED_PATH, 'w', encoding='utf-8') as f:
            json.dump(list(completed), f, indent=2)
        print("Successfully updated completed_skus.json.")
        
if __name__ == "__main__":
    main()
