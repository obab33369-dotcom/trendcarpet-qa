import json
import os

WORKSPACE_DIR = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
db_path = os.path.join(WORKSPACE_DIR, "reforma-turboflow", "rooms_turboflow_full_catalog.json")

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

collision_files = [
    "2014_matta-aureline-gron.jpg",
    "2023_matta-carrano-svart-vit.jpg",
    "2040_matta-forma-beige.jpg",
    "2047_matta-lorano-brun.jpg",
    "2053_matta-marionae-brun-beige.jpg",
    "2075_matta-rivetta-beige-gron.jpg",
    "2079_matta-savelle-gron.jpg",
    "2083_matta-savena-gul-gra.jpg",
    "2090_matta-sorvento-svart-gra.jpg",
    "2091_matta-striped-sand-natur-160x230.jpg",
    "2093_matta-taliana-rosa-rod.jpg",
    "2100_matta-velenna-160x230-cm-ljusbrun-beige.jpg",
    "2107_matta-ventaro-beige.jpg"
]

print("=== FINDING DB ENTRIES USING COLLISION FILES ===")
for ref_file in collision_files:
    found_indices = []
    for item in db:
        prompt = item.get("prompt", "")
        refs = item.get("image_references", "")
        
        if ref_file.lower() in refs.lower():
            import re
            m = re.match(r'^(\d+)', prompt)
            if m:
                found_indices.append(int(m.group(1)))
    
    print(f"Ref File: {ref_file}")
    print(f"  Used in database indices ({len(found_indices)} times): {found_indices}")
    print("-" * 50)
