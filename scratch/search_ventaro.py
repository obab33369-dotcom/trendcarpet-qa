import json
import os

plan_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\carpet_redirection_plan.json"
with open(plan_path, 'r', encoding='utf-8') as f:
    plan = json.load(f)

print("=== SEARCH RESULTS ===")
for folder, mappings in plan.items():
    for fn, item in mappings.items():
        if '3008' in fn or '3012' in fn or 'Ventaro' in folder or 'Ventaro' in str(item):
            print(f"Folder: {folder}")
            print(f"  File: {fn}")
            print(f"  Matched SKU: {item.get('matched_sku')}")
            print(f"  Matched Name: {item.get('matched_name')}")
            print(f"  Explanation: {item.get('explanation')}")
            print("-" * 50)
