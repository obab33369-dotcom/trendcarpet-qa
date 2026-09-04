import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def check_index(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    if not os.path.exists(p):
        print(f"{filename} not found")
        return
    with open(p, 'r', encoding='utf-8') as f:
        db = json.load(f)
    found = False
    for item in db:
        prompt = item.get("prompt", "")
        if prompt.strip().startswith("2019"):
            print(f"--- Found in {filename} ---")
            print(f"Prompt: {prompt}")
            print(f"Image References: {item.get('image_references')}")
            found = True
    if not found:
        print(f"Index 2019 NOT found in {filename}")

check_index("rooms_turboflow_batch1.json")
check_index("rooms_turboflow_batch2.json")
check_index("rooms_turboflow_full_catalog.json")
