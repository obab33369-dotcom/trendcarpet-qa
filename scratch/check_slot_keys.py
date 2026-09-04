import json
import os

cache_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\classification_cache.json"

with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

test_keys = ["100519_7", "100519_8", "0000107482_6", "0000107482_7"]
for tk in test_keys:
    prefix = f"type_{tk}_"
    matches = {k: v for k, v in cache.items() if k.startswith(prefix)}
    print(f"Prefix '{prefix}':")
    for k, v in matches.items():
        print(f"  {k}: {v}")
