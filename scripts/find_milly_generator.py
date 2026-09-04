import os

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
generator_file = os.path.join(project_dir, "generate_full_catalog_rooms.py")

with open(generator_file, 'r', encoding='utf-8') as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"milly", content, re.IGNORECASE)]
print(f"Found {len(matches)} occurrences of 'milly' in generator file.")
for m in matches:
    start = max(0, content.rfind("\n", 0, m))
    end = content.find("\n", m)
    print(content[start:end].strip())
