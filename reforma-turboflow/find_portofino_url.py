import json
import os

key_to_find = "fatolj-portofino-beige-boucle"

for db_file in ['furniture_db.json', 'furniture_db_batch2.json', 'furniture_db_batch3.json', 'brand_sku_dict.json']:
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if key_to_find in data:
            print(f"File: {db_file}")
            print(f"  Data: {data[key_to_find]}")
        else:
            # Check if it contains as substring
            for k in data:
                if key_to_find in k.lower():
                    print(f"File: {db_file}, key matches: {k}")
