import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def check_prompts():
    # Batch 1, Index 1973
    p1 = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_batch1.json")
    with open(p1, 'r', encoding='utf-8') as f:
        db1 = json.load(f)
    for item in db1:
        if item.get('prompt', '').strip().startswith("1973 "):
            print("=== Batch 1, Index 1973 ===")
            print(f"Prompt: {item.get('prompt')}")
            print(f"Refs: {item.get('image_references')}")

    # Full Catalog, Index 183
    p2 = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")
    with open(p2, 'r', encoding='utf-8') as f:
        db2 = json.load(f)
    for item in db2:
        if item.get('prompt', '').strip().startswith("183 "):
            print("\n=== Full Catalog, Index 183 ===")
            print(f"Prompt: {item.get('prompt')}")
            print(f"Refs: {item.get('image_references')}")

    # Full Catalog, Index 1973
    for item in db2:
        if item.get('prompt', '').strip().startswith("1973 "):
            print("\n=== Full Catalog, Index 1973 ===")
            print(f"Prompt: {item.get('prompt')}")
            print(f"Refs: {item.get('image_references')}")

check_prompts()
