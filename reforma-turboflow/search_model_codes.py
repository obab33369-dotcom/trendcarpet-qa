import json
import os

fn = "brand_sku_dict.json"
if os.path.exists(fn):
    with open(fn, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("--- BRAND SKU DICT MONTMARTRE SEARCH ---")
    for k, v in data.items():
        if "yd-h440b" in k.lower() or "yd-h440b" in str(v).lower() or "sm-1025k" in k.lower() or "sm-1025k" in str(v).lower():
            print(f"  {k} -> {v}")
else:
    print(f"File {fn} not found.")
