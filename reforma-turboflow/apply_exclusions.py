import os, re, csv, json

folder = r'C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow'
files = os.listdir(folder)
generated_numbers = set()
for f in files:
    m = re.match(r'^(\d+)-', f)
    if m:
        generated_numbers.add(int(m.group(1)))

featured_items = set()
try:
    with open('turboflow_ready_batch1.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            row_num = i + 1
            if row_num in generated_numbers:
                refs = [x.strip() for x in row['image_references'].split(';')]
                for r in refs:
                    if r: featured_items.add(r)
except Exception as e:
    pass

# Write to exclude_list.json
with open('exclude_list.json', 'w', encoding='utf-8') as f:
    json.dump(list(featured_items), f, ensure_ascii=False, indent=2)

with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update should_skip_item to load exclude_list.json
exclude_code = '''
# Load exclusions
try:
    with open('exclude_list.json', 'r', encoding='utf-8') as f:
        exclude_list = set(json.load(f))
except:
    exclude_list = set()

def should_skip_item(filename: str) -> bool:
    if filename in exclude_list:
        return True
'''
content = re.sub(r'def should_skip_item\(filename: str\) -> bool:', exclude_code, content)

# 2. Add random.shuffle to find_matching_companion
shuffle_code = '''def find_matching_companion(allowed_cats, items_by_cat, unfeatured_ids, exclude_ids, anchor_item, relax_level):
    candidates = []
    for cat in allowed_cats:
        candidates.extend(items_by_cat.get(cat, []))
    import random
    random.shuffle(candidates)
'''
content = re.sub(r'def find_matching_companion.*?candidates\.extend\(items_by_cat\.get\(cat, \[\]\)\)', shuffle_code, content, flags=re.DOTALL)

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
