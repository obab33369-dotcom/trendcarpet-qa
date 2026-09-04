import os
import sys
import shutil
import json
import re
import time

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
TEST_FURNITURE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\test_furniture"
DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"

def parse_metadata_from_filename(filename: str) -> dict:
    fname = filename.lower()
    
    # 1. Category (typ_av_möbel)
    if 'barstol' in fname:
        typ = 'stol'
    elif 'stol' in fname or 'fåtölj' in fname or 'soff' in fname or 'bänk' in fname or 'pall' in fname:
        typ = 'stol'
    elif 'soffbord' in fname or 'avlastningsbord' in fname or 'matbord' in fname or 'klaffbord' in fname or 'barbord' in fname or 'skrivbord' in fname or 'bord' in fname:
        typ = 'bord'
    elif 'matta' in fname:
        typ = 'matta'
    elif any(x in fname for x in ['bokhylla', 'skåp', 'byrå', 'hylla', 'tv-bänk', 'skänk', 'sideboard', 'mediabänk', 'garderob']):
        typ = 'förvaring'
    else:
        if 'lampa' in fname:
            typ = 'bord' # Bordslampa is categorized as bord in database
        else:
            typ = 'förvaring'

    # 2. Wood/Material (träslag)
    if 'ek' in fname:
        wood = 'ek'
    elif 'valnöt' in fname or 'walnut' in fname:
        wood = 'valnöt'
    elif 'furu' in fname:
        wood = 'furu'
    elif 'ask' in fname:
        wood = 'ask'
    elif 'svart' in fname or 'metall' in fname or 'järn' in fname:
        wood = 'svart metall'
    elif 'marmor' in fname:
        wood = 'marmor'
    elif 'natur' in fname:
        wood = 'natur'
    elif 'vit' in fname:
        wood = 'vit'
    else:
        wood = 'inget'

    # 3. Upholstery/Fabric (tyg_material)
    if 'boucle' in fname or 'bouclé' in fname:
        fabric = 'bouclé'
    elif 'rotting' in fname:
        fabric = 'rotting'
    elif 'läder' in fname or 'skinn' in fname:
        fabric = 'läder'
    elif 'ull' in fname:
        fabric = 'ull'
    elif 'sammet' in fname:
        fabric = 'sammet'
    elif any(x in fname for x in ['beige', 'grå', 'tyg', 'textil', 'linne']):
        fabric = 'textil'
    else:
        fabric = 'inget'

    # 4. Color Tone (färgton)
    warm_keywords = ['beige', 'mässing', 'guld', 'brun', 'ek', 'valnöt', 'natur', 'trä', 'sand', 'creme', 'rustik']
    cool_keywords = ['svart', 'vit', 'grå', 'charcoal', 'stål', 'metall', 'järn', 'silver', 'antracit']
    
    warm_score = sum(1 for x in warm_keywords if x in fname)
    cool_score = sum(1 for x in cool_keywords if x in fname)
    
    if warm_score > cool_score:
        tone = 'varm'
    elif cool_score > warm_score:
        tone = 'kall'
    else:
        if wood in ['ek', 'valnöt', 'natur']:
            tone = 'varm'
        else:
            tone = 'kall'

    # 5. Aesthetic Style (stil_estetik)
    if 'rustik' in fname or 'industri' in fname or 'järn' in fname:
        style = 'rustik'
    elif 'klassisk' in fname or 'traditionell' in fname:
        style = 'klassisk'
    elif 'minimal' in fname or 'svart' in fname or 'stål' in fname:
        style = 'minimalistisk'
    else:
        style = 'nordisk modern'

    return {
        "typ_av_möbel": typ,
        "träslag": wood,
        "tyg_material": fabric,
        "färgton": tone,
        "stil_estetik": style
    }

def main():
    print(f"Scanning OneDrive folder: {ONEDRIVE_DIR}")
    if not os.path.exists(ONEDRIVE_DIR):
        print(f"Error: OneDrive folder not found at {ONEDRIVE_DIR}!")
        sys.exit(1)
        
    os.makedirs(TEST_FURNITURE_DIR, exist_ok=True)
    
    # Clean the local test_furniture folder first to build a clean set of all 734 primary items
    print("🧹 Cleaning local test_furniture folder...")
    for filename in os.listdir(TEST_FURNITURE_DIR):
        file_path = os.path.join(TEST_FURNITURE_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"⚠️ Failed to delete {file_path}. Reason: {e}")
            
    files = os.listdir(ONEDRIVE_DIR)
    primary_files = []
    for f in files:
        if f.lower().endswith('.webp'):
            if '-1-26u-wonder' in f.lower() or '-1-' in f.lower():
                match = re.match(r'^(\d+)_', f)
                if match:
                    item_id = int(match.group(1))
                    if 1 <= item_id <= 1324:
                        primary_files.append(f)
                
    print(f"Found {len(primary_files)} unique primary images in range 0001-1324 out of {len(files)} total files.")
    
    database = {}
    copied_count = 0
    
    print("\nCopying and parsing all 734 unique primary products...")
    for idx, filename in enumerate(primary_files):
        src_path = os.path.join(ONEDRIVE_DIR, filename)
        dest_path = os.path.join(TEST_FURNITURE_DIR, filename)
        
        # Copy to local test_furniture
        shutil.copy(src_path, dest_path)
        copied_count += 1
        
        # Parse metadata
        metadata = parse_metadata_from_filename(filename)
        
        database[filename] = {
            "filename": filename,
            "parsed_name": filename,
            "metadata": metadata,
            "timestamp": time.time()
        }
        
    # Write to furniture_db.json
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 SUCCESS!")
    print(f"Copied all {copied_count} unique primary three-quarter angle products to: {TEST_FURNITURE_DIR}")
    print(f"Rebuilt database {DB_PATH} with all {len(database)} unique catalog items!")

if __name__ == "__main__":
    main()
