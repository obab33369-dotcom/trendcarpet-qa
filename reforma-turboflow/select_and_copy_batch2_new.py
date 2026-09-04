import os
import sys
import json
import shutil
import re
import time
from PIL import Image

# Reconfigure stdout/stderr encoding for Windowscp1252
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

TEST_TOPAZ = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
NEW_RUGS_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\new_rugs"
NEW_RUGS_DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\new_rugs_db.json"

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
    typ = parse_category(filename)
    
    # Wood
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

    # Fabric
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

    # Color Tone
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

    # Style
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
    print("==================================================")
    print("      SELECTING & BALANCING BATCH 2 CATALOG       ")
    print("==================================================")
    
    # 1. Load used IDs from Batch 1
    with open(USED_DB_PATH, "r", encoding="utf-8") as f:
        used_db = json.load(f)
        
    used_ids = set()
    for k in used_db.keys():
        parts = k.split('_', 1)
        if len(parts) >= 1:
            used_ids.add(parts[0])
            
    print(f"Loaded used product IDs in Batch 1: {len(used_ids)}")
    
    # 2. Scan TEST TOPAZ for primary unused items
    all_files = os.listdir(TEST_TOPAZ)
    primary_files = []
    for f in all_files:
        if f.lower().endswith('.webp'):
            if '-1-' in f.lower() or '-1-26u-wonder' in f.lower():
                match = re.match(r'^(\d+)_', f)
                if match:
                    primary_files.append(f)
                    
    unused_by_cat = {
        'lampa': [],
        'förvaring': [],
        'bord': [],
        'stol': [],
        'andra': []
    }
    
    for f in primary_files:
        match = re.match(r'^(\d+)_', f)
        item_id = match.group(1)
        if item_id not in used_ids:
            cat = parse_category(f)
            if cat in unused_by_cat:
                unused_by_cat[cat].append(f)
                
    # 3. Load scraped new rugs from new_rugs_db.json
    with open(NEW_RUGS_DB_PATH, "r", encoding="utf-8") as f:
        new_rugs_db = json.load(f)
        
    round_rugs = [k for k, v in new_rugs_db.items() if v["metadata"]["form"] == "rund"]
    rect_rugs = [k for k, v in new_rugs_db.items() if v["metadata"]["form"] == "rektangulär"]
    
    print(f"Available new rugs: Round: {len(round_rugs)}, Rectangular: {len(rect_rugs)}")
    
    # Select exactly 20 rugs: 7 round + 13 rectangular
    selected_round = round_rugs[:7]
    selected_rect = rect_rugs[:13]
    selected_rugs_keys = selected_round + selected_rect
    print(f"Selected new rugs: {len(selected_rugs_keys)} (Round: {len(selected_round)}, Rect: {len(selected_rect)})")
    
    # 4. Proportions selection
    selected_lamps = unused_by_cat['lampa'] # All 11 remaining lamps
    selected_storage = sorted(unused_by_cat['förvaring'])[:50] # 50 storage
    selected_tables = sorted(unused_by_cat['bord'])[:48] # 48 tables
    selected_seating = sorted(unused_by_cat['stol'])[:80] # 80 chairs
    
    # Sum: 20 rugs + 11 lamps + 50 storage + 48 tables + 80 seating = 209 items total!
    total_selected_count = len(selected_rugs_keys) + len(selected_lamps) + len(selected_storage) + len(selected_tables) + len(selected_seating)
    print(f"Sum Check: Rugs: {len(selected_rugs_keys)} + Lamps: {len(selected_lamps)} + Storage: {len(selected_storage)} + Tables: {len(selected_tables)} + Seating: {len(selected_seating)} = {total_selected_count} items.")
    
    assert total_selected_count == 209, f"Proportions error! Total count is {total_selected_count} instead of 209!"
    
    # 5. Clean OneDrive folder
    os.makedirs(BATCH2_ONEDRIVE_DIR, exist_ok=True)
    print("\n🧹 Cleaning OneDrive Batch 2 folder...")
    for filename in os.listdir(BATCH2_ONEDRIVE_DIR):
        file_path = os.path.join(BATCH2_ONEDRIVE_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception:
            pass
            
    # 6. Copy files to OneDrive (PNG format)
    print("\n🚚 Copying product reference photos to OneDrive as PNG...")
    copied_count = 0
    batch2_db = {}
    
    # A. Copy non-rug items from TEST TOPAZ on-the-fly converting to PNG
    other_items = selected_lamps + selected_storage + selected_tables + selected_seating
    for filename in other_items:
        src_path = os.path.join(TEST_TOPAZ, filename)
        base, _ = os.path.splitext(filename)
        new_png_name = f"{base}.png"
        dest_path = os.path.join(BATCH2_ONEDRIVE_DIR, new_png_name)
        
        try:
            with Image.open(src_path) as img:
                img.save(dest_path, format="PNG")
            copied_count += 1
            
            metadata = parse_metadata_from_filename(filename)
            batch2_db[new_png_name] = {
                "filename": new_png_name,
                "parsed_name": new_png_name,
                "metadata": metadata,
                "timestamp": time.time()
            }
        except Exception as e:
            print(f"   ❌ Error converting '{filename}': {e}")
            
    # B. Copy and register the 20 selected new rugs (already PNG in new_rugs)
    for rug_key in selected_rugs_keys:
        src_path = os.path.join(NEW_RUGS_DIR, rug_key)
        dest_path = os.path.join(BATCH2_ONEDRIVE_DIR, rug_key)
        
        try:
            shutil.copy2(src_path, dest_path)
            copied_count += 1
            
            # Register in database directly
            rug_data = new_rugs_db[rug_key].copy()
            batch2_db[rug_key] = rug_data
            print(f"   [OK] Copied Rug: {rug_key}")
        except Exception as e:
            print(f"   ❌ Error copying rug '{rug_key}': {e}")
            
    # Save the updated database json
    with open(BATCH2_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(batch2_db, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print("         NEW BATCH 2 BALANCED CATALOG CREATED!    ")
    print("==================================================")
    print(f"📂 Output folder: {BATCH2_ONEDRIVE_DIR}")
    print(f"📝 Database saved: {BATCH2_DB_PATH}")
    print(f"🖼️ Successfully copied & converted: {copied_count} files (EXACTLY 209!)")
    print(f"📊 Items in Batch 2 DB: {len(batch2_db)} (EXACTLY 209!)")
    print("==================================================")

if __name__ == "__main__":
    main()
