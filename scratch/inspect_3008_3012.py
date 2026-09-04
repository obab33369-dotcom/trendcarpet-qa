import json
import os

db_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_full_catalog.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

targets = [3008, 3009, 3012]
print("=== PROMPT DB ENTRIES ===")
for item in db:
    prompt = item.get("prompt", "")
    for t in targets:
        if prompt.startswith(f"{t} "):
            print(f"Index: {t}")
            print(f"Prompt: {prompt}")
            print(f"Image References: {item.get('image_references')}")
            print(f"Other fields: {list(item.keys())}")
            print("-" * 60)
