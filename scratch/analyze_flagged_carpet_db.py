import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
prompt_db_path = os.path.join(WORKSPACE_DIR, 'reforma-turboflow', 'rooms_turboflow_full_catalog.json')

with open(prompt_db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

# The 21 flagged SKUs
flagged_skus = {
    "RG01-20": "Matta Aravelle - Multi",
    "RG01-65": "Matta Arvella - RödGrön",
    "RG01-8": "Matta Aureline - BeigeBrun",
    "RG01-9": "Matta Aureline - Grön",
    "RG01-7": "Matta Aureline BeigeGrå",
    "RG01-76": "Matta Avendo - GulBeige",
    "RG01-75": "Matta Avendo - Röd",
    "RG01-74": "Matta Belden - Grön",
    "RG01-73": "Matta Belden - Röd",
    "RG01-35": "Matta Calvera - Grå",
    "RG01-34": "Matta Calvera - Röd",
    "RG01-72": "Matta Carrano - GråVit",
    "RG01-71": "Matta Carrano - Grön",
    "RG01-70": "Matta Carrano - SvartVit",
    "RG01-91": "Matta Ventaro - GrönGul",
    "RG01-87": "Matta Ventaro - Multi",
    "RG01-90": "Matta Ventaro - RosaBrun",
    "RG002": "Matta Ängelholm - GråBlå",
    "RG00": "Matta Ängelholm - Grön",
    "RG001": "Matta Ängelholm - Mörkbrun",
    "H100017": "Ryamatta Aranga Super Soft Fur Rosa"
}

# We want to import resolve_anchor
import sys
sys.path.append(os.path.join(WORKSPACE_DIR, 'scratch'))
from execute_full_catalog_sorting import resolve_anchor

# Gather all items in DB that map to each flagged SKU
matches = {sku: [] for sku in flagged_skus}

for item in db:
    prompt = item.get('prompt', '')
    m = re.match(r'^(\d+)\s*-', prompt)
    if not m:
        continue
    idx = int(m.group(1))
    
    refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
    for ref_idx, ref in enumerate(refs):
        sku, name = resolve_anchor(ref)
        if sku in flagged_skus:
            matches[sku].append({
                "idx": idx,
                "ref_idx": ref_idx,
                "ref": ref,
                "prompt": prompt,
                "all_refs": refs
            })

for sku, name in flagged_skus.items():
    print("=" * 80)
    print(f"SKU: {sku} ({name}) - Found {len(matches[sku])} prompts:")
    # Group by ref
    by_ref = {}
    for m_item in matches[sku]:
        ref = m_item["ref"]
        by_ref[ref] = by_ref.get(ref, 0) + 1
    for ref, count in by_ref.items():
        print(f"  Ref: {ref} -> {count} times")
        # Print one example
        example = next(x for x in matches[sku] if x["ref"] == ref)
        print(f"    Example Prompt {example['idx']}: {example['prompt'][:200]}...")
        print(f"    Example Refs: {example['all_refs']}")
