import json
import os

for jf in ["furniture_db.json", "furniture_db_batch2.json", "furniture_db_batch3.json"]:
    if os.path.exists(jf):
        with open(jf, "r", encoding="utf-8") as f:
            db = json.load(f)
        for k in db:
            if "portofino" in k.lower():
                print(f"File: {jf}, key: {k}")
