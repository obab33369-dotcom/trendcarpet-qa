import os
import json
import re

json_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\rooms_turboflow_full_catalog.json"
if not os.path.exists(json_path):
    # Try local workspace path
    json_path = r"rooms_turboflow_full_catalog.json"

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded catalog from {json_path}")
    
    matches = []
    for idx, item in enumerate(data):
        prompt = item.get("prompt", "")
        if "angom" in prompt.lower() or "ängom" in prompt.lower():
            matches.append((idx + 1, prompt))
            
    print(f"Found {len(matches)} matches in catalog:")
    for row_num, prompt in matches:
        print(f"Row {row_num}: {prompt[:200]}...")
else:
    print("Catalog file not found.")
