import json
import os
import sys

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
sys.path.append(os.path.join(WORKSPACE_DIR, 'scratch'))
from execute_full_catalog_sorting import resolve_anchor, load_db

full_catalog = load_db("rooms_turboflow_full_catalog.json")

if 23 in full_catalog:
    item = full_catalog[23]
    print("Index 23 entry in full_catalog:")
    print(f"  Prompt: {item['prompt']}")
    print(f"  Refs: {item['refs']}")
    
    print("\nResolving each reference:")
    for ref_idx, ref in enumerate(item['refs']):
        sku, name = resolve_anchor(ref)
        is_primary = (ref_idx == 0)
        role = "Primary" if is_primary else "Secondary"
        print(f"  Ref {ref_idx}: '{ref}' -> SKU: {sku} | Name: {name} | Role: {role}")
else:
    print("Index 23 not found in database.")
