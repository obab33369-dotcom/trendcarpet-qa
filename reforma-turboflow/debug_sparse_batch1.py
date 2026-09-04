import json
import re

json_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\rooms_turboflow_batch1.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

db_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

print("Checking 1-tag prompts in Batch 1:")
seeds_of_1tag = []
for idx, row in enumerate(data):
    tags = row["image_tags"].split("; ")
    tags = [t.strip() for t in tags if t.strip()]
    if len(tags) == 1:
        # Determine the seed from the tag
        ref_files = row["image_references"].split("; ")
        seed_ref = ref_files[0]
        # Let's look up this seed_ref in db
        db_entry = db.get(seed_ref)
        if db_entry:
            cat_meta = db_entry.get("metadata", {}).get("typ_av_möbel", "").strip().lower()
            seeds_of_1tag.append((seed_ref, cat_meta))
        else:
            seeds_of_1tag.append((seed_ref, "Unknown"))

from collections import Counter
c = Counter([s[1] for s in seeds_of_1tag])
print("\nCategories of seeds that lead to 1-tag prompts:")
for cat, count in c.items():
    print(f"  {cat}: {count}")

print("\nExamples of seed files that lead to 1-tag prompts:")
for s in seeds_of_1tag[:10]:
    print(f"  {s[0]} (Category: {s[1]})")
