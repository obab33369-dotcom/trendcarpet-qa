import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def inspect_file(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        print(f"{filename} not found")
        return
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n--- {filename} ---")
    print(f"Total items: {len(data)}")
    if isinstance(data, list) and len(data) > 0:
        print("Sample item keys:", list(data[0].keys()))
        print("Sample prompt:", data[0].get("prompt", "")[:120])
    elif isinstance(data, dict):
        print("Keys:", list(data.keys())[:10])

inspect_file("rooms_turboflow_batch1.json")
inspect_file("turboflow_ready_batch1.json")
inspect_file("rooms_turboflow_batch2.json")
inspect_file("turboflow_ready_batch2.json")
inspect_file("rooms_turboflow_full_catalog.json")
inspect_file("turboflow_ready_full_catalog.json")
inspect_file("turboflow_ready.json")
