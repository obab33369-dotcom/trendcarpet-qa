import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_sku_dict = json.load(f)

print("Entries in brand_sku_dict.json containing 'carrano' or SKUs RG01-70, RG01-71, RG01-72:")
for k, v in brand_sku_dict.items():
    if "carrano" in k or v['sku'] in ["RG01-70", "RG01-71", "RG01-72", "RG01-8", "RG01-7"]:
        print(f"  Key: {k} -> SKU: {v['sku']} | Name: {v.get('name')}")
