import os
import json
from PIL import Image

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

print("Checking bounding box coordinates database:")
if os.path.exists(bbox_path):
    with open(bbox_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    for key, bbox in db.items():
        if "1091-white-pigmented" in key or "19791" in key:
            print(f"  {key}: {bbox}")
else:
    print("BBox database not found.")

# Let's inspect the dimensions of the source image used for slot 1
src_img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\Refoma chair\1 Stol _Astrid_ - Vitpigmenterad\1 Stol _Astrid_ - Vitpigmenterad-01-W.jpg"
if os.path.exists(src_img_path):
    with Image.open(src_img_path) as img:
        print(f"\nSource image size: {img.size}")
else:
    print(f"\nSource image not found: {src_img_path}")
