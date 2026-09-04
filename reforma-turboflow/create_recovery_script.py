import json
import os
import re

with open('generate_full_catalog_rooms.py', 'r', encoding='utf-8') as f:
    script_content = f.read()

# Replace the new norm logic with the old buggy logic
old_logic = """    ex_norm = {item for item in exclude_list}
    
    # Now filter the primary products using should_skip_item and done_titles
    done_dir = r"C:\\Users\\AndronikLindgren\\OneDrive - CaMa Gruppen AB\\Pictures\\turboflow\\sorterat_efter_mobel_1x1_2000px"
    done_titles = set()
    if os.path.exists(done_dir):
        for name in os.listdir(done_dir):
            if os.path.isdir(os.path.join(done_dir, name)):
                done_titles.add(name.lower().strip())
                
    filtered_db = {}
    for k, v in primary_db.items():
        if k in ex_norm:
            continue
        title = clean_tag_to_name(k)
        if title.lower().strip() not in done_titles:
            filtered_db[k] = v
"""

start_idx = script_content.find('def norm(s):')
end_idx = script_content.find('print(f"Filtered out {len(primary_db) - len(filtered_db)}')

if start_idx != -1 and end_idx != -1:
    script_content = script_content[:start_idx] + old_logic + "\n    " + script_content[end_idx:]

with open('recover_mapping_script.py', 'w', encoding='utf-8') as f:
    f.write(script_content)
