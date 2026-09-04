import os
import json
import re

REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
BRAND_DICT_PATH = os.path.join(REFORMA_DIR, "brand_sku_dict.json")
NEW_WHITE_BG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"

with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
    brand_sku_dict = json.load(f)

def normalize_name(name):
    text = name.lower()
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'é': 'e', 'è': 'e', 'ü': 'u', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

sku_to_names = {}
for name, info in brand_sku_dict.items():
    sku = info.get("sku", "").strip()
    if sku:
        sku_to_names[sku] = (name, normalize_name(name))

print("Looking for folders in White Background Fix directory...")
folders_in_fix = {}
for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
    for d in dirs:
        norm = normalize_name(d)
        folders_in_fix[norm] = os.path.join(root, d)

for sku in ["2105", "19011"]:
    if sku in sku_to_names:
        prod_name, norm_name = sku_to_names[sku]
        print(f"\nSKU {sku} -> Product Name: '{prod_name}' (normalized: '{norm_name}')")
        
        # Look for matching folder
        matched_folder = None
        for f_norm, f_path in folders_in_fix.items():
            if f_norm == norm_name or norm_name in f_norm or f_norm in norm_name:
                matched_folder = f_path
                break
                
        if matched_folder:
            print(f"  Matched folder: {matched_folder}")
            files = [f for f in os.listdir(matched_folder) if os.path.isfile(os.path.join(matched_folder, f))]
            print(f"  Files in folder: {files}")
        else:
            print("  No matching folder found in White Background Fix directory.")
    else:
        print(f"SKU {sku} not found in brand_sku_dict.")
