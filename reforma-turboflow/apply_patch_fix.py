import os
import json

def patch_file():
    target = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\generate_full_catalog_rooms.py"
    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = """    filtered_db = {}
    for k, v in db.items():
        title = parse_filename_to_title(k).lower().strip()"""

    new_code = """    filtered_db = {}
    for k, v in db.items():
        title = clean_tag_to_name(k).lower().strip()"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patch applied successfully.")
    else:
        print("Patch failed: old code not found.")

if __name__ == "__main__":
    patch_file()
