import os
import json

project_dir = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA"
cache_path = os.path.join(project_dir, "scratch", "classification_cache.json")
bbox_path = os.path.join(project_dir, "scratch", "bbox_coordinates_db.json")

def print_keys(file_path, title):
    print(f"\n=== Keys in {title} ({file_path}) ===")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        keys = list(data.keys())
        print(f"Total keys: {len(keys)}")
        # Print first 20 keys
        for k in keys[:20]:
            print(f"  {k}")
    else:
        print("File not found.")

print_keys(cache_path, "Classification Cache")
print_keys(bbox_path, "BBox Coordinates DB")
