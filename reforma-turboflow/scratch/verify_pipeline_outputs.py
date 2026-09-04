import os
from PIL import Image
import numpy as np

OUTPUT_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar"
SKUS = ["1200180", "T8044-white", "97828", "1311-L-S", "LINK-SM11-light"]

print("==================================================")
print("      VERIFYING GENERATED IMAGES FOR TARGET SKUS  ")
print("==================================================")

if not os.path.exists(OUTPUT_DIR):
    print(f"[ERROR] Output directory does not exist: {OUTPUT_DIR}")
    exit(1)

zoom_dir = os.path.join(OUTPUT_DIR, "zoom")
liten_dir = os.path.join(OUTPUT_DIR, "liten")

all_zoom_files = os.listdir(zoom_dir) if os.path.exists(zoom_dir) else []

for sku in SKUS:
    print(f"\nSKU: {sku}")
    
    # Check main images (1000px and 400px)
    main_img_path = os.path.join(OUTPUT_DIR, f"{sku}.jpg")
    liten_img_path = os.path.join(liten_dir, f"{sku}_S.jpg")
    
    if os.path.exists(main_img_path):
        with Image.open(main_img_path) as img:
            print(f"  Main image (1000x1000): {img.size[0]}x{img.size[1]} - {'[OK]' if img.size == (1000, 1000) else '[ERROR]'}")
    else:
        print(f"  Main image: [MISSING] {main_img_path}")
        
    if os.path.exists(liten_img_path):
        with Image.open(liten_img_path) as img:
            print(f"  Liten image (400x400): {img.size[0]}x{img.size[1]} - {'[OK]' if img.size == (400, 400) else '[ERROR]'}")
    else:
        print(f"  Liten image: [MISSING] {liten_img_path}")
        
    # Check zoom images (2000px max)
    sku_zoom_files = sorted([f for f in all_zoom_files if f.startswith(sku)])
    print(f"  Zoom/Detail files found: {len(sku_zoom_files)}")
    
    for f in sku_zoom_files:
        p = os.path.join(zoom_dir, f)
        with Image.open(p) as img:
            w, h = img.size
            # A view is expected to be square 2000x2000 if it's a Studio Hero view (Slots 1-6)
            # and is expected to be rectangular if it is a detail/zoom view or lifestyle view.
            # Let's inspect the actual size.
            is_square = (w == 2000 and h == 2000)
            
            # Detect corner pixels to check if there are white borders (e.g. if we padded a lifestyle image)
            arr = np.array(img.convert('RGB'))
            corners = [arr[0, 0], arr[0, -1], arr[-1, 0], arr[-1, -1]]
            corners_white = all(np.all(c > 250) for c in corners)
            
            aspect_ratio_str = f"{w}x{h}"
            status = "Square Studio Hero" if is_square else "Bypassed Aspect Ratio (No margins)"
            
            print(f"    - {f}: Size={aspect_ratio_str} ({status})")
            if not is_square:
                print(f"      Corners are white: {corners_white}")
                
print("\nVerification complete.")
