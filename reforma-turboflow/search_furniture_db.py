import json
import os

files = ["furniture_db.json", "furniture_db_batch3.json"]

print("--- FURNITURE DB SEARCH ---")
for fn in files:
    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"\nFile: {fn}")
        count = 0
        for k, v in data.items():
            if "montmartre" in k.lower() or "montmartre" in str(v).lower():
                print(f"  Key: {repr(k)}")
                print(f"    Val: {repr(v)[:200]}...")
                count += 1
                if count >= 10:
                    print("  ... truncated ...")
                    break
    else:
        print(f"File {fn} not found.")
