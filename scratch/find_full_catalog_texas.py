import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_text_full(filename):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        db = json.load(f)
    results = []
    for item in db:
        prompt = item.get("prompt", "")
        img_refs = item.get("image_references", "")
        if "texas" in img_refs.lower() or "lucca" in img_refs.lower() or "ljusgr" in img_refs.lower() or "502580" in img_refs:
            import re
            m = re.match(r"^(\d+)", prompt.strip())
            if m:
                results.append((int(m.group(1)), prompt[:100], img_refs))
    return results

print("=== Full Catalog Search ===")
matches = search_text_full("rooms_turboflow_full_catalog.json")
print(f"Total matches: {len(matches)}")
print(f"Indices: {[m[0] for m in matches]}")
for m in matches[:10]:
    print(f"  {m[0]}: {m[1]}... | Refs: {m[2]}")
