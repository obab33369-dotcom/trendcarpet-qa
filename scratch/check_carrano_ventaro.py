import json
import os
import re

db_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_full_catalog.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

# Find all entries where the prompt mentions Carrano (RG01-71, RG01-70, RG01-72) or if there are other rug indices
carrano_indices = []
ventaro_indices = []

for item in db:
    prompt = item.get("prompt", "")
    m = re.match(r"^(\d+)\s*-\s*", prompt)
    if not m:
        continue
    idx = int(m.group(1))
    
    if "carrano" in prompt.lower():
        carrano_indices.append((idx, prompt, item.get("image_references")))
    if "ventaro" in prompt.lower():
        ventaro_indices.append((idx, prompt, item.get("image_references")))

print(f"Total Carrano entries in DB: {len(carrano_indices)}")
for idx, prompt, refs in carrano_indices[:10]:
    print(f"  Index {idx}: Refs={refs}")
if len(carrano_indices) > 10:
    print(f"  ... and {len(carrano_indices)-10} more.")

print(f"\nTotal Ventaro entries in DB: {len(ventaro_indices)}")
for idx, prompt, refs in ventaro_indices[:10]:
    print(f"  Index {idx}: Refs={refs}")
if len(ventaro_indices) > 10:
    print(f"  ... and {len(ventaro_indices)-10} more.")
