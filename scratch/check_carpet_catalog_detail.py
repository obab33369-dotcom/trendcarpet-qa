import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
catalog_path = os.path.join(WORKSPACE_DIR, 'scratch', 'carpet_catalog.json')

with open(catalog_path, 'r', encoding='utf-8') as f:
    catalog = json.load(f)

print("Entries in carpet_catalog.json:")
for sku in sorted(catalog.keys()):
    if sku.startswith("RG01-7") or sku.startswith("RG01-8"):
        print(f"  SKU: {sku} -> {catalog[sku]}")
