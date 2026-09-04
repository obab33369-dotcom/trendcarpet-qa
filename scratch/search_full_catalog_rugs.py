import json
import os
import re
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from execute_full_catalog_sorting import resolve_anchor, load_db

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

print("=== RESOLVING ALL CARPET REFERENCES IN DB ===")
for item in db:
    prompt = item.get("prompt", "")
    image_references = item.get("image_references", "")
    
    # Check if there is any rug mentioned in prompt or refs
    if any(term in prompt.lower() or term in image_references.lower() for term in ["matta", "rg01", "seronis", "arabelle", "orlisse", "sorvento"]):
        # Extract index
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            idx = int(m.group(1))
            refs = [r.strip() for r in image_references.split(';') if r.strip()]
            resolved = []
            for ref in refs:
                sku, name = resolve_anchor(ref)
                resolved.append((ref, sku, name))
            
            print(f"Index: {idx}")
            print(f"  Prompt: {prompt[:150]}...")
            print(f"  Refs: {refs}")
            print(f"  Resolved to: {resolved}")
            print("-" * 50)
