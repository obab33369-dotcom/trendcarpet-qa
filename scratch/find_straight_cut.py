import os
from PIL import Image
import numpy as np

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected\artiklar\19791.jpg"

if not os.path.exists(img_path):
    print("Output image not found.")
else:
    with Image.open(img_path) as img:
        img_np = np.array(img.convert('RGB')).astype(np.float32)
        H, W, _ = img_np.shape
        
        # Check for any vertical line where columns to the left are all 255 (or very close)
        # and column itself is not 255.
        gray = np.mean(img_np, axis=2)
        
        # We look at y from 60% to 98%
        y_start = int(H * 0.60)
        y_end = int(H * 0.98)
        
        print(f"Scanning y={y_start} to {y_end}...")
        
        # For each column x from 10 to W/2
        for x in range(10, int(W/2)):
            # Check if column x has some dark pixels (shadow), say brightness < 240
            col_vals = gray[y_start:y_end, x]
            dark_pixels = np.sum(col_vals < 245)
            
            if dark_pixels > 20: # has a shadow here
                # Check if the column x-1 is almost purely white (brightness > 254)
                col_left = gray[y_start:y_end, x-1]
                white_pixels = np.sum(col_left >= 254.8)
                
                # If column x-1 is almost purely white, we have a straight vertical cut!
                if white_pixels > 0.8 * (y_end - y_start):
                    print(f"Detected vertical shadow cut at column x={x}!")
                    print(f"  Column {x-1} has {white_pixels} white pixels out of {y_end - y_start}")
                    print(f"  Column {x} has {dark_pixels} dark pixels")
                    
                    # Print sample values across columns for a row that has the cut
                    for y in range(y_start, y_end):
                        if col_left[y - y_start] >= 254.8 and col_vals[y - y_start] < 245:
                            print(f"  At y={y}: x={x-3} to {x+3}: {gray[y, x-3:x+4]}")
                            break
                    break
        else:
            print("No straight vertical shadow cut detected in bottom-left.")
            
        # Let's also check if there is a bottom cut (horizontal cut)
        for y in range(int(H*0.8), H-1):
            row_vals = gray[y, :]
            dark_pixels = np.sum(row_vals < 245)
            if dark_pixels > 20:
                row_below = gray[y+1, :]
                white_pixels = np.sum(row_below >= 254.8)
                if white_pixels > 0.8 * W:
                    print(f"Detected horizontal shadow cut at row y={y}!")
                    break
        else:
            print("No straight horizontal shadow cut detected near bottom.")
