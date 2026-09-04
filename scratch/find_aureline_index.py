import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

print("=== CARPET DB ENTRIES ===")
for item in db:
    prompt = item.get("prompt", "")
    refs = item.get("image_references", "")
    
    if any(kw in prompt.lower() for kw in ["aureline", "carrano", "matta-forma", "lorano-brun", "marionae", "markelo", "merano-gra", "velenna-svart", "ventaro-beige"]):
        import re
        m = re.match(r'^(\d+)', prompt)
        idx = m.group(1) if m else "?"
        print(f"Index {idx}:")
        print(f"  Prompt: {prompt[:150]}...")
        print(f"  Refs:   {refs}")
        print("-" * 50)
