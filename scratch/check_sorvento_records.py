import json
import os
import sys

sys.path.append(r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch")
from execute_full_catalog_sorting import resolve_anchor

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

for item in db:
    prompt = item.get("prompt", "")
    refs = item.get("image_references", "")
    
    if "sorvento" in prompt.lower():
        import re
        m = re.match(r'^(\d+)', prompt)
        idx = m.group(1) if m else "?"
        print(f"Index {idx}:")
        print(f"  Prompt: {prompt[:200]}")
        print(f"  Refs: {refs}")
        resolved = []
        for r in refs.split(';'):
            r = r.strip()
            sku, name = resolve_anchor(r)
            resolved.append(f"{r} -> {sku} ({name})")
        print(f"  Resolved: {resolved}")
        print("-" * 50)
