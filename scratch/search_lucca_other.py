import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_json(filepath, term):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        db = json.load(f)
    print(f"\n=== Search in {os.path.basename(filepath)} ===")
    if isinstance(db, dict):
        for k, v in db.items():
            if term in k.lower() or term in str(v).lower():
                print(f"Key: {k} | Value: {v}")
    elif isinstance(db, list):
        for item in db:
            if term in str(item).lower():
                print(item)

search_json(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "sku_map.json"), "1397")
search_json(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "sku_map.json"), "lucca")
search_json(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "complete_sku_map.py"), "1397") # wait, python script? let's ignore.
search_json(os.path.join(WORKSPACE_DIR, "reforma-turboflow", "complete_sku_map.py"), "lucca")
