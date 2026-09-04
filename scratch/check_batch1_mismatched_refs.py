import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def print_indices(indices):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_batch1.json")
    with open(p, 'r', encoding='utf-8') as f:
        db = json.load(f)
    for item in db:
        prompt = item.get('prompt', '')
        import re
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            idx = int(m.group(1))
            if idx in indices:
                print(f"\nIndex {idx}:")
                print(f"  Prompt: {prompt[:200]}...")
                print(f"  Refs: {item.get('image_references')}")

print_indices([1231, 1232, 2199, 2200])
