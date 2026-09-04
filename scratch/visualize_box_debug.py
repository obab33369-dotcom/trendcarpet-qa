import os
import json
import re
from PIL import Image, ImageDraw

REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
FTP_UPLOAD_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3"
INPUT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images"
STATUS_FILE = os.path.join(FTP_UPLOAD_DIR, "review_status.json")
ARTIFACTS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\9a89adb6-c2a2-4ca2-a186-3ca3c4d5681e"

def normalize_name(name):
    text = name.lower()
    text = re.sub(r'^\s*\d+\s*', '', text)
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def main():
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        status_db = {k.lower(): v for k, v in json.load(f).items()}
        
    skus_to_check = ["107313.jpg", "108458.jpg", "101176.jpg", "85624.jpg", "81534.jpg"]
    
    for fn in skus_to_check:
        db_key = f"artiklar/{fn.lower()}"
        if db_key not in status_db:
            print(f"Skipping {fn}, not in DB.")
            continue
            
        entry = status_db[db_key]
        status = entry.get("status")
        original_bbox = entry.get("original_bbox") or entry.get("bbox")
        category = entry.get("category", "default")
        
        if not original_bbox:
            print(f"Skipping {fn}, no bbox.")
            continue
            
        # Draw on corrected image
        corrected_path = os.path.join(FTP_UPLOAD_DIR, "artiklar", fn)
        if os.path.exists(corrected_path):
            with Image.open(corrected_path) as img:
                img = img.convert('RGB')
                # Save a copy to artifacts
                img.save(os.path.join(ARTIFACTS_DIR, f"{fn[:-4]}_corrected.jpg"))
                print(f"Saved corrected image copy for {fn}")
        else:
            print(f"Corrected image for {fn} not found.")

if __name__ == "__main__":
    main()
