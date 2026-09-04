import json
import os

cache_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\classification_cache.json"

if os.path.exists(cache_path):
    print("Loading cache...")
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    print(f"Total keys in cache: {len(cache)}")
    
    # Let's search for some keys containing "97828" or "100519"
    samples = ["97828", "100519", "0000107482"]
    for sample in samples:
        print(f"\nKeys matching '{sample}':")
        matched = {k: v for k, v in cache.items() if sample in k}
        # Print first 10 matched keys
        for k, v in list(matched.items())[:10]:
            print(f"  {k}: {v}")
else:
    print(f"Cache not found at {cache_path}")
