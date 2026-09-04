import json
import os

fn = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\sku_map.json"
if not os.path.exists(fn):
    fn = "sku_map.json"

if os.path.exists(fn):
    with open(fn, "r", encoding="utf-8") as f:
        sku_map = json.load(f)
    print(f"Loaded sku_map.json from {fn}")
    count = 0
    for k, v in sku_map.items():
        if "mont" in k.lower() or "yd-" in k.lower() or "h440" in k.lower() or "marseille" in k.lower():
            print(f"  {k} -> {v}")
            count += 1
    print(f"Total matching keys in sku_map.json: {count}")
else:
    print("sku_map.json not found.")
