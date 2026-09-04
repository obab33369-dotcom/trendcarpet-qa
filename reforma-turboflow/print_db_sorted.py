import json

db_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

sorted_keys = sorted(db.keys())
for idx, key in enumerate(sorted_keys[:30]):
    print(f"#{idx+1:03d}: {key}")
