import os
import json
import re
from PIL import Image
import numpy as np

topaz_dir = r"C:\Users\AndronikGruppen\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
# Correct OneDrive path from config
topaz_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
bbox_db_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\bbox_coordinates_db.json"

with open(bbox_db_path, "r", encoding="utf-8") as f:
    bbox_db = json.load(f)

# Find files of tables/lamps
files = os.listdir(topaz_dir)
count = 0
for f in files:
    if f.lower().endswith(".webp"):
        m = re.match(r"^\d+_(.+?)-(\d+)-26U-wonder\.webp$", f)
        if m:
            prod_name = m.group(1)
            slot = int(m.group(2))
            
            # We look for tables, desks, lamps, or chairs
            is_target = any(x in prod_name.lower() for x in ["bord", "skrivbord", "table", "desk", "lampa", "lamp", "stol", "chair"])
            if not is_target:
                continue
                
            img_path = os.path.join(topaz_dir, f)
            
            # Find in bbox_db
            matched_key = None
            for k in bbox_db:
                parts = k.split("_")
                # parts[0] is SKU, parts[1] is slot, parts[2..] is name/filesig
                if len(parts) >= 2 and parts[1] == str(slot):
                    # Check if the product name matches
                    # Since SKU is unique, let's see if we can check the file signature or just match the slot
                    # Let's check if the signature in the key matches the file size/mtime
                    try:
                        sz = os.path.getsize(img_path)
                        mtime = int(os.path.getmtime(img_path))
                        sig = f"{sz}_{mtime}"
                        if sig in k:
                            matched_key = k
                            break
                    except Exception:
                        pass
            
            if matched_key:
                bbox = bbox_db[matched_key]
                x_min, y_min, x_max, y_max = bbox
                
                # Load image and inspect actual margins
                try:
                    with Image.open(img_path) as img:
                        w, h = img.size
                        longest = max(w, h)
                        scale_init = 2000.0 / longest
                        new_w = int(w * scale_init)
                        new_h = int(h * scale_init)
                        
                        # Check actual non-white pixels in original image
                        arr = np.array(img.convert('RGB'))
                        # Background is white. Let's find how many pixels at the borders are non-white
                        top_border = arr[0, :, :]
                        bottom_border = arr[-1, :, :]
                        left_border = arr[:, 0, :]
                        right_border = arr[:, -1, :]
                        
                        # Background is typically white (255, 255, 255)
                        non_white_top = np.sum(np.sum(np.abs(top_border - 255), axis=-1) > 15)
                        non_white_bottom = np.sum(np.sum(np.abs(bottom_border - 255), axis=-1) > 15)
                        non_white_left = np.sum(np.sum(np.abs(left_border - 255), axis=-1) > 15)
                        non_white_right = np.sum(np.sum(np.abs(right_border - 255), axis=-1) > 15)
                        
                        # Bounding box limits check
                        touches_left_25 = (x_min <= 25)
                        touches_right_25 = (x_max >= new_w - 25)
                        touches_top_25 = (y_min <= 25)
                        touches_bottom_25 = (y_max >= new_h - 25)
                        
                        print(f"\nImage: {f}")
                        print(f"  Dimensions: {w}x{h} -> Resized: {new_w}x{new_h}")
                        print(f"  SAM3 BBox in database: {bbox}")
                        print(f"  BBox width: {x_max - x_min} ({100*(x_max - x_min)/new_w:.1f}% of width)")
                        print(f"  BBox height: {y_max - y_min} ({100*(y_max - y_min)/new_h:.1f}% of height)")
                        print(f"  Pipeline margin flags (25px threshold):")
                        print(f"    touches_left_25={touches_left_25} (x_min={x_min})")
                        print(f"    touches_right_25={touches_right_25} (x_max={x_max}, new_w-25={new_w-25})")
                        print(f"    touches_top_25={touches_top_25} (y_min={y_min})")
                        print(f"    touches_bottom_25={touches_bottom_25} (y_max={y_max}, new_h-25={new_h-25})")
                        print(f"  Actual non-white border pixels on 1px frame edge:")
                        print(f"    Top: {non_white_top}, Bottom: {non_white_bottom}, Left: {non_white_left}, Right: {non_white_right}")
                except Exception as e:
                    print(f"  Failed to inspect {f}: {e}")
                
                count += 1
                if count >= 8:
                    break
