import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

print("--- SKU MAP RG01 ENTRIES ---")
with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)
for k, v in sku_map.items():
    if "RG01" in k or "seronis" in k.lower() or "arabelle" in k.lower() or "orlisse" in k.lower() or "sorvento" in k.lower():
        print(f"Key: {k} -> {v}")

print("\n--- BRAND DICT RG01 ENTRIES ---")
with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_dict = json.load(f)
for k, v in brand_dict.items():
    if "RG01" in v.get("sku", "") or "seronis" in k.lower() or "arabelle" in k.lower() or "orlisse" in k.lower() or "sorvento" in k.lower() or "seronis" in v.get("name", "").lower() or "arabelle" in v.get("name", "").lower() or "orlisse" in v.get("name", "").lower() or "sorvento" in v.get("name", "").lower():
        print(f"Slug: {k} -> {v}")

print("\n--- DB RG01 PROMPTS ---")
with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)
for item in db:
    prompt = item.get("prompt", "")
    refs = item.get("image_references", "")
    if "RG01" in prompt or "RG01" in refs or "seronis" in prompt.lower() or "arabelle" in prompt.lower() or "orlisse" in prompt.lower() or "sorvento" in prompt.lower():
        print(f"Prompt: {prompt}\nRefs: {refs}\n")
