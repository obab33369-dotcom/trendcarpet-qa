import os
import json
import shutil
import re

# Paths
cache_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\classification_cache.json"
src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_fixstolar"
dest_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_fixstolar_studio_only"

# Load classification cache
print(f"Loading cache from: {cache_path}")
with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Ensure target directories exist
os.makedirs(dest_dir, exist_ok=True)
os.makedirs(os.path.join(dest_dir, "artiklar"), exist_ok=True)
os.makedirs(os.path.join(dest_dir, "artiklar", "liten"), exist_ok=True)
os.makedirs(os.path.join(dest_dir, "artiklar", "zoom"), exist_ok=True)

# Copy main folder files
src_artiklar = os.path.join(src_dir, "artiklar")
dest_artiklar = os.path.join(dest_dir, "artiklar")

print("Copying main articles images...")
main_count = 0
for item in os.listdir(src_artiklar):
    src_file = os.path.join(src_artiklar, item)
    if os.path.isfile(src_file) and item.lower().endswith(('.jpg', '.jpeg', '.png')):
        dest_file = os.path.join(dest_artiklar, item)
        shutil.copy2(src_file, dest_file)
        main_count += 1

print(f"Copied {main_count} main images.")

# Copy liten files
src_liten = os.path.join(src_artiklar, "liten")
dest_liten = os.path.join(dest_artiklar, "liten")

print("Copying thumbnail (liten) images...")
liten_count = 0
for item in os.listdir(src_liten):
    src_file = os.path.join(src_liten, item)
    if os.path.isfile(src_file) and item.lower().endswith(('.jpg', '.jpeg', '.png')):
        dest_file = os.path.join(dest_liten, item)
        shutil.copy2(src_file, dest_file)
        liten_count += 1

print(f"Copied {liten_count} thumbnail images.")

# Copy zoom files (skipping lifestyle)
src_zoom = os.path.join(src_artiklar, "zoom")
dest_zoom = os.path.join(dest_artiklar, "zoom")

print("Processing zoom images...")
zoom_copied = 0
zoom_skipped = 0
skipped_files = []

for item in os.listdir(src_zoom):
    src_file = os.path.join(src_zoom, item)
    if not os.path.isfile(src_file) or not item.lower().endswith(('.jpg', '.jpeg', '.png')):
        continue
        
    # Match filename like {sku}_{slot}.jpg
    m = re.match(r'^(.+)_(\d+)\.([a-zA-Z]+)$', item)
    if not m:
        # If filename doesn't match standard pattern, copy it to be safe
        dest_file = os.path.join(dest_zoom, item)
        shutil.copy2(src_file, dest_file)
        zoom_copied += 1
        continue
        
    sku = m.group(1)
    slot = m.group(2)
    
    # Query classification cache using prefix type_{sku}_{slot}_
    prefix = f"type_{sku}_{slot}_"
    class_val = None
    for k, v in cache.items():
        if k.startswith(prefix):
            class_val = v
            break
            
    if class_val == "lifestyle":
        zoom_skipped += 1
        skipped_files.append(item)
    else:
        dest_file = os.path.join(dest_zoom, item)
        shutil.copy2(src_file, dest_file)
        zoom_copied += 1

print(f"Zoom copy results:")
print(f"  Copied: {zoom_copied}")
print(f"  Skipped (lifestyle): {zoom_skipped}")
if skipped_files:
    print(f"Sample skipped files (up to 15): {skipped_files[:15]}")
