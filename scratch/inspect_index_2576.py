import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

for item in db:
    prompt = item.get('prompt', '')
    if prompt.startswith("2576 ") or prompt.startswith("2576-"):
        print("=== INDEX 2576 ===")
        print(f"Prompt: {prompt}")
        print(f"Image References: {item.get('image_references')}")
        print("-" * 50)
