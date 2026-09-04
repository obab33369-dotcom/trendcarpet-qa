import os
import json
import re
from PIL import Image

cache_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\classification_cache.json"
dir_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_studio_only\artiklar\zoom"

with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

files = [f for f in os.listdir(dir_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

def find_info_in_cache(sku, slot):
    type_val = None
    zoom_val = None
    bg_val = None
    
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

non_square_count = 0
results = []

for f in files:
    p = os.path.join(dir_path, f)
    try:
        with Image.open(p) as img:
            w, h = img.size
            if w != h:
                non_square_count += 1
                m = re.match(r"^(.+?)_(\d+)\.(jpg|jpeg|png|webp)$", f, re.IGNORECASE)
                if m:
                    sku = m.group(1)
                    slot = int(m.group(2))
                    t, z, bg = find_info_in_cache(sku, slot)
                    results.append({
                        "file": f,
                        "dims": f"{w}x{h}",
                        "type": t,
                        "is_zoom_view": z,
                        "has_white_bg": bg
                    })
    except Exception as e:
        pass

print(f"Total non-square images: {non_square_count}")
# Count by type
type_counts = {}
zoom_counts = {}
bg_counts = {}

for item in results:
    t = str(item["type"])
    z = str(item["is_zoom_view"])
    bg = str(item["has_white_bg"])
    
    type_counts[t] = type_counts.get(t, 0) + 1
    zoom_counts[z] = zoom_counts.get(z, 0) + 1
    bg_counts[bg] = bg_counts.get(bg, 0) + 1

print("\nBy Image Type:")
for t, count in type_counts.items():
    print(f"  - {t}: {count}")

print("\nBy is_zoom_view:")
for z, count in zoom_counts.items():
    print(f"  - {z}: {count}")

print("\nBy has_white_bg:")
for bg, count in bg_counts.items():
    print(f"  - {bg}: {count}")
    
# Show 20 examples of non-square with white background
print("\nExamples of non-square zoom images with white background:")
examples_wb = [item for item in results if item["has_white_bg"] == True]
print(f"Total non-square with white background: {len(examples_wb)}")
for item in examples_wb[:20]:
    print(f"  - {item['file']} ({item['dims']}) type={item['type']} zoom={item['is_zoom_view']}")
