import os
import json

def patch_file():
    target = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\generate_full_catalog_rooms.py"
    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = """    for k, v in brand_db.items():
        if k not in db and not should_skip_item(k):
            db[k] = {'metadata': {}, 'url': v.get('url'), 'filename': k}"""

    new_code = """    for k, v in brand_db.items():
        if k not in db and not should_skip_item(k):
            db[k] = {'metadata': {}, 'url': v.get('url'), 'filename': k}
            
    # Remove items already generated in turboflow
    done_dir = r"C:\\Users\\AndronikLindgren\\OneDrive - CaMa Gruppen AB\\Pictures\\turboflow\\sorterat_efter_mobel_1x1_2000px"
    done_titles = set()
    if os.path.exists(done_dir):
        for name in os.listdir(done_dir):
            if os.path.isdir(os.path.join(done_dir, name)):
                done_titles.add(name.lower().strip())
                
    filtered_db = {}
    for k, v in db.items():
        title = parse_filename_to_title(k).lower().strip()
        if title not in done_titles:
            filtered_db[k] = v
    print(f"Filtered out {len(db) - len(filtered_db)} items that were already generated.")
    db = filtered_db"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patch applied successfully.")
    else:
        print("Patch failed: old code not found.")

if __name__ == "__main__":
    patch_file()
