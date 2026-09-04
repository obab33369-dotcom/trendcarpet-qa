import os
import sys
import json
import shutil
import re
import time

# Configure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

TEST_TOPAZ = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
BATCH2_ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow_batch2_produkter"

USED_DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
BATCH2_DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"

def parse_category(fname):
    fname = fname.lower()
    if 'barstol' in fname:
        return 'stol'
    elif 'stol' in fname or 'fåtölj' in fname or 'soff' in fname or 'bänk' in fname or 'pall' in fname:
        return 'stol'
    elif 'soffbord' in fname or 'avlastningsbord' in fname or 'matbord' in fname or 'klaffbord' in fname or 'barbord' in fname or 'skrivbord' in fname or 'bord' in fname:
        return 'bord'
    elif 'matta' in fname:
        return 'matta'
    elif any(x in fname for x in ['bokhylla', 'skåp', 'byrå', 'hylla', 'tv-bänk', 'skänk', 'sideboard', 'mediabänk', 'garderob']):
        return 'förvaring'
    elif 'lampa' in fname:
        return 'lampa'
    else:
        return 'andra'

def parse_metadata_from_filename(filename: str) -> dict:
    fname = filename.lower()
    
    # 1. Category
    typ = parse_category(filename)

    # 2. Wood/Material
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

    # 3. Upholstery/Fabric
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

    # 4. Color Tone
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

    # 5. Aesthetic Style
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

def select_and_copy_batch2():
    print("==================================================")
    print("      SELECTING & COPYING BATCH 2 PRODUCTS        ")
    print("==================================================")
    
    if not os.path.exists(TEST_TOPAZ) or not os.path.exists(USED_DB_PATH):
        print("❌ Error: Missing master folder or Batch 1 database!")
        return

    # Load used products
    with open(USED_DB_PATH, "r", encoding="utf-8") as f:
        used_db = json.load(f)
        
    used_ids = set()
    for k in used_db.keys():
        parts = k.split('_', 1)
        if len(parts) >= 1:
            used_ids.add(parts[0])
            
    print(f"📦 Used product IDs in Batch 1: {len(used_ids)}")
    
    # Scan TEST TOPAZ for primary files
    all_files = os.listdir(TEST_TOPAZ)
    primary_files = []
    
    for f in all_files:
        if f.lower().endswith('.webp'):
            if '-1-' in f.lower() or '-1-26u-wonder' in f.lower():
                match = re.match(r'^(\d+)_', f)
                if match:
                    primary_files.append(f)
                    
    print(f"📂 Total primary files in master: {len(primary_files)}")
    
    # Filter unused files
    unused_by_cat = {
        'matta': [],
        'lampa': [],
        'förvaring': [],
        'bord': [],
        'stol': [],
        'andra': []
    }
    
    unused_count = 0
    for f in primary_files:
        match = re.match(r'^(\d+)_', f)
        item_id = match.group(1)
        if item_id not in used_ids:
            cat = parse_category(f)
            unused_by_cat[cat].append(f)
            unused_count += 1
            
    print(f"🔄 Total unused primary files: {unused_count}")
    for cat, lst in unused_by_cat.items():
        print(f"   • {cat.capitalize()}: {len(lst)} files")
        
    # Select exactly 209 items
    # 1. All 13 rugs
    selected_rugs = unused_by_cat['matta']
    # 2. All 11 lamps
    selected_lamps = unused_by_cat['lampa']
    # 3. All 55 storage units
    selected_storage = unused_by_cat['förvaring']
    
    # 4. We need to select 50 tables from 'bord' (out of 91 available)
    selected_tables = sorted(unused_by_cat['bord'])[:50]
    
    # 5. We need to select 80 chairs/sofas from 'stol' (out of 307 available)
    selected_seating = sorted(unused_by_cat['stol'])[:80]
    
    # Total selected = 13 + 11 + 55 + 50 + 80 = 209!
    selected_files = selected_rugs + selected_lamps + selected_storage + selected_tables + selected_seating
    print(f"\n🎯 Selected exactly {len(selected_files)} balanced items for Batch 2:")
    print(f"   • Rugs: {len(selected_rugs)}")
    print(f"   • Lamps: {len(selected_lamps)}")
    print(f"   • Storage: {len(selected_storage)}")
    print(f"   • Tables: {len(selected_tables)}")
    print(f"   • Seating: {len(selected_seating)}")
    
    # Copy selected files to OneDrive Batch 2 directory
    os.makedirs(BATCH2_ONEDRIVE_DIR, exist_ok=True)
    
    # Clean the OneDrive Batch 2 folder first to ensure a clean copy
    print("\n🧹 Cleaning destination OneDrive Batch 2 folder...")
    for filename in os.listdir(BATCH2_ONEDRIVE_DIR):
        file_path = os.path.join(BATCH2_ONEDRIVE_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            pass
            
    print("🚚 Copying product reference photos to OneDrive...")
    copied_count = 0
    batch2_db = {}
    
    for filename in selected_files:
        src_path = os.path.join(TEST_TOPAZ, filename)
        dest_path = os.path.join(BATCH2_ONEDRIVE_DIR, filename)
        
        try:
            shutil.copy2(src_path, dest_path)
            copied_count += 1
            
            # Parse metadata
            metadata = parse_metadata_from_filename(filename)
            
            batch2_db[filename] = {
                "filename": filename,
                "parsed_name": filename,
                "metadata": metadata,
                "timestamp": time.time()
            }
        except Exception as e:
            print(f"   ❌ Error copying '{filename}': {e}")
            
    # Save the new database json
    with open(BATCH2_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(batch2_db, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print("            BATCH 2 CATALOG CREATED!              ")
    print("==================================================")
    print(f"📂 Output folder: {BATCH2_ONEDRIVE_DIR}")
    print(f"📝 Database saved as: {BATCH2_DB_PATH}")
    print(f"🖼️ Successfully copied: {copied_count} product images")
    print("==================================================")

if __name__ == "__main__":
    select_and_copy_batch2()
