import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_dict = json.load(f)

print("=== ALL CARPETS (RG01) ===")
for slug, info in brand_dict.items():
    sku = info.get("sku", "")
    name = info.get("name", "")
    if sku.startswith("RG01") or "matta" in slug or "matta" in name.lower():
        print(f"Slug: {slug} -> SKU: {sku} | Name: {name}")
