import json
import os

files = ["brand_sku_dict.json", "sku_map.json"]

print("--- MONTMARTRE SEARCH RESULTS ---")
for fn in files:
    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"\nFile: {fn}")
        count = 0
        if isinstance(data, dict):
            for k, v in data.items():
                if "montmartre" in k.lower():
                    print(f"  Key: {repr(k)} -> {repr(v)}")
                    count += 1
        print(f"  Total matches in {fn}: {count}")
