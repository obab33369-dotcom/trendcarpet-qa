import os
from PIL import Image
import numpy as np

orig_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Stol 'Ystad' - SvartGrå (19791-black-oak)\artiklar\19791-black-oak.jpg"

if os.path.exists(orig_path):
    with Image.open(orig_path) as img:
        img_np = np.array(img.convert('L'))
        H, W = img_np.shape
        non_white = np.where(img_np < 240)
        if len(non_white[0]) > 0:
            ymin, xmin = np.min(non_white[0]), np.min(non_white[1])
            ymax, xmax = np.max(non_white[0]), np.max(non_white[1])
            print(f"Original image dimensions: {W}x{H}")
            print(f"Product bounding box in pixels: y=[{ymin}, {ymax}], x=[{xmin}, {xmax}]")
            print(f"Product starts at x={xmin} pixels, which is {xmin/W:.2%} of width")
            
            # Print sample values at ymin and xmin
            print(f"Row {ymin} columns {xmin} to {xmin+20}: {list(img_np[ymin, xmin:xmin+20])}")
            # Check bottom-most pixels
            print(f"Row {ymax} columns {xmin} to {xmin+20}: {list(img_np[ymax, xmin:xmin+20])}")
        else:
            print("No non-white pixels found.")
else:
    print("Original file not found.")
