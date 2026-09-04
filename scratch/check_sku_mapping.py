import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

print("=== Search in sku_map.json ===")
for k, v in sku_map.items():
    if "1397" in k or "0108" in k:
        print(f"Key: {k} | Value: {v}")

brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_dict = json.load(f)

print("\n=== Search in brand_sku_dict.json ===")
for k, v in brand_dict.items():
    sku = v.get("sku", "")
    if "1397" in k or "0108" in k or "1397" in sku or "0108" in sku:
        print(f"Key: {k} | Value: {v}")
