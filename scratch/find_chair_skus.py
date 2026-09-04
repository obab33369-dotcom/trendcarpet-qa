import os
import json
import re

brand_dict_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\brand_sku_dict.json"
fix_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix"
chair_folders = ["Refoma chair", "armchairs"]

with open(brand_dict_path, "r", encoding="utf-8") as f:
    brand_sku_dict = json.load(f)

def normalize_name(name):
    name = name.lower()
    replacements = {
        'å': 'a', 'ä': 'a', 'ö': 'o', 'é': 'e', 'è': 'e',
        'ü': 'u', 'ó': 'o', 'á': 'a', 'í': 'i', 'ø': 'o', 'æ': 'a'
    }
    for char, rep in replacements.items():
        name = name.replace(char, rep)
    return re.sub(r'[^a-z0-9]', '', name)

# Scan orig folders to resolve prod_norm to sku
# Or do it by scanning files in the chair subfolders
chair_skus = set()

# Map product normal names to SKUs from brand_sku_dict
name_to_sku = {}
for name, info in brand_sku_dict.items():
    norm = normalize_name(name)
    name_to_sku[norm] = info["sku"].strip()

# Scan folders inside Refoma chair and armchairs
for folder_name in chair_folders:
    folder_path = os.path.join(fix_dir, folder_name)
    if not os.path.exists(folder_path):
        continue
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            norm = normalize_name(item)
            # Find match in name_to_sku
            matched_sku = name_to_sku.get(norm)
            if matched_sku:
                chair_skus.add(matched_sku)
            else:
                # Substring matching
                for name_norm, sku in name_to_sku.items():
                    if norm == name_norm or norm in name_norm or name_norm in norm:
                        chair_skus.add(sku)
                        break

print(f"Found {len(chair_skus)} chair SKUs from Refoma chair and armchairs subfolders:")
print(sorted(list(chair_skus)))
