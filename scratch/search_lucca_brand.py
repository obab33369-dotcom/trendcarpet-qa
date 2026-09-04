import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_dict = json.load(f)

print("=== Search for 'lucca' in brand_sku_dict.json ===")
found = False
for k, v in brand_dict.items():
    name = v.get("name", "")
    sku = v.get("sku", "")
    if "lucca" in k.lower() or "lucca" in name.lower():
        print(f"Key: {k} | SKU: {sku} | Name: {name}")
        found = True

if not found:
    print("No product with 'lucca' found in brand_sku_dict.json")
