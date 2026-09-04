import os
import json
import re
from PIL import Image

topaz_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
bbox_db_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\bbox_coordinates_db.json"
cache_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\classification_cache.json"

if not os.path.exists(topaz_dir):
    print("Topaz directory not found")
    exit(1)

with open(bbox_db_path, "r", encoding="utf-8") as f:
    bbox_db = json.load(f)

with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

files = os.listdir(topaz_dir)
print(f"Total files in TEST TOPAZ: {len(files)}")

# Find some files and check their bbox/zoom status
count = 0
for f in files:
    if f.lower().endswith(".webp"):
        m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
        if m:
            prod_name = m.group(1)
            slot = int(m.group(2))
            
            # Let's see if we can find its bounding box in bbox_db
            # We need to construct the img_key. img_key is sku_slot_filesig.
            # Let's search bbox_db keys for prefix that matches slot and sku.
            # First, let's get the sku. We can search brand_sku_dict.json
            img_path = os.path.join(topaz_dir, f)
            print(f"\nFile: {f}")
            print(f"  Product Name: {prod_name}, Slot: {slot}")
            
            # Print dimensions
            try:
                with Image.open(img_path) as img:
                    print(f"  Dimensions: {img.size}")
            except Exception as e:
                print(f"  Failed to read dimensions: {e}")
                
            # Let's search keys in bbox_db containing the slot
            matched_keys = []
            for k in bbox_db:
                # Key format: sku_slot_filesig
                parts = k.split("_")
                if len(parts) >= 2 and parts[1] == str(slot):
                    # Check if the filesig matches
                    # Since we don't know the sku, we look for matches
                    matched_keys.append((k, bbox_db[k]))
            
            if matched_keys:
                print(f"  Matches in bbox_db:")
                for k, bbox in matched_keys:
                    print(f"    Key: {k}")
                    print(f"    BBox: {bbox}")
                    x_min, y_min, x_max, y_max = bbox
                    bbox_w = x_max - x_min
                    bbox_h = y_max - y_min
                    # Let's calculate touches
                    touches_left = (x_min <= 25)
                    touches_top = (y_min <= 25)
                    print(f"    w_p={bbox_w}, h_p={bbox_h}, touches_left={touches_left}, touches_top={touches_top}")
            else:
                print("  No matches in bbox_db")
                
            count += 1
            if count >= 15:
                break
