with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('print(f"Total items loaded: {len(raw_db)}', '# print(f"Total items loaded: {len(raw_db)}')
with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
