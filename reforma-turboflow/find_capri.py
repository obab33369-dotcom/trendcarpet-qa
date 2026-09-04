import json

terms = ["alta", "elsa", "nagano", "saba", "marbleous", "forshaga", "dion", "portofino", "ebba"]
db_files = ['furniture_db.json', 'furniture_db_batch2.json', 'furniture_db_batch3.json', 'brand_sku_dict.json']

for term in terms:
    print(f"\n================= TERM: {term} =================")
    for db_file in db_files:
        try:
            with open(f"reforma-turboflow/{db_file}", "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    if term in k.lower():
                        print(f"[{db_file}] Key: {k}")
                        if "name" in v:
                            print(f"  Name: {v['name']}")
                        elif "metadata" in v and "title" in v["metadata"]:
                            print(f"  Title: {v['metadata']['title']}")
        except Exception as e:
            print(f"Error reading {db_file}: {e}")
