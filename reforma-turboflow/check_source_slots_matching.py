import json
import re
import os

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
db_files = ['furniture_db.json', 'furniture_db_batch2.json', 'furniture_db_batch3.json']

databases = {}
for db_file in db_files:
    path = os.path.join(project_dir, db_file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            databases[db_file] = json.load(f)

def get_base_slug(filename):
    base = re.sub(r'^\d+[_-]', '', filename)
    base = re.sub(r'\.(jpg|jpeg|png|webp)$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'-\d+-\w+-wonder$', '', base)
    base = re.sub(r'-\d+$', '', base)
    return base.lower()

# Map base slug to (db_file, filename)
slug_map = {}
for db_file, db in databases.items():
    for k in db.keys():
        slug = get_base_slug(k)
        slug_map.setdefault(slug, []).append((db_file, k))

print("Duplicate products across databases with different filenames:")
duplicate_count = 0
for slug, occurrences in slug_map.items():
    # If there are different filenames for the same slug
    filenames = set(occ[1] for occ in occurrences)
    if len(filenames) > 1:
        duplicate_count += 1
        print(f"\nBase Slug: '{slug}'")
        for db_file, k in occurrences:
            print(f"  [{db_file}] {k}")

print(f"\nTotal duplicate products found: {duplicate_count}")
