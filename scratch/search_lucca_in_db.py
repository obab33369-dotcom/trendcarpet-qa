import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")
with open(db_path, 'r', encoding='latin-1') as f:
    data = json.load(f)

for item in data:
    prompt = item.get('prompt', '')
    img_refs = item.get('image_references', '')
    if "0108" in img_refs or "1397" in img_refs or "texas-ljus" in img_refs.lower() or "lucca" in img_refs.lower():
        print("Found in full_catalog:")
        print(f"  Prompt: {prompt[:150]}")
        print(f"  Refs: {img_refs}")
