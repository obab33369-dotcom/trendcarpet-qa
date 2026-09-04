import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

for db_name in ['rooms_turboflow_batch1.json', 'rooms_turboflow_batch2.json', 'rooms_turboflow_full_catalog.json']:
    path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', db_name)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        p = item.get('prompt', '')
        if p.startswith('033 ') or p.startswith('33 ') or p.startswith('033-') or p.startswith('33-'):
            print(f"[{db_name}] Prompt 33:")
            print(f"  Prompt: {p}")
            print(f"  Refs: {item.get('image_references')}")
        if p.startswith('087 ') or p.startswith('87 ') or p.startswith('087-') or p.startswith('87-'):
            print(f"[{db_name}] Prompt 87:")
            print(f"  Prompt: {p}")
            print(f"  Refs: {item.get('image_references')}")
