import os
import sys
import json
import shutil
import re

# Configure standard streams to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
BRAND_DICT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\brand_sku_dict.json"
ORIG_IMAGES_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
TEST_TOPAZ_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"

def clean_str(s: str) -> str:
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
    for c, r in repl.items():
        s = s.replace(c, r)
    return s.lower()

def slugify(text):
    text = text.lower().strip()
    replacements = {
        'ö': 'o', 'ä': 'a', 'å': 'a',
        'Ö': 'O', 'Ä': 'A', 'Å': 'A'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    text = re.sub(r"['\"()åäöÅÄÖ]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip('-')
    return text

def parse_rug_metadata(name: str, index: int) -> dict:
    lower_name = name.lower()
    
    # 1. Form (Round vs Rectangular)
    if any(x in lower_name for x in ["rund", "cirkel", "cirkulär", "round", "runt"]):
        form = "rund"
    else:
        form = "rektangulär"
        
    # 2. Material
    if "jute" in lower_name:
        material = "jute"
    elif any(x in lower_name for x in ["ull", "wool"]):
        material = "ull"
    elif any(x in lower_name for x in ["bomull", "cotton", "trasmatta"]):
        material = "bomull"
    elif any(x in lower_name for x in ["viskos", "viscose"]):
        material = "viskos"
    elif "polyester" in lower_name:
        material = "polyester"
    elif "polypropen" in lower_name:
        material = "polypropen"
    elif "sammet" in lower_name:
        material = "sammet"
    else:
        material = "textil" # Default
        
    # 3. Color Tone (Warm vs Cool)
    cool_keywords = ["grå", "gra", "svart", "silver", "stål", "antracit", "charcoal", "blå", "bla", "grön", "gron", "kall"]
    if any(x in lower_name for x in cool_keywords):
        tone = "kall"
    else:
        tone = "varm" # Default to warm neutral
        
    # 4. Style Aesthetic
    styles = ["nordisk modern", "minimalistisk", "sekelskifte"]
    if any(x in lower_name for x in ["modern", "minimal", "clean"]):
        aesthetic = "minimalistisk"
    elif any(x in lower_name for x in ["klassisk", "sekelskifte", "traditionell"]):
        aesthetic = "sekelskifte"
    elif any(x in lower_name for x in ["rustik", "natur", "jute"]):
        aesthetic = "rustik"
    else:
        aesthetic = styles[index % len(styles)]
        
    return {
        "typ_av_möbel": "matta",
        "träslag": "inget",
        "tyg_material": material,
        "färgton": tone,
        "stil_estetik": aesthetic,
        "form": form
    }

def main():
    print("==================================================")
    print("      INTEGRATING ALL BRAND RUGS INTO BATCH 1     ")
    print("==================================================")
    
    # 1. Load active furniture database
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database file not found at {DB_PATH}.")
        sys.exit(1)
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
    print(f"Loaded existing database with {len(database)} items.")
    
    # 2. Clear out any old rug entries starting with 2001_ or containing category "matta"
    keys_to_delete = []
    for k, v in database.items():
        cat = v.get("metadata", {}).get("typ_av_möbel", "").strip().lower()
        if cat == "matta" or "matta" in k.lower():
            keys_to_delete.append(k)
            
    for k in keys_to_delete:
        del database[k]
    print(f"Cleared {len(keys_to_delete)} old rug entries from database.")
    
    # 3. Load 116 brand rugs from brand_sku_dict.json
    if not os.path.exists(BRAND_DICT_PATH):
        print(f"❌ Error: Brand dictionary not found at {BRAND_DICT_PATH}.")
        sys.exit(1)
        
    with open(BRAND_DICT_PATH, "r", encoding="utf-8") as f:
        brand_db = json.load(f)
        
    brand_rugs = {k: v for k, v in brand_db.items() if 'matta' in k.lower() or v['sku'].startswith('RG')}
    print(f"Loaded {len(brand_rugs)} rugs from brand dictionary.")
    
    # 4. Copy images and append rugs to database
    folders = os.listdir(ORIG_IMAGES_DIR)
    added_count = 0
    errors_count = 0
    
    # Sort keys to ensure deterministic processing
    sorted_rug_keys = sorted(brand_rugs.keys())
    
    for idx, key in enumerate(sorted_rug_keys):
        rug = brand_rugs[key]
        sku = rug["sku"]
        name = rug["name"]
        
        # Match folder in reforma_original_images_by_product
        folder_match = [f for f in folders if f"({sku})" in f or sku in f]
        if not folder_match:
            print(f"  ⚠️ Warning: No folder found for rug {name} ({sku})")
            errors_count += 1
            continue
            
        folder_name = folder_match[0]
        artiklar_dir = os.path.join(ORIG_IMAGES_DIR, folder_name, "artiklar")
        
        if not os.path.exists(artiklar_dir):
            print(f"  ⚠️ Warning: No 'artiklar' directory for rug {name} ({sku})")
            errors_count += 1
            continue
            
        art_files = os.listdir(artiklar_dir)
        img_match = [f for f in art_files if f.startswith(sku) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        
        if not img_match:
            print(f"  ⚠️ Warning: No image starting with SKU '{sku}' found in '{artiklar_dir}'")
            errors_count += 1
            continue
            
        src_img_filename = img_match[0]
        _, ext = os.path.splitext(src_img_filename)
        
        # Generate new filename for TEST TOPAZ
        id_num = 2001 + idx
        slug = slugify(key)
        new_filename = f"{id_num}_{slug}{ext}"
        
        # Copy to TEST TOPAZ
        src_path = os.path.join(artiklar_dir, src_img_filename)
        dest_path = os.path.join(TEST_TOPAZ_DIR, new_filename)
        
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            print(f"  ❌ Error copying {src_path} -> {dest_path}: {e}")
            errors_count += 1
            continue
            
        # Parse metadata
        meta = parse_rug_metadata(name, idx)
        
        # Save into database
        database[new_filename] = {
            "filename": new_filename,
            "parsed_name": name.replace("'", "").replace('"', ''),
            "metadata": meta
        }
        added_count += 1
        
    # Write updated database back to disk
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print("         INTEGRATION SUCCESSFULLY COMPLETED!      ")
    print("==================================================")
    print(f"📂 Total items in furniture_db.json: {len(database)}")
    print(f"🎨 Successfully copied and registered {added_count} rugs in database!")
    if errors_count > 0:
        print(f"⚠️ Errors/Warnings encountered: {errors_count}")
    print("==================================================")

if __name__ == "__main__":
    main()
