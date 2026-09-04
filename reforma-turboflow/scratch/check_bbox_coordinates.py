import json
import os

BBOX_DB_PATH = "scratch/bbox_coordinates_db.json"

if os.path.exists(BBOX_DB_PATH):
    with open(BBOX_DB_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)
    print("Pre-calculated Bounding Boxes:")
    for key, bbox in sorted(db.items()):
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        print(f"  {key}: bbox={bbox} | width={w}, height={h} | aspect={w/h:.3f}")
else:
    print("No bounding box database found.")
