import json
import os

fn = "brand_sku_dict.json"
if os.path.exists(fn):
    with open(fn, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("--- ADVENT STARS SEARCH ---")
    for k, v in data.items():
        if "stjarna" in k.lower() or "advent" in k.lower() or "star" in k.lower():
            print(f"  {k} -> {v}")
else:
    print(f"File {fn} not found.")
