import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')

with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

for k, v in sorted(sku_map.items()):
    if "RG01" in k or "seronis" in k.lower() or "arabelle" in k.lower() or "orlisse" in k.lower() or "sorvento" in k.lower():
        print(f"{k} -> {v}")
