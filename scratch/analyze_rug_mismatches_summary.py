import json
import os
import collections

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

keywords = ["seronis", "arabelle", "aravelle", "sorvento", "orlisse"]

summary = collections.defaultdict(list)

for item in db:
    prompt = item.get("prompt", "")
    image_references = item.get("image_references", "")
    
    # Identify which keyword is in the prompt text
    matched_prompt = [kw for kw in keywords if kw in prompt.lower()]
    # Identify which keyword is in the image references
    matched_refs = [kw for kw in keywords if kw in image_references.lower()]
    
    if matched_prompt or matched_refs:
        summary[tuple(matched_prompt)].append(image_references)

print("=== SUMMARY OF DATABASE MISMATCHES ===")
for prompt_kws, ref_lists in summary.items():
    print(f"Prompt mentions: {prompt_kws} ({len(ref_lists)} times)")
    # Get unique reference filenames
    unique_refs = set()
    for rl in ref_lists:
        for r in rl.split(';'):
            r = r.strip()
            if any(kw in r.lower() for kw in keywords):
                unique_refs.add(r)
    print(f"  Associated reference files in DB: {list(unique_refs)}")
    print("-" * 50)
