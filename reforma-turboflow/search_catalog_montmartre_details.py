import os
import json

json_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\rooms_turboflow_full_catalog.json"
if not os.path.exists(json_path):
    json_path = r"rooms_turboflow_full_catalog.json"

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    matches = []
    for idx, item in enumerate(data):
        prompt = item.get("prompt", "")
        if "montmartre" in prompt.lower():
            matches.append((idx + 1, item))
            
    print(f"Found {len(matches)} matches in catalog.")
    # Group by the specific chair description in prompt
    grouped = {}
    for row_num, item in matches:
        prompt = item.get("prompt", "")
        import re
        m = re.search(r'chairs? \((.*?)\)', prompt, re.IGNORECASE)
        if m:
            chair_desc = m.group(1)
            grouped.setdefault(chair_desc, []).append((row_num, item))
            
    for desc, rows in grouped.items():
        print(f"\nDescription in prompt: {desc} (Count: {len(rows)})")
        # Print first row details
        r_num, r_item = rows[0]
        print(f"  Sample Row {r_num}:")
        print(f"    Tags: {r_item.get('image_tags')}")
        print(f"    Refs: {r_item.get('image_references')[:3]}")
else:
    print("Catalog file not found.")
