import os
import re
import json

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
FALLBACK_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
BRAND_DICT_PATH = "brand_sku_dict.json"

# Load exclude list
exclude_list = []
if os.path.exists("exclude_list.json"):
    with open("exclude_list.json", "r", encoding="utf-8") as f:
        exclude_list = json.load(f)
exclude_set = set(exclude_list)

with open(BRAND_DICT_PATH, "r", encoding="utf-8") as f:
    brand_sku_dict = json.load(f)

# Helper to normalize names (same as classification.py)
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

# Classify function to check type
def get_category(prod_name):
    name_lower = prod_name.lower()
    if "matta" in name_lower or "rug" in name_lower:
        return "carpet"
    if "lampa" in name_lower or "lamp" in name_lower or "belysning" in name_lower or "ljus" in name_lower:
        return "lamp"
    if "tavla" in name_lower or "poster" in name_lower or "spegel" in name_lower or "kruka" in name_lower or "vas" in name_lower or "dekoration" in name_lower:
        return "decoration"
        
    # Check if wall-hanging or other things to skip
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

print(f"Unique Topaz product norms: {len(topaz_norms)}")
print(f"Unique Fallback product norms: {len(fallback_norms)}")

topaz_candidates = []
fallback_candidates = []

for name, info in brand_sku_dict.items():
    sku = info.get('sku', '').strip()
    if not sku:
        continue
    if sku in exclude_set:
        continue
    
    prod_norm = normalize_name(name)
    category = get_category(name)
    
    if category in ["sofa", "chair", "furniture"]:
        # Check if in Topaz
        if prod_norm in topaz_norms:
            topaz_candidates.append((sku, name, category, "topaz"))
        # Check if in Fallback
        if prod_norm in fallback_norms:
            fallback_candidates.append((sku, name, category, "fallback"))

print(f"\nFound {len(topaz_candidates)} Topaz furniture candidates:")
for c in topaz_candidates[:15]:
    print(f" SKU: {c[0]} | Name: {c[1]} | Cat: {c[2]}")

print(f"\nFound {len(fallback_candidates)} Fallback furniture candidates:")
for c in fallback_candidates[:15]:
    print(f" SKU: {c[0]} | Name: {c[1]} | Cat: {c[2]}")
