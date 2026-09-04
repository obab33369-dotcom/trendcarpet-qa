import os
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
final_file = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full", "artiklar", "zoom", "1200180_3.jpg")

if not os.path.exists(final_file):
    print("File does not exist!")
    exit(1)

with Image.open(final_file) as img:
    arr = np.array(img.convert('RGB'))
    h, w, c = arr.shape
    
    # We inspect a horizontal slice across the middle of the product height
    # Product height is from y=160 to y=1800. Let's inspect at y=800
    y = 800
    row_pixels = arr[y, :, :]
    
    print(f"Inspecting row y={y}:")
    
    # Let's find where the actual product body sits by looking for significantly dark pixels (e.g. RGB sum < 700)
    body_pixels = np.argwhere(np.sum(255 - row_pixels, axis=-1) > 100).flatten()
    if body_pixels.size > 0:
        x_min_body = body_pixels.min()
        x_max_body = body_pixels.max()
        print(f"  Dark product body bounds: x_min={x_min_body}, x_max={x_max_body}, width={x_max_body - x_min_body}")
        print(f"  Body center: {(x_min_body + x_max_body)/2.0} (deviation={(x_min_body + x_max_body)/2.0 - 1000.0}px)")
    else:
        print("  No dark body pixels found at this row.")
        
    # Let's print pixel values at key points:
    # 753 (left visual edge), 1000 (center), 1246 (right visual edge), 1500 (inside crop), 1754 (edge of crop), 1900 (canvas)
    points = [200, 500, 753, 1000, 1246, 1500, 1754, 1900]
    print("\nPixel values at specific X coordinates:")
    for x in points:
        rgb = row_pixels[x]
        print(f"  X={x:4d}: RGB={list(rgb)} (sum of diff from white={sum(255-rgb)})")
