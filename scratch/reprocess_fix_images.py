import os
import json
import shutil
import re

SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full"
TEST_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2"

targets = [
    '19005-m', '19744-c', '19791-black-oak', '19791-ek', '19791-walnut',
    '19791-white-oak-grey', '19791-white-oak', '19791', '19798-grey',
    '2372-walnut', '9971-oak', 'adst-beige', 'adst-brown', 'adst-white',
    'alm-3065', 'ww-advent-star-white-2'
]

def main():
    print("=== REPROCESSING ENVIRONMENT SETUP ===")
    
    # 1. Clear/Create test corrected directory structure
    if os.path.exists(TEST_DIR):
        print(f"Cleaning files in existing test directory: {TEST_DIR}")
        for root, dirs, files in os.walk(TEST_DIR, topdown=False):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                except Exception as e:
                    print(f"Failed to remove file {f}: {e}")
        
    os.makedirs(os.path.join(TEST_DIR, "artiklar"), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, "artiklar", "liten"), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, "artiklar", "zoom"), exist_ok=True)
    
    # 2. Copy review_status.json from original to test folder
    src_status = os.path.join(SRC_DIR, "review_status.json")
    dest_status = os.path.join(TEST_DIR, "review_status.json")
    if os.path.exists(src_status):
        shutil.copy2(src_status, dest_status)
        print("Copied review_status.json to test directory.")
        
        # Load and filter review_status.json to reset targeted SKUs
        with open(dest_status, 'r', encoding='utf-8') as f:
            status_db = json.load(f)
            
        initial_count = len(status_db)
        keys_to_delete = []
        for key in status_db.keys():
            # key is like "artiklar/2372-walnut.jpg" or "zoom/2372-walnut_4.jpg"
            fn = os.path.basename(key).lower()
            for t in targets:
                # Check if it starts with the target name followed by _ or .
                if fn.startswith(t + '.') or fn.startswith(t + '_'):
                    keys_to_delete.append(key)
                    break
                    
        for key in keys_to_delete:
            del status_db[key]
            
        print(f"Deleted {len(keys_to_delete)} keys in review_status.json to reset their status.")
        with open(dest_status, 'w', encoding='utf-8') as f:
            json.dump(status_db, f, indent=2)
    else:
        print("review_status.json not found in original directory, creating empty one.")
        with open(dest_status, 'w', encoding='utf-8') as f:
            json.dump({}, f)
            
    # 3. Copy files for target SKUs from original to test folder
    # Main images
    main_src = os.path.join(SRC_DIR, "artiklar")
    main_dest = os.path.join(TEST_DIR, "artiklar")
    for f in os.listdir(main_src):
        if os.path.isfile(os.path.join(main_src, f)):
            fn = f.lower()
            for t in targets:
                if fn.startswith(t + '.'):
                    shutil.copy2(os.path.join(main_src, f), os.path.join(main_dest, f))
                    print(f"Copied main image: {f}")
                    break
                    
    # Liten images
    liten_src = os.path.join(main_src, "liten")
    liten_dest = os.path.join(main_dest, "liten")
    if os.path.exists(liten_src):
        for f in os.listdir(liten_src):
            fn = f.lower()
            for t in targets:
                if fn.startswith(t + '_s.'):
                    shutil.copy2(os.path.join(liten_src, f), os.path.join(liten_dest, f))
                    print(f"Copied liten image: {f}")
                    break
                
    # Zoom images
    zoom_src = os.path.join(main_src, "zoom")
    zoom_dest = os.path.join(main_dest, "zoom")
    if os.path.exists(zoom_src):
        for f in os.listdir(zoom_src):
            fn = f.lower()
            for t in targets:
                if fn.startswith(t + '_'):
                    shutil.copy2(os.path.join(zoom_src, f), os.path.join(zoom_dest, f))
                    print(f"Copied zoom image: {f}")
                    break
                
    print("\nEnvironment setup complete. You can now run the corrector script.")

if __name__ == "__main__":
    main()
