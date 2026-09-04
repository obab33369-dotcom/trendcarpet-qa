with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

fix_woods = '''def woods_harmonize(w1: str, w2: str) -> bool:
    if not w1 or not w2: return True
    w1, w2 = w1.strip().lower(), w2.strip().lower()'''

content = content.replace('def woods_harmonize(w1: str, w2: str) -> bool:\n    w1, w2 = w1.strip().lower(), w2.strip().lower()', fix_woods)

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
