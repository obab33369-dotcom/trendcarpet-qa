import os
import json

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow"
bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

print(f"Checking BBox database inside project directory ({bbox_path}):")
if os.path.exists(bbox_path):
    with open(bbox_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    found = 0
    for key, bbox in sorted(db.items()):
        if any(x in key for x in ["1091", "19791", "WD2001", "WS-8651A"]):
            print(f"  {key}: {bbox}")
            found += 1
    print(f"Total matching keys: {found}")
else:
    print("Database not found.")
