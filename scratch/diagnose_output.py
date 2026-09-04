import json
import os
from PIL import Image

db_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected\review_status.json"
test_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected"

targets = [
    '19005-m', '19744-c', '19791-black-oak', '19791-ek', '19791-walnut',
    '19791-white-oak-grey', '19791-white-oak', '19791', '19798-grey',
    '2372-walnut', '9971-oak', 'adst-beige', 'adst-brown', 'adst-white',
    'alm-3065', 'ww-advent-star-white-2'
]

db = json.load(open(db_path, 'r', encoding='utf-8'))

print("=== TARGET SKU STATUSES IN DB ===")
found = 0
for key, val in sorted(db.items()):
    fn = os.path.basename(key).lower()
    for t in targets:
        sku_lower = t.lower()
        if fn.startswith(sku_lower + '.') or fn.startswith(sku_lower + '_'):
            status = val.get('status', '?')
            reason = val.get('reason', '')
            if reason:
                reason = reason[:100]
            print(f"  {key}: {status} | {reason}")
            found += 1
            break

print(f"\nFound {found} entries for target SKUs in status DB")

# Check which zoom files are NOT square
print("\n=== NON-SQUARE ZOOM FILES ===")
zoom_dir = os.path.join(test_dir, "artiklar", "zoom")
non_square = 0
for f in sorted(os.listdir(zoom_dir)):
    if f.lower().endswith('.jpg'):
        fp = os.path.join(zoom_dir, f)
        try:
            img = Image.open(fp)
            w, h = img.size
            img.close()
            if w != h:
                print(f"  {f}: {w}x{h} (NOT SQUARE)")
                non_square += 1
        except Exception as e:
            print(f"  {f}: ERROR {e}")
print(f"\nTotal non-square zoom files: {non_square}")

# Check main images that look like they haven't been processed
print("\n=== MAIN IMAGES - SHADOW CHECK ===")
art_dir = os.path.join(test_dir, "artiklar")
for f in sorted(os.listdir(art_dir)):
    if f.lower().endswith('.jpg') and os.path.isfile(os.path.join(art_dir, f)):
        fp = os.path.join(art_dir, f)
        img = Image.open(fp)
        w, h = img.size
        # Check bottom edge - is there shadow that's cut?
        # Sample bottom 5 rows
        pixels = []
        for y in range(h-5, h):
            for x in range(0, w, 10):
                pixels.append(img.getpixel((x, y)))
        avg_bottom = sum(sum(p)/3 for p in pixels) / len(pixels)
        
        # Sample top 5 rows for comparison
        pixels_top = []
        for y in range(0, 5):
            for x in range(0, w, 10):
                pixels_top.append(img.getpixel((x, y)))
        avg_top = sum(sum(p)/3 for p in pixels_top) / len(pixels_top)
        
        # Check db status
        db_key = f"artiklar/{f}"
        status = db.get(db_key, {}).get('status', 'not in db')
        
        print(f"  {f}: {w}x{h} | bottom_avg={avg_bottom:.1f} | top_avg={avg_top:.1f} | status={status}")
        img.close()
