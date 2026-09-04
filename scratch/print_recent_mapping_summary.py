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

OUTPUT_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\8d5a6254-fa67-462f-8b37-231337af5cec\recent_batches_mapping.md"

def clean_ref_name(ref):
    if not ref:
        return "Unknown"
    ref_clean = ref
    if "_" in ref:
        parts = ref.split("_", 1)
        if parts[0].isdigit() and len(parts[0]) <= 5:
            ref_clean = parts[1]
    # Remove extension
    ref_clean = os.path.splitext(ref_clean)[0]
    # Replace dashes/underscores with spaces and capitalize
    name = ref_clean.replace("-", " ").replace("_", " ")
    return name.title()

def main():
    target_prefixes = list(range(2943, 3341))
    matched_data = {}
    
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if isinstance(data, list):
                for item in data:
                    prompt = item.get("prompt", "")
                    m = re.match(r"^(\d+)\s*-\s*", prompt)
                    if m:
                        idx = int(m.group(1))
                        if idx in target_prefixes:
                            matched_data[idx] = (os.path.basename(db_path), item)
            elif isinstance(data, dict):
                for k, v in data.items():
                    idx = None
                    if k.isdigit():
                        idx = int(k)
                    elif isinstance(v, dict):
                        prompt = v.get("prompt", "")
                        m = re.match(r"^(\d+)\s*-\s*", prompt)
                        if m:
                            idx = int(m.group(1))
                    if idx in target_prefixes:
                        matched_data[idx] = (os.path.basename(db_path), v)
        except Exception as e:
            print(f"Error reading {db_path}: {e}")
            
    # Group ranges
    ranges = []
    current_start = None
    current_ref = None
    current_db = None
    
    for idx in sorted(target_prefixes):
        if idx in matched_data:
            db_name, item = matched_data[idx]
            image_refs = item.get("image_references", "")
            first_ref = image_refs.split(";")[0].strip() if image_refs else "Unknown"
            
            if current_start is None:
                current_start = idx
                current_ref = first_ref
                current_db = db_name
            elif first_ref != current_ref:
                ranges.append((current_start, idx - 1, current_ref, current_db))
                current_start = idx
                current_ref = first_ref
                current_db = db_name
        else:
            if current_start is not None:
                ranges.append((current_start, idx - 1, current_ref, current_db))
                current_start = None
                current_ref = None
                current_db = None
                
    if current_start is not None:
        ranges.append((current_start, 3340, current_ref, current_db))
        
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f_out:
        f_out.write("# Mapped Products for Recent Batches (2943 - 3340)\n\n")
        f_out.write("This document matches the index numbers in the user's latest downloads to actual product references and database configurations.\n\n")
        f_out.write("## Summary of Batches\n\n")
        f_out.write("| Range | Count | Primary Product / Reference | Source Database |\n")
        f_out.write("|---|---|---|---|\n")
        
        for start, end, ref, db in ranges:
            count = end - start + 1
            prod_name = clean_ref_name(ref)
            f_out.write(f"| **{start} - {end}** | {count} | {prod_name} | `{db}` |\n")
            
        f_out.write("\n\n## Detailed Product Breakdown\n\n")
        for start, end, ref, db in ranges:
            count = end - start + 1
            prod_name = clean_ref_name(ref)
            f_out.write(f"### {prod_name} (Indices {start} - {end})\n")
            f_out.write(f"- **Total Renders**: {count} images\n")
            f_out.write(f"- **Reference Image**: `{ref}`\n")
            f_out.write(f"- **Source Config**: Found in `{db}`\n\n")
            
            # Show a sample prompt from the first index in the range
            if start in matched_data:
                _, item = matched_data[start]
                prompt = item.get("prompt", "")
                f_out.write(f"> **Sample Prompt**: {prompt}\n\n")
                
    print(f"Generated report at {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
