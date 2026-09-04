import json
import os

db_path = "scratch/bbox_coordinates_db.json"
skus = ["37281105", "98875", "1200180", "99684", "91472"]

if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    print(f"Total entries in bbox DB: {len(db)}")
    for sku in skus:
        matches = [k for k in db.keys() if sku.lower() in k.lower()]
        print(f"SKU {sku} has {len(matches)} matches in bbox DB:")
        for m in matches:
            print(f"  - {m}: {db[m]}")
else:
    print("bbox DB not found!")
