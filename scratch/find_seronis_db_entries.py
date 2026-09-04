import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
prompt_db_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'rooms_turboflow_full_catalog.json')

with open(prompt_db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

keywords = ["seronis", "sorvento", "velenna", "carrano", "arabelle", "aravelle", "orlisse"]

print("=== DB SEARCH FOR CARPET KEYWORDS ===")
found_count = 0
for item in db:
    prompt_text = item.get("prompt", "")
    refs_str = item.get("image_references", "")
    
    # Check for keywords
    has_kw = any(kw in prompt_text.lower() or kw in refs_str.lower() for kw in keywords)
    if has_kw:
        found_count += 1
        m = re.match(r"^(\d+)", prompt_text)
        idx = int(m.group(1)) if m else None
        
        print(f"Index {idx}:")
        print(f"  Prompt: {prompt_text[:150]}...")
        print(f"  Refs  : {refs_str}")
        print("-" * 50)
        
        if found_count >= 30:
            print("Showing first 30 entries only.")
            break
print(f"Total entries found: {found_count}")
