import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
sku_map_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'sku_map.json')
brand_dict_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'brand_sku_dict.json')
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(sku_map_path, 'r', encoding='utf-8') as f:
    sku_map = json.load(f)

with open(brand_dict_path, 'r', encoding='utf-8') as f:
    brand_dict = json.load(f)

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

# Find all entries where the prompt mentions Seronis, Aravelle, Sorvento, or Orlisse
print("=== DB RUGS ENTRIES ===")
for item in db:
    prompt = item.get("prompt", "")
    image_references = item.get("image_references", "")
    
    # Check for keywords
    has_seronis = "seronis" in prompt.lower() or "seronis" in image_references.lower()
    has_arabelle = "arabelle" in prompt.lower() or "arabelle" in image_references.lower() or "aravelle" in prompt.lower() or "aravelle" in image_references.lower()
    has_sorvento = "sorvento" in prompt.lower() or "sorvento" in image_references.lower()
    has_orlisse = "orlisse" in prompt.lower() or "orlisse" in image_references.lower()
    
    if has_seronis or has_arabelle or has_sorvento or has_orlisse:
        m = re.match(r'^(\d+)\s*-', prompt)
        idx = int(m.group(1)) if m else None
        
        # We want to see:
        # 1. The index
        # 2. What rug is mentioned in the text prompt
        # 3. What reference filenames are listed in the database
        print(f"Index {idx}:")
        print(f"  Prompt: {prompt[:200]}")
        print(f"  Refs  : {image_references}")
        print("-" * 40)
