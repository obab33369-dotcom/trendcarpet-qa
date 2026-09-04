import os
from PIL import Image
import numpy as np

topaz_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\1332_stol-ystad-svart-grå-1-26U-wonder.webp"

if os.path.exists(topaz_path):
    with Image.open(topaz_path) as img:
        img_np = np.array(img.convert('L'))
        H, W = img_np.shape
        non_white = np.where(img_np < 240)
        if len(non_white[0]) > 0:
            ymin, xmin = np.min(non_white[0]), np.min(non_white[1])
            ymax, xmax = np.max(non_white[0]), np.max(non_white[1])
            print(f"Topaz image dimensions: {W}x{H}")
            print(f"Product bounding box in pixels: y=[{ymin}, {ymax}], x=[{xmin}, {xmax}]")
            print(f"Product starts at x={xmin} pixels, which is {xmin/W:.2%} of width")
            
            # Print sample values at ymin and xmin
            print(f"Row 2000 columns {xmin-10} to {xmin+10}: {list(img_np[2000, xmin-10:xmin+10])}")
        else:
            print("No non-white pixels found.")
else:
    print("Topaz file not found.")
