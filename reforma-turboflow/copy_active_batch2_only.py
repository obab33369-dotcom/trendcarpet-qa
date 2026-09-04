import os
import shutil
import sys
import json

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"
SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter"
DEST_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter_aktiva"

def clean_str(s: str) -> str:
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
    for c, r in repl.items():
        s = s.replace(c, r)
    return s.lower()

def should_skip_item(filename: str) -> bool:
    fname = filename.lower()
    skip_keywords = ["hylla", "hyllor", "bokhylla", "bokhyllor", "vägghylla", "vägghyllor", "klädhängare", "skåp", "väggspegel", "väggspeglar", "bokhylloiw"]
    cleaned_fname = clean_str(fname)
    for kw in skip_keywords:
        if kw in fname or clean_str(kw) in cleaned_fname:
            return True
    return False

def main():
    print("==================================================")
    print("      EXPORTING ACTIVE BATCH 2 PRODUCT IMAGES    ")
    print("==================================================")
    
    # 1. Load Batch 2 DB
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}.")
        sys.exit(1)
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    # 2. Get active keys
    active_filenames = []
    skipped_count = 0
    for k in db.keys():
        if should_skip_item(k):
            skipped_count += 1
            continue
        active_filenames.append(k)
        
    print(f"Total items in DB: {len(db)}")
    print(f"Filtered out (skipped shelves/wardrobes/mirrors): {skipped_count}")
    print(f"Active items to export: {len(active_filenames)} (Expected: 173)")
    
    # 3. Create destination folder
    print(f"\n📂 Creating/cleaning target folder: {DEST_DIR}")
    os.makedirs(DEST_DIR, exist_ok=True)
    for filename in os.listdir(DEST_DIR):
        file_path = os.path.join(DEST_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"⚠️ Failed to delete {file_path}. Reason: {e}")
            
    # 4. Copy files from source directory
    if not os.path.exists(SRC_DIR):
        print(f"Error: Source images directory not found at {SRC_DIR}.")
        sys.exit(1)
        
    copied_count = 0
    missing_count = 0
    
    for filename in active_filenames:
        src_path = os.path.join(SRC_DIR, filename)
        dest_path = os.path.join(DEST_DIR, filename)
        
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, dest_path)
                copied_count += 1
            except Exception as e:
                print(f"❌ Failed to copy '{filename}': {e}")
        else:
            # Try to see if it exists with a webp or png mismatch extension
            # (though B2 DB items should be exactly matching)
            print(f"⚠️ File missing in source: {filename}")
            missing_count += 1
            
    print("\n==================================================")
    print("         EXPORT COMPLETE!                         ")
    print("==================================================")
    print(f"📂 Source folder: {SRC_DIR}")
    print(f"📂 Active target folder: {DEST_DIR}")
    print(f"🖼️ Successfully copied: {copied_count} of {len(active_filenames)} active files")
    if missing_count > 0:
        print(f"⚠️ Missing files in source folder: {missing_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
