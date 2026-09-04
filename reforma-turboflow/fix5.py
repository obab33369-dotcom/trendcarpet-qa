with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('def find_matching_companion(allowed_cats,', 'def find_matching_companion(cats_to_search,')
content = content.replace('for cat in allowed_cats:', 'for cat in cats_to_search:')

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
