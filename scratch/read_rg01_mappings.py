import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')

with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_dict = json.load(f)

print("=== sku_map.json matches for RG01 ===")
for k, v in sorted(sku_map.items()):
    if "RG01" in k:
        print(f"  {k} -> {v}")

print("\n=== brand_sku_dict.json matches for RG01 ===")
for k, v in sorted(brand_dict.items()):
    if "RG01" in v.get("sku", ""):
        print(f"  {k} -> {v}")

print("\n=== Special Name Lookups ===")
for k, v in sorted(brand_dict.items()):
    if any(n in k.lower() for n in ["seronis", "arabelle", "orlisse", "sorvento"]):
        print(f"  {k} -> SKU: {v.get('sku')} | Name: {v.get('name')}")
