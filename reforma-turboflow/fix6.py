with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_harmonize = '''def woods_harmonize(w1: str, w2: str) -> bool:
    if not w1 or not w2: return True
    w1, w2 = w1.strip().lower(), w2.strip().lower()
    if w1 == w2: return True
    if w1 == 'inget' or w2 == 'inget':
        return True
    neutrals = {'svart metall', 'marmor', 'vit', 'svart ek', 'svart', 'metall'}
    if w1 in neutrals or w2 in neutrals:
        return True
    light_woods = {'ek', 'ask', 'natur', 'ljus ek', 'vitlaserad ek'}
    dark_woods = {'valnöt', 'mörkbrun', 'mörk ek', 'brunt trä'}
    if w1 in light_woods and w2 in light_woods:
        return True
    if w1 in dark_woods and w2 in dark_woods:
        return True
    if w1 == 'furu' and w2 in dark_woods:
        return False
    if w2 == 'furu' and w1 in dark_woods:
        return False
    if w1 == 'furu' or w2 == 'furu':
        return True
    return False'''

import re
content = re.sub(r'def woods_harmonize.*?return False', new_harmonize, content, flags=re.DOTALL)

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
