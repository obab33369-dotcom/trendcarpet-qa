import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def find_exact_indices(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        db = json.load(f)
    results = []
    for item in db:
        prompt = item.get("prompt", "")
        img_refs = item.get("image_references", "")
        m = re.match(r"^(\d+)\s*-", prompt)
        if m:
            idx = int(m.group(1))
            # Check references and text
            if "0108" in img_refs or "1397" in img_refs or "mlm-502580-lightgrey" in img_refs.lower():
                results.append((idx, prompt[:100], img_refs))
    return results

for dbname in ["rooms_turboflow_batch1.json", "rooms_turboflow_batch2.json", "rooms_turboflow_full_catalog.json"]:
    print(f"\n=== Exact Texas Sofa (lightgrey/lucca) in {dbname} ===")
    matches = find_exact_indices(dbname)
    print(f"Total matches: {len(matches)}")
    print(f"Indices: {[m[0] for m in matches]}")
    for m in matches[:5]:
        print(f"  {m[0]}: {m[1]}... | Refs: {m[2]}")
