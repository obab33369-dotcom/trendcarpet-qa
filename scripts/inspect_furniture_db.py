import json
import os

DB_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\scratch\reforma-turboflow\furniture_db.json"

if not os.path.exists(DB_PATH):
    print(f"File not found: {DB_PATH}")
else:
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Type of data:", type(data))
    if isinstance(data, dict):
        print("Keys:", list(data.keys())[:10])
        # Print a sample entry
        first_key = list(data.keys())[0]
        print(f"Sample entry for '{first_key}':")
        print(json.dumps(data[first_key], indent=2, ensure_ascii=False))
    elif isinstance(data, list):
        print("Length:", len(data))
        print("Sample entry:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
