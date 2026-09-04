import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def print_detail(filename, target_indices):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        db = json.load(f)
    print(f"\n================ DETAILS FOR {filename} ================")
    for item in db:
        prompt = item.get('prompt', '')
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            idx = int(m.group(1))
            if idx in target_indices:
                print(f"Index {idx}:")
                print(f"  Prompt: {prompt}")
                print(f"  Refs: {item.get('image_references')}")

b1_indices = [637, 638, 1241, 1242]
print_detail("rooms_turboflow_batch1.json", b1_indices)
