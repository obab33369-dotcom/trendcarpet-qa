import json
import os

fn = "brand_sku_dict.json"
if os.path.exists(fn):
    with open(fn, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("--- OSLO SEARCH ---")
    for k, v in data.items():
        if "oslo" in k.lower() or "oslo" in str(v).lower():
            print(f"  {k} -> {v}")
else:
    print(f"File {fn} not found.")
