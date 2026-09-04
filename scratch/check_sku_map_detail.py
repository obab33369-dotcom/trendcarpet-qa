import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')

with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

print("Searching for '2021_matta-carrano-brun-vit' in sku_map.json:")
found = False
for k, v in sku_map.items():
    if "2021" in k or "carrano" in k:
        print(f"  {k} -> {v}")
        found = True

if not found:
    print("  Not found.")
