import sys
import json
import os

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db_batch2.json"
ENGINE_DIR = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow"

sys.path.append(ENGINE_DIR)
import engine

with open(DB_PATH, "r", encoding="utf-8") as f:
    db = json.load(f)

print(f"Total Batch 2 items loaded: {len(db)}")

cat_counts = {}
for filename, item in db.items():
    cat = engine.get_item_category(filename, item)
    cat_counts[cat] = cat_counts.get(cat, 0) + 1
    
print("\nBatch 2 Category Distribution:")
for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  • {cat}: {count}")
