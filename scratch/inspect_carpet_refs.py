import json
import os
import re

# Exact implementation of get_short_tag from python generator
def get_short_tag(filename: str) -> str:
    try:
        corrupted = filename.encode('utf-8').decode('windows-1252').lower()
    except Exception:
        corrupted = filename.lower()
    
    base = os.path.splitext(corrupted)[0]
    
    cleaned = ''
    for c in base:
        if re.match(r'[a-z0-9_-]', c):
            cleaned += c
        else:
            cleaned += '-'
            
    collapsed = re.sub(r'-+', '-', cleaned)
    truncated = collapsed[:20].strip('-')
    return f"@{truncated}"

db_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\rooms_turboflow_full_catalog.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

# Collect all unique carpet references
carpet_refs = set()
for item in db:
    refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
    for r in refs:
        if 'matta' in r.lower() or 'rug' in r.lower():
            carpet_refs.add(r)

print(f"Total unique carpet references in DB: {len(carpet_refs)}")

# Print them with their short tags
tag_map = {}
for ref in sorted(carpet_refs):
    tag = get_short_tag(ref)
    print(f"File: {ref} -> Tag: {tag}")
    if tag not in tag_map:
        tag_map[tag] = []
    tag_map[tag].append(ref)

print("\nCollisions among carpets:")
carpet_collisions = {t: fs for t, fs in tag_map.items() if len(fs) > 1}
if not carpet_collisions:
    print("None!")
else:
    for t, fs in carpet_collisions.items():
        print(f"{t}: {fs}")
