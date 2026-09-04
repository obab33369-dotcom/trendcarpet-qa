import json
import os

path = "sku_map.json"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k in data:
        if "portofino" in k.lower() or "t8049" in k.lower():
            print(f"Key: {k}")
            print(f"  Info: {data[k]}")
else:
    print("sku_map.json does not exist")
