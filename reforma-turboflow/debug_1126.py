import json
from engine import get_item_category, find_matching_companion

def main():
    with open(r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json", "r", encoding="utf-8") as f:
        db = json.load(f)
        
    items_by_cat = {}
    for filename, item in db.items():
        item["filename"] = filename
        cat = get_item_category(filename, item)
        items_by_cat[cat] = items_by_cat.get(cat, []) + [item]
        
    unfeatured_ids = set(db.keys())
    seed_id = [k for k in db.keys() if "1126" in k][0]
    seed_item = db[seed_id]
    seed_cat = get_item_category(seed_id, seed_item)
    
    print(f"Seed ID: {seed_id}")
    print(f"Seed Category: {seed_cat}")
    
    exclude_ids = {seed_id}
    for relax in range(10):
        sofa = seed_item
        ac = find_matching_companion(["armchair"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
        ct = find_matching_companion(["coffeetable"], items_by_cat, unfeatured_ids, exclude_ids, seed_item, relax)
        
        print(f"Relax {relax}: sofa={sofa['filename'][:20]}, ac={ac['filename'][:20] if ac else None}, ct={ct['filename'][:20] if ct else None}")

if __name__ == "__main__":
    main()
