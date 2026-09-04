import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def check_db_range(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        print(f"File not found: {p}")
        return
        
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    indices = []
    for item in data:
        prompt = item.get('prompt', '')
        m = re.match(r'^(\d+)\s*-', prompt)
        if m:
            indices.append(int(m.group(1)))
            
    if indices:
        print(f"{filename}:")
        print(f"  Total prompts: {len(data)}")
        print(f"  Min index: {min(indices)}")
        print(f"  Max index: {max(indices)}")
    else:
        print(f"{filename} has no indices matched.")

def main():
    check_db_range("rooms_turboflow_batch1.json")
    check_db_range("rooms_turboflow_batch2.json")
    check_db_range("rooms_turboflow_full_catalog.json")

if __name__ == "__main__":
    main()
