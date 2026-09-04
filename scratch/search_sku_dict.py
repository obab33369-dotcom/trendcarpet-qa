import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
sku_map_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "sku_map.json")

with open(sku_map_path, 'r', encoding='latin-1') as f:
    sku_map = json.load(f)

print("10 sample keys in sku_map.json:")
for idx, (k, v) in enumerate(sku_map.items()):
    if idx >= 15:
        break
    print(f"  {k} -> {v}")
