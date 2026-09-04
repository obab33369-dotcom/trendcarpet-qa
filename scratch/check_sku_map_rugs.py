import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')

with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

test_keys = [
    "2007_matta-aravelle-gra-multi.jpg",
    "2008_matta-aravelle-turkos-multi.jpg",
    "2073_matta-orlisse-rod.jpg",
    "3006_matta-orlisse-brun.png",
    "2087_matta-seronis-svart-beige.jpg",
    "2090_matta-sorvento-svart-gra.jpg",
    "2088_matta-sorvento-gra-beige.jpg",
    "2089_matta-sorvento-svart-beige.jpg"
]

print("=== CHECKING KEY MAP RESOLUTIONS ===")
for tk in test_keys:
    # Try direct lookup, and also lowercase lookup or substring
    found = False
    for k, v in sku_map.items():
        if k.lower() == tk.lower() or k.lower().startswith(tk.lower().split('.')[0]):
            print(f"Key: {k} -> SKU: {v.get('sku')} | Slug: {v.get('slug')}")
            found = True
    if not found:
        print(f"Key: {tk} -> NOT FOUND")
