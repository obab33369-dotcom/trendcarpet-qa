import os
import json

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

with open(bbox_path, "r", encoding="utf-8") as f:
    db = json.load(f)

for k in sorted(db.keys()):
    if any(x in k for x in ["WS-8651A", "WD2001", "1091", "19791"]):
        print(f"  {k}: {db[k]}")
