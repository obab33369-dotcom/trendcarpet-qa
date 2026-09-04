import os
import json

json_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\rooms_turboflow_full_catalog.json"
if not os.path.exists(json_path):
    json_path = r"rooms_turboflow_full_catalog.json"

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    matching_tags = set()
    for idx, item in enumerate(data):
        tags_raw = item.get("image_tags", "")
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(";")]
        elif isinstance(tags_raw, list):
            tags = tags_raw
        else:
            tags = []
            
        for t in tags:
            if "mont" in t.lower() or "marseille" in t.lower():
                matching_tags.add(t)
                
    print("Matching tags found in catalog:")
    for t in sorted(matching_tags):
        print(f"  {t}")
else:
    print("Catalog file not found.")
