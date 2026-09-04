import os
import json
import re

DB_PATHS = [
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_full_catalog.json",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow.json",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_batch1.json",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_batch2.json",
    r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\turboflow_ready_yesterday.json"
]

def main():
    target_prefixes = list(range(2943, 3341))
    results = {p: [] for p in target_prefixes}
    
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        print(f"Checking database: {os.path.basename(db_path)}...")
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if isinstance(data, list):
                for item in data:
                    prompt = item.get("prompt", "")
                    m = re.match(r"^(\d+)\s*-\s*", prompt)
                    if m:
                        idx = int(m.group(1))
                        if idx in results:
                            results[idx].append((os.path.basename(db_path), item))
            elif isinstance(data, dict):
                # If it's a dict, check keys first
                for k, v in data.items():
                    if k.isdigit():
                        idx = int(k)
                        if idx in results:
                            results[idx].append((os.path.basename(db_path), v))
                    # Also check if it has a prompt field inside
                    if isinstance(v, dict):
                        prompt = v.get("prompt", "")
                        m = re.match(r"^(\d+)\s*-\s*", prompt)
                        if m:
                            idx = int(m.group(1))
                            if idx in results:
                                results[idx].append((os.path.basename(db_path), v))
        except Exception as e:
            print(f"Error reading {db_path}: {e}")
            
    # Compile a list of matched prefixes and summary
    matched = {k: v for k, v in results.items() if v}
    print(f"\nMatched {len(matched)} out of {len(target_prefixes)} target prefixes.")
    
    if not matched:
        print("Still no matches found. Let's see some sample prompts:")
        for db_path in DB_PATHS:
            if not os.path.exists(db_path):
                continue
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                print(f"Sample prompts in {os.path.basename(db_path)}:")
                for i in range(min(5, len(data))):
                    print(f"  - {data[i].get('prompt')[:100]}...")
        return
        
    # Group the matches by the primary product shown in the prompt or references
    product_mapping = {}
    for idx, matches in sorted(matched.items()):
        # Try to find a good name from the prompt or image references
        db_name, item = matches[0]
        prompt = item.get("prompt", "")
        image_refs = item.get("image_references", "")
        
        # Let's extract product info from prompt
        # Usually it says "... featuring the beautiful/elegant [Product Name] ..."
        # Or let's just use the first image reference as the SKU/product identifier
        first_ref = ""
        if image_refs:
            refs = [r.strip() for r in image_refs.split(";")]
            if refs:
                first_ref = refs[0]
                
        # Clean first_ref to represent a product
        # e.g., "0079_matbord-nordisk-120x70cm-ek-1-26U-wonder.webp"
        ref_clean = first_ref
        if "_" in first_ref:
            # remove prefix like "0079_" or "0217_"
            parts = first_ref.split("_", 1)
            if parts[0].isdigit() and len(parts[0]) <= 5:
                ref_clean = parts[1]
        
        product_mapping[idx] = {
            "ref": ref_clean or "Unknown",
            "prompt_snippet": prompt[:120],
            "db": db_name
        }
        
    # Print the grouped overview
    print("\nOverview of mapped ranges:")
    current_range_start = None
    current_ref = None
    current_snippet = None
    current_db = None
    
    ranges = []
    
    for idx in sorted(product_mapping.keys()):
        info = product_mapping[idx]
        ref = info["ref"]
        snippet = info["prompt_snippet"]
        db = info["db"]
        
        if current_range_start is None:
            current_range_start = idx
            current_ref = ref
            current_snippet = snippet
            current_db = db
        elif ref != current_ref:
            ranges.append((current_range_start, idx - 1, current_ref, current_snippet, current_db))
            current_range_start = idx
            current_ref = ref
            current_snippet = snippet
            current_db = db
            
    if current_range_start is not None:
        ranges.append((current_range_start, max(product_mapping.keys()), current_ref, current_snippet, current_db))
        
    for start, end, ref, snippet, db in ranges:
        count = end - start + 1
        print(f"  Indices {start}-{end} ({count} images) -> Product Reference: {ref}")
        print(f"    Sample Prompt: {snippet}...")
        print(f"    (from {db})")

if __name__ == "__main__":
    main()
