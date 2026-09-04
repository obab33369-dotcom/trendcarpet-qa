import os
import json
import re
import glob
from PIL import Image

COMPLETED_PATH = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\scratch\completed_skus.json"
CACHE_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\classification_cache.json"
ZOOM_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_studio_only\artiklar\zoom"

def find_info_in_cache(cache, sku, slot):
    prefix = f"type_{sku}_{slot}_"
    matches = [k for k in cache.keys() if k.startswith(prefix)]
    if matches:
        key = matches[0]
        sig = key[len(prefix):]
        type_val = cache.get(key)
        zoom_val = cache.get(f"zoom_{sku}_{slot}_{sig}")
        bg_val = cache.get(f"has_white_bg_{sku}_{slot}_{sig}")
        return type_val, zoom_val, bg_val
        
    fallback = f"type_{sku}_{slot}"
    if fallback in cache:
        type_val = cache[fallback]
        zoom_val = cache.get(f"zoom_{sku}_{slot}")
        bg_val = cache.get(f"has_white_bg_{sku}_{slot}")
        return type_val, zoom_val, bg_val
        
    return None, None, None

def main():
    if not os.path.exists(COMPLETED_PATH):
        print("completed_skus.json not found.")
        return
    if not os.path.exists(CACHE_PATH):
        print("classification_cache.json not found.")
        return
    if not os.path.exists(ZOOM_DIR):
        print("Zoom directory not found.")
        return

    with open(COMPLETED_PATH, 'r', encoding='utf-8') as f:
        completed = set(json.load(f))
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    files = [f for f in os.listdir(ZOOM_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    print(f"Total zoom images in output: {len(files)}")

    reset_skus = set()
    deleted_files_count = 0

    for f in files:
        fpath = os.path.join(ZOOM_DIR, f)
        try:
            with Image.open(fpath) as img:
                w, h = img.size
                if w != h:
                    m = re.match(r"^(.+?)_(\d+)\.(jpg|jpeg|png|webp)$", f, re.IGNORECASE)
                    if m:
                        sku = m.group(1)
                        slot = int(m.group(2))
                        img_type, is_zoom_view, has_white_bg = find_info_in_cache(cache, sku, slot)
                        
                        is_studio_view = (img_type == "studio") or (has_white_bg == True)
                        
                        # If it is a studio view and not zoom, it should be square
                        if is_studio_view and (is_zoom_view is not True):
                            print(f"Non-square studio image: {f} ({w}x{h}) type={img_type} zoom={is_zoom_view} has_white_bg={has_white_bg}")
                            reset_skus.add(sku)
                            
                            # Close image before deletion
                            img.close()
                            try:
                                os.remove(fpath)
                                deleted_files_count += 1
                            except Exception as de:
                                print(f"  Failed to delete {f}: {de}")
        except Exception as e:
            print(f"Error checking {f}: {e}")

    print(f"\nSummary:")
    print(f"  - Total SKUs identified with invalid non-square zoom outputs: {len(reset_skus)}")
    print(f"  - Total non-square zoom files deleted: {deleted_files_count}")

    if reset_skus:
        # Remove reset SKUs from completed list
        completed.difference_update(reset_skus)
        with open(COMPLETED_PATH, 'w', encoding='utf-8') as f:
            json.dump(list(completed), f, indent=2)
        print(f"Successfully updated completed_skus.json. Current completed count: {len(completed)}")
        
        # Also clean status of completed batch run so the coordinator knows to run
        status_path = r"C:\Users\AndronikLindgren\.gemini\antigravity\brain\41bee646-b445-489b-bad6-c09eca7c241b\scratch\batch_run_status.json"
        if os.path.exists(status_path):
            try:
                os.remove(status_path)
                print("Removed batch_run_status.json to reset the batch runner state.")
            except Exception:
                pass
    else:
        print("No SKUs need to be reset.")

if __name__ == "__main__":
    main()
