with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_load = '''    if os.path.exists("furniture_db_batch2.json"):
        with open("furniture_db_batch2.json", "r", encoding="utf-8") as f:
            db_items.update(json.load(f))'''
new_load = '''    if os.path.exists("furniture_db_batch2.json"):
        with open("furniture_db_batch2.json", "r", encoding="utf-8") as f:
            db_items.update(json.load(f))
    if os.path.exists("furniture_db_batch3.json"):
        with open("furniture_db_batch3.json", "r", encoding="utf-8") as f:
            db_items.update(json.load(f))'''

content = content.replace(old_load, new_load)

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
