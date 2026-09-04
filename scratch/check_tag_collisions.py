import json
import os
import re

# Exact implementation of get_short_tag from python generator
def get_short_tag(filename: str) -> str:
    # Mimic windows-1252 corruption
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

# Collect all unique image references across all prompt entries
all_refs = set()
for item in db:
    refs = [r.strip() for r in item.get('image_references', '').split(';') if r.strip()]
    for r in refs:
        all_refs.add(r)

print(f"Total unique image references: {len(all_refs)}")

# Group filenames by their short tag
tag_to_filenames = {}
for ref in all_refs:
    tag = get_short_tag(ref)
    if tag not in tag_to_filenames:
        tag_to_filenames[tag] = []
    tag_to_filenames[tag].append(ref)

# Find collisions
collisions = {tag: files for tag, files in tag_to_filenames.items() if len(files) > 1}

print(f"Total short tags: {len(tag_to_filenames)}")
print(f"Number of colliding tags: {len(collisions)}")
print("\n=== COLLISION DETAILS ===")
for tag, files in sorted(collisions.items()):
    print(f"Tag: {tag} ({len(files)} files)")
    for f in sorted(files):
        print(f"  - {f}")
    print("-" * 50)
