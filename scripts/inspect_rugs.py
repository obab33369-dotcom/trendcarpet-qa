import json

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"

with open(DB_PATH, "r", encoding="utf-8") as f:
    database = json.load(f)

rug_keywords = ["matta", "carpet", "rug", "ull", "rya", "flatweave", "jute", "jut", "bomull", "slatva"]
matching = []
for fname in database.keys():
    for kw in rug_keywords:
        if kw in fname.lower():
            matching.append(fname)
            break

print(f"Total matching filenames for rug keywords: {len(matching)}")
for fname in matching:
    print(fname)
