with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(r'scratch\reforma-turboflow', r'scratch\Projects\REFORMA\reforma-turboflow')

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
