import json
import re

json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

db_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

# Build a mapping from name (cleaned) to list of short tags
name_to_tags = {}
for filename, item in db.items():
    # Let's get clean name
    def get_short_tag(fname):
        match = re.match(r'^(\d+)_', fname)
        return f"@{match.group(1)}" if match else ""
        
    def clean_tag_to_name(fname):
        import os
        base, _ = os.path.splitext(fname)
        base = re.sub(r'^\d+__*', '', base)
        base = re.sub(r'^\d+_', '', base)
        base = re.sub(r'-\d+-\w+-wonder$', '', base)
        base = re.sub(r'-\d+$', '', base)
        base = base.replace("-", " ").replace("_", " ").title()
        # Clean Swedish chars
        replacements = {'ö': 'o', 'ä': 'a', 'å': 'a', 'Ö': 'O', 'Ä': 'A', 'Å': 'A'}
        for char, rep in replacements.items():
            base = base.replace(char, rep)
        return base
        
    name = clean_tag_to_name(filename)
    tag = get_short_tag(filename)
    name_to_tags.setdefault(name.lower(), []).append(tag)

print(f"Loaded {len(name_to_tags)} unique name-to-tags mappings.")

mismatches = 0
for idx, row in enumerate(data):
    prompt = row["prompt"]
    tags = row["image_tags"]
    # Find all items inside parentheses, e.g. (Byra Prime 6 Lador Valnot Massing)
    matches = re.findall(r'\(([^)]+)\)', prompt)
    for m in matches:
        m_clean = m.strip().lower()
        if m_clean in name_to_tags:
            expected_tags = name_to_tags[m_clean]
            # Check if any of the expected tags for this name is in the prompt's tags
            if not any(t in tags for t in expected_tags):
                print(f"MISMATCH in Row {idx+1}:")
                print(f"  Description mentions: '{m}' (expected one of {expected_tags})")
                print(f"  Tags present: {tags}")
                mismatches += 1

print(f"Total mismatches found: {mismatches}")

