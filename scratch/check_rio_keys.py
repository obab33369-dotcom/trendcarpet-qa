import json
import os

cache_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\classification_cache.json"

with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

sku = "Rio-1-rigth-Grace01"
print(f"Keys matching '{sku}':")
matched = {k: v for k, v in cache.items() if sku in k}
for k, v in sorted(matched.items()):
    print(f"  {k}: {v}")
