import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

print("=== SEARCHING FOR RG01-6 / 2104 ===")
count = 0
for item in db:
    prompt = item.get('prompt', '')
    refs = item.get('image_references', '')
    if "2104" in refs or "RG01-6" in refs or "velenna-svart-beige" in refs or "velenna-svart-beige" in prompt.lower():
        count += 1
        print(f"Index: {prompt.split(' - ')[0]}")
        print(f"  Prompt: {prompt[:150]}...")
        print(f"  Refs: {refs}")
        print("-" * 50)
print(f"Total found: {count}")
