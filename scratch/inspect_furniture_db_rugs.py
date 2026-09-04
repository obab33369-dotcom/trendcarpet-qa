import json

db_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\furniture_db.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

print(f"Total entries in furniture_db.json: {len(db)}")

rug_items = {}
for filename, item in db.items():
    cat = item.get("typ_av_möbel", "")
    if not cat:
        # Check by Swedish keys
        cat = item.get("typ_av_m\u00f6bel", "")
    
    if cat == "matta" or cat == "rug" or "matta" in filename.lower():
        rug_items[filename] = item

print(f"Total rug items found: {len(rug_items)}")
for fn, item in list(rug_items.items())[:10]:
    print(f"Filename: {fn}")
    print(f"  SKU: {item.get('sku') or item.get('artnr')}")
    print(f"  Metadata: {item.get('metadata')}")
    print(f"  Keys: {list(item.keys())}")
    print("-" * 50)
