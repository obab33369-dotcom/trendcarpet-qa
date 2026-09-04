import os
import re
import json

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
FTP_DIR = os.path.join(ONEDRIVE_DIR, "26-06-18-FTP")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
FALLBACK_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
BRAND_DICT_PATH = "brand_sku_dict.json"

# 1. Collect SKUs in FTP folder and backup folders
ftp_skus = set()
backup_root = os.path.join(ONEDRIVE_DIR, "turboflow_backup")

scan_dirs = [
    FTP_DIR,
    os.path.join(backup_root, "chairs_cropped3"),
    os.path.join(backup_root, "ftp_upload_cropped"),
    os.path.join(backup_root, "temporary-ftp-upload")
]

for base_p in scan_dirs:
    for folder in ["artiklar", os.path.join("Inte-dessa-Uppdaterade-på-sajt-undersök-FTP", "artiklar")]:
        p = os.path.join(base_p, folder)
        if os.path.exists(p):
            for f in os.listdir(p):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    # Extract SKU from filename (e.g. 1200180.jpg -> 1200180)
                    sku = os.path.splitext(f)[0].strip()
                    # Also clean _S or indices
                    sku_clean = re.sub(r'[-_](S|\d+|liten|zoom)$', '', sku, flags=re.IGNORECASE)
                    ftp_skus.add(sku_clean.lower())

print(f"Total unique SKUs in FTP & Backup folders: {len(ftp_skus)}")

# Load brand sku dict
with open(BRAND_DICT_PATH, "r", encoding="utf-8") as f:
    brand_sku_dict = json.load(f)

# Helper to normalize names
def normalize_name(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A', '’': "'", '`': "'"}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'^\d+\s*', '', text)
    text = text.replace('sofa bed', 'baddsoffa')
    text = text.replace('bed sofa', 'baddsoffa')
    text = text.replace('bed armchair', 'baddfatolj')
    text = text.replace('sofabed', 'baddsoffa')
    text = text.replace('bedsofa', 'baddsoffa')
    text = text.replace('bedarmchair', 'baddfatolj')
    text = text.replace('seater sofa', 'sitssoffa')
    text = text.replace('seatersofa', 'sitssoffa')
    text = text.replace('sofa', 'soffa')
    text = text.replace('module', 'modul')
    text = text.replace('eucalyptus', 'eukalyptus')
    text = text.replace('cape verde', 'kap verde')
    text = text.replace('3-seater', '3-sits')
    text = text.replace('2-seater', '2-sits')
    text = text.replace('3-sitss', '3-sits')
    text = text.replace('2-sitss', '2-sits')
    text = text.replace('3 seater', '3 sits')
    text = text.replace('2 seater', '2 sits')
    text = text.replace('off-white', 'vit')
    text = text.replace('off white', 'vit')
    text = text.replace('offwhite', 'vit')
    text = text.replace('mintgron', 'gron')
    text = text.replace('ongom', 'angom')
    text = text.replace('ängom', 'angom')
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def get_category(prod_name):
    name_lower = prod_name.lower()
    if "matta" in name_lower or "rug" in name_lower:
        return "carpet"
    if "lampa" in name_lower or "lamp" in name_lower or "belysning" in name_lower or "ljus" in name_lower:
        return "lamp"
    if "tavla" in name_lower or "poster" in name_lower or "spegel" in name_lower or "kruka" in name_lower or "vas" in name_lower or "dekoration" in name_lower:
        return "decoration"
    if "vägghylla" in name_lower or "vagghylla" in name_lower or "vägghängd" in name_lower or "vagghangd" in name_lower:
        return "wall-hanging"
    if "soffa" in name_lower or "sofa" in name_lower or "schaslong" in name_lower:
        return "sofa"
    if "stol" in name_lower or "chair" in name_lower or "fåtölj" in name_lower or "fatolj" in name_lower or "barstol" in name_lower or "pall" in name_lower or "puff" in name_lower:
        return "chair"
    if "bord" in name_lower or "table" in name_lower or "desk" in name_lower or "byrå" in name_lower or "byra" in name_lower or "skåp" in name_lower or "skap" in name_lower or "skänk" in name_lower or "skank" in name_lower or "sideboard" in name_lower or "hylla" in name_lower or "shelf" in name_lower:
        return "furniture"
    return "other"

# Scan Topaz
topaz_norms = set()
if os.path.exists(TOPAZ_DIR):
    for f in os.listdir(TOPAZ_DIR):
        if f.lower().endswith('.webp'):
            m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
            if m:
                topaz_norms.add(normalize_name(m.group(1)))

# Scan Fallback
fallback_norms = set()
if os.path.exists(FALLBACK_DIR):
    for folder in os.listdir(FALLBACK_DIR):
        p = os.path.join(FALLBACK_DIR, folder, "artiklar")
        if os.path.isdir(p):
            fallback_norms.add(normalize_name(folder))

# Filter candidates
valid_candidates = []
for name, info in brand_sku_dict.items():
    sku = info.get('sku', '').strip()
    if not sku:
        continue
    # Exclude if in FTP
    if sku.lower() in ftp_skus:
        continue
    
    prod_norm = normalize_name(name)
    category = get_category(name)
    
    if category in ["sofa", "chair", "furniture"]:
        in_topaz = prod_norm in topaz_norms
        in_fallback = prod_norm in fallback_norms
        if in_topaz or in_fallback:
            valid_candidates.append({
                "sku": sku,
                "name": name,
                "category": category,
                "in_topaz": in_topaz,
                "in_fallback": in_fallback
            })

print(f"Found {len(valid_candidates)} valid candidates (not in FTP, not carpets/lamps/wall-hanging):")
for c in valid_candidates[:20]:
    print(f" SKU: {c['sku']} | Name: {c['name']} | Cat: {c['category']} | Topaz: {c['in_topaz']} | Fallback: {c['in_fallback']}")

# Save the full list of remaining candidate SKUs to json
out_json_path = os.path.join("scratch", "remaining_skus.json")
with open(out_json_path, "w", encoding="utf-8") as f_out:
    json.dump(valid_candidates, f_out, indent=2, ensure_ascii=False)
print(f"Saved all remaining SKUs to: {out_json_path}")
