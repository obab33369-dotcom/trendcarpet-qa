import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

search_terms = ["lucca", "texas", "mlm-502580", "1397"]

for db_name in ['rooms_turboflow_batch1.json', 'rooms_turboflow_batch2.json', 'rooms_turboflow_full_catalog.json']:
    path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', db_name)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='latin-1') as f:
        data = json.load(f)
    
    for item in data:
        prompt = item.get('prompt', '')
        img_refs = item.get('image_references', '')
        # check if any search term is in prompt or img_refs (case-insensitive)
        for term in search_terms:
            if term in prompt.lower() or term in img_refs.lower():
                print(f"Found in {db_name}:")
                print(f"  Prompt: {prompt}")
                print(f"  Refs: {img_refs}")
                break
