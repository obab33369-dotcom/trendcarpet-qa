import json

db_files = ['furniture_db.json', 'furniture_db_batch2.json', 'furniture_db_batch3.json', 'brand_sku_dict.json']
for db_file in db_files:
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\n{db_file}:")
            for k in data.keys():
                if "0303" in k or "0214" in k:
                    print(f"  Key: {k}")
    except Exception as e:
        print(f"Could not load {db_file}: {e}")
