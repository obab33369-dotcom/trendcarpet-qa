import os
import json
import re

REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
GEMINI_ENV = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"
BRAND_DICT_PATH = os.path.join(REFORMA_DIR, "brand_sku_dict.json")
FTP_UPLOAD_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3"
INPUT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images"
STATUS_FILE = os.path.join(FTP_UPLOAD_DIR, "review_status.json")
REPORT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\bad_crops_report.json"
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

def normalize_name(name):
    text = name.lower()
    text = re.sub(r'^\s*\d+\s*', '', text)
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

WB_FIX_FOLDERS = set()
if os.path.exists(NEW_WHITE_BG_DIR):
    for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
        for d in dirs:
            WB_FIX_FOLDERS.add(normalize_name(d))

def find_original_source_image(sku, prod_name, slot=1):
    prod_norm = normalize_name(prod_name)
    sku_clean = sku.strip().lower()
    has_wb_fix_folder = prod_norm in WB_FIX_FOLDERS

    if not has_wb_fix_folder:
        if slot == 1:
            local_path = os.path.join(INPUT_DIR, "artiklar", f"{sku}.jpg")
            if os.path.exists(local_path):
                return "INPUT_DIR/main", local_path
        else:
            local_path = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_{slot}.jpg")
            if os.path.exists(local_path):
                return "INPUT_DIR/zoom", local_path

    if os.path.exists(NEW_WHITE_BG_DIR):
        for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
            for d in dirs:
                if normalize_name(d) == prod_norm:
                    folder_path = os.path.join(root, d)
                    img_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                    
                    def parse_slot(filename):
                        fn_clean = filename.lower().rsplit('.', 1)[0]
                        m = re.search(r'-01-(\d+)[-_]', fn_clean)
                        if m:
                            return int(m.group(1))
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
                        return "WB_FIX_DIR/slot_match", os.path.join(folder_path, candidates[0])
                    
                    if slot == 1 and img_files:
                        fallback_candidates = [f for f in img_files if parse_slot(f) not in range(2, 10)]
                        if fallback_candidates:
                            return "WB_FIX_DIR/fallback_slot1", os.path.join(folder_path, fallback_candidates[0])
                        return "WB_FIX_DIR/first_file", os.path.join(folder_path, img_files[0])

    is_ystad_sku = "1979" in sku_clean
    if os.path.exists(TOPAZ_DIR) and not has_wb_fix_folder and not is_ystad_sku:
        for f in os.listdir(TOPAZ_DIR):
            if f.lower().endswith('.webp'):
                m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
                if m:
                    name_part = m.group(1)
                    s_part = int(m.group(2))
                    if normalize_name(name_part) == prod_norm and s_part == slot:
                        return "TOPAZ_DIR", os.path.join(TOPAZ_DIR, f)

    if os.path.exists(ORIG_DIR):
        for folder in os.listdir(ORIG_DIR):
            sku_match = re.search(r'\(([^)]+)\)', folder)
            if sku_match:
                folder_sku = sku_match.group(1).strip().lower()
                if folder_sku == sku_clean:
                    if slot == 1:
                        folder_path = os.path.join(ORIG_DIR, folder, "artiklar")
                        if os.path.exists(folder_path):
                            candidates = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                            if candidates:
                                return "ORIG_DIR/main", os.path.join(folder_path, candidates[0])
                    else:
                        folder_path = os.path.join(ORIG_DIR, folder, "artiklar", "zoom")
                        if os.path.exists(folder_path):
                            candidates = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                            match_prefix = f"{sku_clean}_{slot}."
                            for c in candidates:
                                if c.lower().startswith(match_prefix):
                                    return "ORIG_DIR/zoom", os.path.join(folder_path, c)

    if has_wb_fix_folder:
        if slot == 1:
            local_path = os.path.join(INPUT_DIR, "artiklar", f"{sku}.jpg")
            if os.path.exists(local_path):
                return "INPUT_DIR/main_fallback", local_path
        else:
            local_path = os.path.join(INPUT_DIR, "artiklar", "zoom", f"{sku}_{slot}.jpg")
            if os.path.exists(local_path):
                return "INPUT_DIR/zoom_fallback", local_path

    return None, None

def main():
    if not os.path.exists(REPORT_PATH):
        print("Report not found.")
        return
        
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        report = json.load(f)
        
    with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
        brand_sku_dict = json.load(f)
        
    sku_to_prod = {}
    for slug, info in brand_sku_dict.items():
        sku = info.get("sku", "").strip().lower()
        if sku:
            sku_to_prod[sku] = (slug, info.get("name", slug))
            
    status_db = {}
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            status_db = {k.lower(): v for k, v in json.load(f).items()}
            
    print(f"{'Filename':<25} | {'Source Type':<20} | {'Status':<15} | {'Category':<15} | {'Reason'}")
    print("-" * 100)
    
    for item in report:
        fn = item.get("filename")
        reason = item.get("reason")
        sku = fn.split('.')[0]
        sku_lower = sku.lower()
        
        db_key = f"artiklar/{fn.lower()}"
        entry = status_db.get(db_key, {})
        status = entry.get("status", "unknown")
        category = entry.get("category", "unknown")
        
        if sku_lower in sku_to_prod:
            slug, prod_name = sku_to_prod[sku_lower]
            src_type, src_path = find_original_source_image(sku, prod_name, slot=1)
        else:
            src_type, src_path = "unrecognized_sku", None
            
        print(f"{fn:<25} | {str(src_type):<20} | {status:<15} | {category:<15} | {reason}")

if __name__ == "__main__":
    main()
