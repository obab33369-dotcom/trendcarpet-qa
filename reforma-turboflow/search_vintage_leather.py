import os
import json

json_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\rooms_turboflow_full_catalog.json"
if not os.path.exists(json_path):
    json_path = r"rooms_turboflow_full_catalog.json"

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("--- VINTAGE / LÄDER JÄRN SEARCH ---")
    for idx, item in enumerate(data):
        prompt = item.get("prompt", "")
        if "läder" in prompt.lower() and "järn" in prompt.lower():
            print(f"Row {idx+1}: {prompt[:200]}")
else:
    print("Catalog file not found.")
