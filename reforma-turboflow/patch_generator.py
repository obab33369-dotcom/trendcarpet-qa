import re
import json

with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. DB Loading Logic
db_load_code = '''    print("Loading entire catalog...")
    with open('brand_sku_dict.json', 'r', encoding='utf-8') as f:
        brand_db = json.load(f)
    
    # We actually need the rich metadata from furniture_db and furniture_db_batch2
    db = {}
    for db_file in ['furniture_db.json', 'furniture_db_batch2.json']:
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                temp_db = json.load(f)
                for k, v in temp_db.items():
                    if not should_skip_item(k):
                        db[k] = v
        except Exception as e:
            print('Could not load', db_file)
            
    # If any brand items are missing, add them (even without rich metadata, they get 'other')
    for k, v in brand_db.items():
        if k not in db and not should_skip_item(k):
            db[k] = {'metadata': {}, 'url': v.get('url'), 'filename': k}'''

content = re.sub(r'    print\(\"Loading furniture database\.\.\.\"\).*?db\[k\] = v', db_load_code, content, flags=re.DOTALL)

# 2. Modify slots_by_room (remove background_storage and lamps)
slots_code = '''    slots_by_room = {
        "dining": [],
        "living_seating": [
            ("sofa", ["sofa"]),
            ("armchair", ["armchair"])
        ],
        "living_storage": [
            ("armchair", ["armchair"]),
            ("rug", ["rug"])
        ],
        "office": [
            ("desk_chair", ["desk_chair", "dining_chair", "armchair"])
        ],
        "bedroom": [
            ("bed", ["sofa"]),
            ("rug", ["rug"])
        ],
        "bar": [
            ("bartable", ["bartable", "dining_table"]),
            ("rug", ["rug"])
        ]
    }'''
content = re.sub(r'    slots_by_room = \{.*?    \}', slots_code, content, flags=re.DOTALL)

# 3. Update Table Lamp prompts to 'windowsill'
content = content.replace('standing on top of it"', 'placed on a windowsill in a large window"')
content = content.replace('standing on the desk corner"', 'placed on a windowsill in a large window"')
content = content.replace('resting on top of the bedside table"', 'placed on a windowsill in a large window"')

# 4. Implement dynamic armchairs (1 or 2)
ac_code = '''            if ac:
                tagged_items.append(ac)
                ac_name = clean_tag_to_name(ac["filename"])
                import random
                if random.choice([True, False]):
                    subject_parts.append(f"a beautiful elegant armchair ({ac_name})")
                else:
                    subject_parts.append(f"a pair of matching elegant armchairs ({ac_name})")'''
content = re.sub(r'            if ac:\n                tagged_items\.append\(ac\)\n                subject_parts\.append\(f"a pair of matching elegant armchairs \(\{ac_name\}\)"\)', ac_code, content)

# 5. Remove Shot 2 (Close-up Detail View)
content = re.sub(r'        # ----------------------------------------------------\n        # Shot 2: Close-up Detail View.*?        \}\)', '', content, flags=re.DOTALL)

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied.")
