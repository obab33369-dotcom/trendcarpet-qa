import os

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
generator_file = os.path.join(project_dir, "generate_full_catalog_rooms.py")

with open(generator_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(390, 500):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].strip()}")
