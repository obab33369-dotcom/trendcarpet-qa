import os
import re
import json

REFORMA_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
NEW_WHITE_BG_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"
BRAND_DICT_PATH = os.path.join(REFORMA_DIR, "brand_sku_dict.json")

with open(BRAND_DICT_PATH, 'r', encoding='utf-8') as f:
    brand_sku_dict = json.load(f)

sku_to_prod = {}
for slug, info in brand_sku_dict.items():
    sku = info.get("sku", "").strip().lower()
    if sku:
        sku_to_prod[sku] = (slug, info.get("name", slug))

def normalize_name(name):
    text = name.lower()
    text = re.sub(r'^\s*\d+\s*', '', text)
    repl = {'ö': 'o', 'ä': 'a', 'å': 'a', 'ö': 'o', 'ä': 'a', 'å': 'a'}
    for char, rep in repl.items():
        text = text.replace(char, rep)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

sku = "1091-walnut"
slug, prod_name = sku_to_prod[sku]
prod_norm = normalize_name(prod_name)

print(f"Product Name: {prod_name}")
print(f"Normalized Name: {prod_norm}")

found_folder = None
for root, dirs, files in os.walk(NEW_WHITE_BG_DIR):
    for d in dirs:
        if normalize_name(d) == prod_norm:
            found_folder = os.path.join(root, d)
            print(f"Found folder: {found_folder}")
            print("Files in folder:")
            for f in os.listdir(found_folder):
                print(f" - {f}")
            break

if not found_folder:
    print("Folder not found in Refoma white background fix.")
