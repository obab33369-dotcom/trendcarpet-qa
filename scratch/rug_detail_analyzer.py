import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

print("=== SEARCHING FOR SPECIFIC RUG KEYWORDS IN PROMPTS ===")
keywords = ["seronis", "arabelle", "aravelle", "sorvento", "orlisse"]

for item in db:
    prompt = item.get("prompt", "")
    image_references = item.get("image_references", "")
    
    found_keywords = [kw for kw in keywords if kw in prompt.lower() or kw in image_references.lower()]
    if found_keywords:
        m = re.match(r'^(\d+)\s*-', prompt)
        idx = int(m.group(1)) if m else None
        
        print(f"Index {idx}:")
        print(f"  Found Keywords: {found_keywords}")
        print(f"  Prompt: {prompt}")
        print(f"  Refs:   {image_references}")
        print("-" * 60)
