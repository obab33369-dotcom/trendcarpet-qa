import os
import json
from PIL import Image

import sys

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

TEST_RUGS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_rugs"
BATCH2_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter"

DB1_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
DB2_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"

def add_rugs():
    print("==================================================")
    print("      ADDING DOWNLOADED RUGS TO BATCH 2           ")
    print("==================================================")
    
    # 1. Load databases
    with open(DB1_PATH, "r", encoding="utf-8") as f:
        db1 = json.load(f)
    with open(DB2_PATH, "r", encoding="utf-8") as f:
        db2 = json.load(f)
        
    print(f"Loaded Batch 1 DB with {len(db1)} items.")
    print(f"Loaded Batch 2 DB with {len(db2)} items.")
    
    # 2. Identify the 14 rugs in DB1
    rug_keys = [k for k in db1.keys() if k.startswith("20") and db1[k]["metadata"]["typ_av_möbel"] == "matta"]
    print(f"Found {len(rug_keys)} rugs in Batch 1 database to copy.")
    
    copied_count = 0
    added_to_db = 0
    
    # 3. Process each rug
    for key in rug_keys:
        src_path = os.path.join(TEST_RUGS_DIR, key)
        if not os.path.exists(src_path):
            print(f"[-] Rug file not found at {src_path}")
            continue
            
        # Define new filename with PNG extension
        base_name, _ = os.path.splitext(key)
        new_png_name = f"{base_name}.png"
        dest_path = os.path.join(BATCH2_DIR, new_png_name)
        
        # Convert and save as PNG
        try:
            with Image.open(src_path) as img:
                img.save(dest_path, format="PNG")
            copied_count += 1
            print(f"[OK] Converted and copied: {new_png_name}")
        except Exception as e:
            print(f"[ERROR] Failed to convert '{key}': {e}")
            continue
            
        # Copy metadata to Batch 2 DB
        rug_data = db1[key].copy()
        rug_data["filename"] = new_png_name
        rug_data["parsed_name"] = new_png_name
        
        db2[new_png_name] = rug_data
        added_to_db += 1
        
    # 4. Save updated Batch 2 DB
    with open(DB2_PATH, "w", encoding="utf-8") as f:
        json.dump(db2, f, ensure_ascii=False, indent=2)
        
    print("==================================================")
    print("               ADD RUGS COMPLETED!                ")
    print("==================================================")
    print(f"Rugs converted & copied: {copied_count}")
    print(f"Added to Batch 2 DB: {added_to_db}")
    print(f"Total items now in Batch 2 DB: {len(db2)}")
    print("==================================================")

if __name__ == "__main__":
    add_rugs()
