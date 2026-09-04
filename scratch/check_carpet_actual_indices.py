import json
import os
import re

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

carpets = {
    "aureline": "RG01-9",
    "carrano": "RG01-70",
    "forma-beige": "RG01-33",
    "lorano-brun": "RG01-77",
    "marionae": "RG01-43",
    "rivetta": "RG01-37",
    "savelle-gron": "RG01-97",
    "savena-gul": "RG01-22",
    "sorvento-svart-gra": "RG01-51",
    "striped-sand": "Jute-Striped-160.230",
    "taliana": "RG01-80",
    "velenna": "RG016",
    "ventaro-beige": "RG01-89"
}

print("=== ACTUAL CARPET INDICES IN DB ===")
for item in db:
    prompt = item.get("prompt", "")
    refs = item.get("image_references", "")
    
    for kw, sku in carpets.items():
        if kw in prompt.lower():
            m = re.match(r'^(\d+)', prompt)
            idx = int(m.group(1)) if m else None
            
            # Print the index and what reference image was linked to it
            print(f"Carpet: {kw.upper()} ({sku})")
            print(f"  DB Index: {idx}")
            print(f"  Image References linked in DB: {refs}")
            print("-" * 50)
            break
