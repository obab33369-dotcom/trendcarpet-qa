import os
import json
import sys

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
search_terms = ["texas", "lucca", "502580", "1397"]

output_path = os.path.join(WORKSPACE_DIR, "scratch", "search_results.txt")

with open(output_path, "w", encoding="utf-8") as out:
    for db_name in ['rooms_turboflow_batch1.json', 'rooms_turboflow_batch2.json', 'rooms_turboflow_full_catalog.json']:
        path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', db_name)
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='latin-1') as f:
            data = json.load(f)
        
        out.write(f"=== DATABASE: {db_name} ===\n")
        for item in data:
            prompt = item.get('prompt', '')
            img_refs = item.get('image_references', '')
            for term in search_terms:
                if term in prompt.lower() or term in img_refs.lower():
                    out.write(f"Prompt: {prompt[:200]}...\n")
                    out.write(f"Refs: {img_refs}\n\n")
                    break
print("Search completed. Output written to scratch/search_results.txt")
