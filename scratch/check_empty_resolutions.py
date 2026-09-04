import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    import sys
    sys.path.append(WORKSPACE_DIR)
    sys.path.append(os.path.join(WORKSPACE_DIR, "scratch"))
    from rebuild_all_by_time import load_db
    from test_fixed_resolver_v2 import final_resolve_anchor
    
    db = {}
    db.update(load_db("rooms_turboflow_batch1.json"))
    db.update(load_db("rooms_turboflow_batch2.json"))
    db.update(load_db("rooms_turboflow_full_catalog.json"))
    
    keywords = ["newcastle", "blavik", "blåvik", "cardoba", "torekov"]
    found_prompts = []
    
    for prefix, info in db.items():
        prompt = info["prompt"]
        if any(k in prompt.lower() for k in keywords):
            found_prompts.append((prefix, info))
            
    print(f"Found {len(found_prompts)} prompts referencing keywords.")
    
    for prefix, info in found_prompts[:20]:
        print(f"\nPrefix {prefix}:")
        print(f"  Prompt: {info['prompt'][:100]}...")
        for ref in info["refs"]:
            sku, name = final_resolve_anchor(ref)
            print(f"    Ref: {ref} -> SKU: {sku} | Name: {name}")

if __name__ == "__main__":
    main()
