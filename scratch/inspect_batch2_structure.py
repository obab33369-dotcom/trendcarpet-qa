import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_batch2.json")
if os.path.exists(p):
    with open(p, 'r', encoding='utf-8') as f:
        db = json.load(f)
    print(f"Loaded {len(db)} items from batch2")
    if db:
        item = db[0]
        print("Keys:", list(item.keys()))
        print("Sample item:")
        print(json.dumps(item, indent=2, ensure_ascii=False)[:600])
else:
    print("Batch 2 JSON not found")
