import json
import os

fn = "brand_sku_dict.json"
if os.path.exists(fn):
    with open(fn, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("--- ACIR / LIVING SEARCH ---")
    for k, v in data.items():
        if "acir" in k.lower() or "acir" in str(v).lower() or "living" in k.lower() or "living" in str(v).lower():
            print(f"  {k} -> {v}")
else:
    print(f"File {fn} not found.")
