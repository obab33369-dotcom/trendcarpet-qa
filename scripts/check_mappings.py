import json
import os
import re

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
ROOMS_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow.json"

if not os.path.exists(DB_PATH) or not os.path.exists(ROOMS_PATH):
    print("Files not found")
else:
    # Load data
    with open(DB_PATH, "r", encoding="utf-8") as f:
        furniture_db = json.load(f)
    with open(ROOMS_PATH, "r", encoding="utf-8") as f:
        rooms = json.load(f)
        
    print(f"Loaded {len(furniture_db)} furniture items and {len(rooms)} room packages.")
    
    # Let's map 4-digit ID to clean name
    id_to_name = {}
    for key in furniture_db.keys():
        parts = key.split('_', 1)
        if len(parts) >= 2:
            item_id = parts[0]
            rest = parts[1]
            name_part = os.path.splitext(rest)[0]
            # Clean name
            clean_name = re.sub(r'-1-[A-Za-z0-9]+-wonder$', '', name_part)
            clean_name = re.sub(r'-1-\w+-\w+$', '', clean_name)
            clean_name = re.sub(r'-\d+-\w+-\w+$', '', clean_name)
            
            id_to_name[item_id] = clean_name
            
    print(f"Mapped {len(id_to_name)} IDs to names.")
    
    # Test checking if any tag in rooms is missing from id_to_name
    missing_tags = set()
    for idx, r in enumerate(rooms):
        tags_str = r.get("image_tags", "")
        # Tags are like "@0440; @0001; @0124; @2002"
        tags = [t.strip().replace("@", "") for t in tags_str.split(";") if t.strip()]
        for tag in tags:
            if tag not in id_to_name:
                missing_tags.add(tag)
                
    print(f"Missing tags in id_to_name: {missing_tags}")
    
    # Let's inspect some of these missing tags in the raw furniture_db
    print("Checking if any key starts with missing tag:")
    for tag in sorted(missing_tags):
        matching_keys = [k for k in furniture_db.keys() if k.startswith(tag)]
        print(f"  Tag {tag}: {matching_keys}")
