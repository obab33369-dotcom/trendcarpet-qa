import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

indices_to_check = [1827, 1883, 1884, 1889, 1890, 1895, 2018, 2023, 2024, 2029, 2030, 2035, 2036, 2041, 2042, 2161, 2163, 2164, 2165, 2166, 2341, 2342, 2343, 2344, 2345, 2346, 2347, 2348]

print("=== CHECKING CARPET INDICES ===")
for item in db:
    prompt = item.get('prompt', '')
    m = re.match(r"^(\d+)", prompt)
    if m:
        idx = int(m.group(1))
        if idx in indices_to_check:
            print(f"Index {idx}:")
            print(f"  Prompt: {prompt[:150]}...")
            print(f"  Refs: {item.get('image_references')}")
            print("-" * 50)
