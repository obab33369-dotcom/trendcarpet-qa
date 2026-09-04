import os

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
generator_file = os.path.join(project_dir, "generate_full_catalog_rooms.py")

with open(generator_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "def " in line or "get_short_tag" in line:
        print(f"Line {idx}: {line.strip()}")
