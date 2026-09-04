import json
import os

files = ["brand_sku_dict.json", "sku_map.json", "furniture_db.json"]

print("--- LOCAL DB SEARCH RESULTS ---")
for fn in files:
    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"\nFile: {fn}")
        count = 0
        if isinstance(data, dict):
            for k, v in data.items():
                if "angom" in k.lower() or "ängom" in k.lower():
                    print(f"  Key: {repr(k)} -> {repr(v)}")
                    count += 1
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                item_str = str(item).lower()
                if "angom" in item_str or "ängom" in item_str:
                    print(f"  [{idx}]: {repr(item)}")
                    count += 1
        print(f"  Total matches in {fn}: {count}")
    else:
        print(f"\nFile {fn} not found.")
