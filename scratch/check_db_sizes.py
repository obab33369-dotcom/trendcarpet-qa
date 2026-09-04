import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def print_db_stats(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    indices = []
    for item in data:
        prompt = item.get('prompt', '')
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            indices.append(int(m.group(1)))
            
    if indices:
        print(f"{filename}: {len(data)} items | Min index: {min(indices)} | Max index: {max(indices)}")
    else:
        print(f"{filename}: {len(data)} items | No numeric indices found")

print_db_stats("rooms_turboflow_batch1.json")
print_db_stats("rooms_turboflow_batch2.json")
print_db_stats("rooms_turboflow_full_catalog.json")
