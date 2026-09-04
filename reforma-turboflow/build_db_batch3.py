import os
import json

source_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\Export_WebP"
out_file = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\furniture_db_batch3.json"

db = {}
if os.path.exists(source_dir):
    for f in os.listdir(source_dir):
        if f.endswith('.webp') or f.endswith('.png'):
            db[f] = {
                "filename": f,
                "parsed_name": f,
                "metadata": {},
                "timestamp": 123456789
            }

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print(f"Created db with {len(db)} items!")
