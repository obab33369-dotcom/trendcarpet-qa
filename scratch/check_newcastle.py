import os
import json

PROJECT_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def main():
    plan_path = os.path.join(PROJECT_DIR, "scratch", "furniture_redirection_plan.json")
    catalog_path = os.path.join(PROJECT_DIR, "scratch", "furniture_catalog.json")
    
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    print("NEWCASTLE-BLACK in catalog:")
    if "NEWCASTLE-BLACK" in catalog:
        print(json.dumps(catalog["NEWCASTLE-BLACK"], indent=2))
    else:
        print("Not found in catalog.")
        
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
            
        print("\nRedirection matches for NEWCASTLE-BLACK:")
        found_matches = []
        for folder, files in plan.items():
            for fn, res in files.items():
                if res.get("matched_sku") == "NEWCASTLE-BLACK":
                    found_matches.append((folder, fn, res))
                    
        print(f"Found {len(found_matches)} matches:")
        for folder, fn, res in found_matches:
            print(f"  * {folder}/{fn} -> explanation: {res.get('explanation')}")
            
    # Search the prompt databases to see which prompts reference NEWCASTLE-BLACK
    # Let's import load_db from rebuild_all_by_time
    import sys
    sys.path.append(PROJECT_DIR)
    try:
        from rebuild_all_by_time import load_db, resolve_anchor
        db = {}
        db.update(load_db("rooms_turboflow_batch1.json"))
        db.update(load_db("rooms_turboflow_batch2.json"))
        db.update(load_db("rooms_turboflow_full_catalog.json"))
        
        print("\nPrompts referencing NEWCASTLE-BLACK:")
        found_prompts = []
        for prefix, info in db.items():
            for ref in info["refs"]:
                sku, name = resolve_anchor(ref)
                if sku == "NEWCASTLE-BLACK":
                    found_prompts.append((prefix, info["prompt"], ref))
                    
        print(f"Found {len(found_prompts)} prompts:")
        for prefix, prompt, ref in found_prompts[:10]:
            print(f"  * Prefix {prefix} (Ref: {ref})")
            print(f"    Prompt: {prompt[:150]}...")
            
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    main()
