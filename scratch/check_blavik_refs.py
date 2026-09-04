import os
import json

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
    
    for prefix, info in db.items():
        prompt = info["prompt"]
        if "blavik" in prompt.lower() or "blåvik" in prompt.lower() or "torekov" in prompt.lower():
            print(f"\nPrefix {prefix}:")
            print(f"  Prompt: {prompt[:100]}...")
            for ref in info["refs"]:
                sku, name = final_resolve_anchor(ref)
                print(f"    Ref: {ref} -> SKU: {sku} | Name: {name}")

if __name__ == "__main__":
    main()
