import os
import json
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"

def get_counts(target_patterns):
    results = {}
    for db_name in ['rooms_turboflow_batch1.json', 'rooms_turboflow_batch2.json', 'rooms_turboflow_full_catalog.json']:
        path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', db_name)
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results[db_name] = []
        for item in data:
            prompt = item.get('prompt', '')
            img_refs = item.get('image_references', '')
            refs = [r.strip() for r in img_refs.split(";") if r.strip()]
            
            # Check if any of our patterns match any of the references
            for idx, ref in enumerate(refs):
                matched = False
                for pat in target_patterns:
                    if pat.lower() in ref.lower():
                        matched = True
                        break
                if matched:
                    m = re.match(r"^(\d+)", prompt)
                    prompt_idx = int(m.group(1)) if m else None
                    results[db_name].append({
                        "prompt_idx": prompt_idx,
                        "ref": ref,
                        "is_primary": (idx == 0),
                        "prompt": prompt[:100]
                    })
    return results

target_patterns = ["0108_bäddsoffa-texas-ljusgrå", "1397.png", "1397_bäddsoffa-lucca-grå"]
res = get_counts(target_patterns)

for db, matches in res.items():
    print(f"\n{db}: found {len(matches)} matches")
    primaries = [m for m in matches if m["is_primary"]]
    secondaries = [m for m in matches if not m["is_primary"]]
    print(f"  Primary: {len(primaries)}")
    print(f"  Secondary (reserv): {len(secondaries)}")
    if matches:
        print("  Sample matches:")
        for m in matches[:5]:
            print(f"    Index: {m['prompt_idx']} | Primary: {m['is_primary']} | Ref: {m['ref']}")
