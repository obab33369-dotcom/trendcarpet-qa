import json
import os
import re

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"

if not os.path.exists(DB_PATH):
    print("Database not found")
else:
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Total keys: {len(data)}")
    
    cleaned_examples = {}
    for key in sorted(data.keys()):
        # Split 4-digit ID
        parts = key.split('_', 1)
        if len(parts) < 2:
            continue
        item_id, rest = parts
        
        # Remove extension
        name_part = os.path.splitext(rest)[0]
        
        # Remove suffix like '-1-26U-wonder' or similar hash
        # Let's see some patterns of name_part
        # e.g., 'lampa-senigallia-m-vit-svart-1-26U-wonder'
        # Let's remove '-1-26U-wonder' or similar using regex
        clean_name = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', name_part)
        # Also let's try another generic regex to strip the trailing hash/wonder/etc.
        clean_name_generic = re.sub(r'-1-\w+-\w+$', '', name_part)
        clean_name_generic = re.sub(r'-\d+-\w+-\w+$', '', clean_name_generic)
        
        cleaned_examples[key] = {
            "id": item_id,
            "original": key,
            "name_part": name_part,
            "clean": clean_name_generic
        }
        
    # Print the first 50 keys and their cleaned names
    for key, val in list(cleaned_examples.items())[:50]:
        print(f"ID: {val['id']} | Clean: {val['clean']} | Original: {val['original']}")
