import os
import json

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def search_text(filename, text):
    p = os.path.join(WORKSPACE_DIR, "reforma-turboflow", filename)
    with open(p, 'r', encoding='utf-8') as f:
        db = json.load(f)
    results = []
    for item in db:
        prompt = item.get("prompt", "")
        img_refs = item.get("image_references", "")
        if text.lower() in prompt.lower() or text.lower() in img_refs.lower():
            results.append({
                "prompt": prompt,
                "refs": img_refs
            })
    return results

for dbname in ["rooms_turboflow_batch1.json", "rooms_turboflow_batch2.json", "rooms_turboflow_full_catalog.json"]:
    print(f"=== Searching in {dbname} ===")
    res_texas = search_text(dbname, "texas")
    res_lucca = search_text(dbname, "lucca")
    
    unique_indices = set()
    for item in res_texas + res_lucca:
        import re
        m = re.match(r"^(\d+)", item["prompt"].strip())
        if m:
            unique_indices.add(int(m.group(1)))
            
    print(f"Found indices: {sorted(list(unique_indices))}")
    if len(unique_indices) > 0:
        print("Sample prompts:")
        for idx in sorted(list(unique_indices))[:5]:
            for item in res_texas + res_lucca:
                if item["prompt"].strip().startswith(str(idx)):
                    print(f"  {idx}: {item['prompt'][:120]}... | Refs: {item['refs']}")
                    break
