with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# We need to remove the tracking_rows.append that refers to shot2_num
content = re.sub(r'        tracking_rows\.append\(\{\n            \"Row Number\": shot2_num,.*?        \}\)\n', '', content, flags=re.DOTALL)

with open('generate_full_catalog_rooms.py', 'w', encoding='utf-8') as f:
    f.write(content)
