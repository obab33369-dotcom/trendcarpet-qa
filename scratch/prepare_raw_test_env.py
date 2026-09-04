import os
import json
import shutil
import re

NEW_WHITE_BG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"
TOPAZ_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
ORIG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"
SRC_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full"
TEST_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images"
BRAND_DICT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\brand_sku_dict.json"
FTP_UPLOAD_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2"

targets = [
    '19005-m', '19744-c', '19791-black-oak', '19791-ek', '19791-walnut',
    '19791-white-oak-grey', '19791-white-oak', '19791', '19798-grey',
    '2372-walnut', '9971-oak', 'adst-beige', 'adst-brown', 'adst-white',
    'alm-3065', 'ww-advent-star-white-2'
]

def normalize_name(name):
    text = name.lower()
    # Strip leading numbers/spaces (e.g. "6 Stol _Ystad_..." -> "Stol _Ystad_...")
    text = re.sub(r'^\s*\d+\s*', '', text)
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def find_raw_original(sku, prod_name, slot=1):
    prod_norm = normalize_name(prod_name)
    sku_clean = sku.strip().lower()
    
    # Check if the product has a folder in Refoma white background fix
    has_wb_fix_folder = False
    if os.path.exists(NEW_WHITE_BG_DIR):
        for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
            for d in dirs:
                if normalize_name(d) == prod_norm:
                    has_wb_fix_folder = True
                    break
            if has_wb_fix_folder:
                break
                
    # 1. Look in Refoma white background fix
    if os.path.exists(NEW_WHITE_BG_DIR):
        for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
            for d in dirs:
                if normalize_name(d) == prod_norm:
                    folder_path = os.path.join(root, d)
                    img_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                    
                    def parse_slot(filename):
                        fn_clean = filename.lower().rsplit('.', 1)[0]
                        # 1. Match patterns like "-01-1-W" or "-01-2-wonder"
                        m = re.search(r'-01-(\d+)[-_]', fn_clean)
                        if m:
                            return int(m.group(1))
                        # 2. Match standard formats with -W, -wonder, -26u-wonder, etc.
                        fn_suffix = re.sub(r'^\d+\s*stol\s*[a-z0-9_]*\s*[-_]', '', fn_clean)
                        suffix_matches = re.findall(r'[-_](\d+)(?:[-_]|$)', fn_suffix)
                        if suffix_matches:
                            for m_str in suffix_matches:
                                val = int(m_str)
                                if 1 <= val <= 10:
                                    return val
                        return None
                    
                    candidates = [f for f in img_files if parse_slot(f) == slot]
                    if candidates:
                        candidates.sort(key=lambda x: (
                            0 if 'wonder' in x.lower() else 1,
                            1 if re.search(r'-01\s*-1', x.lower()) or '-01-1_w' in x.lower() else 0,
                            x.lower()
                        ))
                        return os.path.join(folder_path, candidates[0])
                    
                    if slot == 1 and img_files:
                        fallback_candidates = [f for f in img_files if parse_slot(f) not in range(2, 10)]
                        if fallback_candidates:
                            wonder_candidates = [c for c in fallback_candidates if 'wonder' in c.lower()]
                            if wonder_candidates:
                                return os.path.join(folder_path, wonder_candidates[0])
                            return os.path.join(folder_path, fallback_candidates[0])
                        return os.path.join(folder_path, img_files[0])
                        
    # 2. Look in TEST TOPAZ
    is_ystad_sku = "1979" in sku_clean
    if os.path.exists(TOPAZ_DIR) and not has_wb_fix_folder and not is_ystad_sku:
        for f in os.listdir(TOPAZ_DIR):
            if f.lower().endswith('.webp'):
                m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
                if m:
                    name_part = m.group(1)
                    s_part = int(m.group(2))
                    if normalize_name(name_part) == prod_norm and s_part == slot:
                        return os.path.join(TOPAZ_DIR, f)
                        
    # 3. Look in reforma_original_images_by_product
    if os.path.exists(ORIG_DIR):
        for folder in os.listdir(ORIG_DIR):
            sku_match = re.search(r'\(([^)]+)\)', folder)
            if sku_match:
                folder_sku = sku_match.group(1).strip().lower()
                if folder_sku == sku_clean:
                    if slot == 1:
                        folder_path = os.path.join(ORIG_DIR, folder, "artiklar")
                        if os.path.exists(folder_path):
                            candidates = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and os.path.isfile(os.path.join(folder_path, f))]
                            if candidates:
                                return os.path.join(folder_path, candidates[0])
                    else:
                        folder_path = os.path.join(ORIG_DIR, folder, "artiklar", "zoom")
                        if os.path.exists(folder_path):
                            candidates = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                            match_prefix = f"{sku_clean}_{slot}."
                            for c in candidates:
                                if c.lower().startswith(match_prefix):
                                    return os.path.join(folder_path, c)
                            
    return None

def main():
    print("=== RAW ENVIRONMENT SETUP ===")
    
    # 1. Load brand dict
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
    sku_to_prod = {}
    for slug, info in brand_sku_dict.items():
        sku = info.get("sku", "").strip().lower()
        if sku:
            sku_to_prod[sku] = (slug, info.get("name", slug))
            
    # 2. Clear test corrected directory structure completely
    if os.path.exists(TEST_DIR):
        print(f"Cleaning files in existing test directory: {TEST_DIR}")
        for root, dirs, files in os.walk(TEST_DIR, topdown=False):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                except Exception as e:
                    print(f"Failed to remove file {f}: {e}")
                    
    artiklar_dir = os.path.join(TEST_DIR, "artiklar")
    liten_dir = os.path.join(artiklar_dir, "liten")
    zoom_dir = os.path.join(artiklar_dir, "zoom")
    os.makedirs(artiklar_dir, exist_ok=True)
    os.makedirs(liten_dir, exist_ok=True)
    os.makedirs(zoom_dir, exist_ok=True)
    
    # 3. Copy review_status.json from original to test folder
    src_status = os.path.join(SRC_DIR, "review_status.json")
    dest_status = os.path.join(TEST_DIR, "review_status.json")
    if os.path.exists(src_status):
        shutil.copy2(src_status, dest_status)
        print("Copied review_status.json to test directory.")
        
        # Load and filter review_status.json to reset targeted SKUs
        with open(dest_status, 'r', encoding='utf-8') as f:
            status_db = json.load(f)
            
        keys_to_delete = []
        for key in status_db.keys():
            fn = os.path.basename(key).lower()
            for t in targets:
                if fn.startswith(t + '.') or fn.startswith(t + '_'):
                    keys_to_delete.append(key)
                    break
                    
        for key in keys_to_delete:
            del status_db[key]
            
        print(f"Deleted {len(keys_to_delete)} keys in review_status.json to reset their status.")
        with open(dest_status, 'w', encoding='utf-8') as f:
            json.dump(status_db, f, indent=2)
            
    # 4. Copy raw original files for each target SKU
    for t in targets:
        if t not in sku_to_prod:
            print(f"SKU {t} not found in brand dict. Skipping raw find.")
            continue
            
        slug, prod_name = sku_to_prod[t]
        
        # A. Copy main image (slot 1)
        raw_main = find_raw_original(t, prod_name, slot=1)
        if raw_main and os.path.exists(raw_main):
            shutil.copy2(raw_main, os.path.join(artiklar_dir, f"{t}.jpg"))
            shutil.copy2(raw_main, os.path.join(zoom_dir, f"{t}_1.jpg"))
            print(f"Copied raw main image and zoom_1 for {t}: {os.path.basename(raw_main)}")
        else:
            # Fallback to SRC_DIR if no raw image found
            fallback_main = os.path.join(SRC_DIR, "artiklar", f"{t}.jpg")
            if os.path.exists(fallback_main):
                shutil.copy2(fallback_main, os.path.join(artiklar_dir, f"{t}.jpg"))
                print(f"Copied fallback pre-cropped main image for {t}")
            fallback_zoom1 = os.path.join(SRC_DIR, "artiklar", "zoom", f"{t}_1.jpg")
            if os.path.exists(fallback_zoom1):
                shutil.copy2(fallback_zoom1, os.path.join(zoom_dir, f"{t}_1.jpg"))
                
        # Copy liten (small) image if it exists in SRC_DIR
        liten_src = os.path.join(SRC_DIR, "artiklar", "liten", f"{t}_S.jpg")
        if os.path.exists(liten_src):
            shutil.copy2(liten_src, os.path.join(liten_dir, f"{t}_S.jpg"))
            print(f"Copied liten image for {t}")
                
        # B. Copy zoom images (slots 2-10)
        # Check in original zoom folder and TOPAZ/fix folder
        copied_zoom_count = 0
        for slot in range(2, 11):
            raw_zoom = find_raw_original(t, prod_name, slot=slot)
            if raw_zoom and os.path.exists(raw_zoom):
                dest_name = f"{t}_{slot}.jpg"
                shutil.copy2(raw_zoom, os.path.join(zoom_dir, dest_name))
                copied_zoom_count += 1
                
        # If no raw zoom images found, check if there are pre-cropped ones in SRC_DIR
        if copied_zoom_count == 0:
            zoom_src = os.path.join(SRC_DIR, "artiklar", "zoom")
            if os.path.exists(zoom_src):
                for f in os.listdir(zoom_src):
                    fn = f.lower()
                    if fn.startswith(t + '_'):
                        shutil.copy2(os.path.join(zoom_src, f), os.path.join(zoom_dir, f))
                        copied_zoom_count += 1
                        
        print(f"Copied {copied_zoom_count} zoom images for {t}.")
        
    # 5. Clear targeted JPGs from output directory to prevent leftovers
    out_artiklar = os.path.join(FTP_UPLOAD_DIR, "artiklar")
    out_liten = os.path.join(out_artiklar, "liten")
    out_zoom = os.path.join(out_artiklar, "zoom")
    
    for folder in [out_artiklar, out_liten, out_zoom]:
        if os.path.exists(folder):
            print(f"Cleaning existing images in output directory: {folder}")
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                if os.path.isfile(item_path) and item.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    try:
                        os.remove(item_path)
                    except Exception as e:
                        print(f"Failed to remove {item}: {e}")
                        
    print("\nEnvironment setup complete. Clean raw originals copied and output directories cleared.")

if __name__ == "__main__":
    main()
