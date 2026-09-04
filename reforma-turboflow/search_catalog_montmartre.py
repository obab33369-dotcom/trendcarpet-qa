import os
import json

json_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\rooms_turboflow_full_catalog.json"
if not os.path.exists(json_path):
    json_path = r"rooms_turboflow_full_catalog.json"

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded catalog from {json_path}")
    
    matches = []
    for idx, item in enumerate(data):
        prompt = item.get("prompt", "")
        tags = item.get("image_tags", [])
        if "montmartre" in prompt.lower():
            matches.append((idx + 1, prompt, tags))
            
    print(f"Found {len(matches)} matches in catalog:")
    for row_num, prompt, tags in matches[:25]:
        print(f"Row {row_num}: tags={tags} | {prompt[:180]}...")
else:
    print("Catalog file not found.")
