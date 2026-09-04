import json
import os

fn = "brand_sku_dict.json"
if os.path.exists(fn):
    with open(fn, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("--- HYDRA SEARCH ---")
    for k, v in data.items():
        if "hydra" in k.lower() or "hydra" in str(v).lower():
            print(f"  {k} -> {v}")
else:
    print(f"File {fn} not found.")
