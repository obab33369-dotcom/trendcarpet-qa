import os
import numpy as np
from PIL import Image

original_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Stol 'Ystad' - Ek (19791-ek)\artiklar\19791-ek.jpg"
corrected_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2\artiklar\19791-ek.jpg"

if not os.path.exists(original_path):
    print("Original path not found!")
    exit(1)

with Image.open(original_path) as img:
    img = img.convert('RGB')
    W, H = img.size
    print(f"Original image size: {W}x{H}")
    
    # Check borders
    img_np = np.array(img)
    print("Top row (middle 10 pixels):", img_np[0, W//2 - 5 : W//2 + 5])
    print("Bottom row (middle 10 pixels):", img_np[H-1, W//2 - 5 : W//2 + 5])
    print("Left column (middle 10 pixels):", img_np[H//2 - 5 : H//2 + 5, 0])
    
    # Run the same detection logic
    gray = img.convert('L')
    gray_np = np.array(gray)
    
    # Calculate background robustly
    edge_pixels = np.concatenate([
        img_np[:5, :, :].reshape(-1, 3),
        img_np[-5:, :, :].reshape(-1, 3),
        img_np[:, :5, :].reshape(-1, 3),
        img_np[:, -5:, :].reshape(-1, 3)
    ])
    sampled_bg = np.median(edge_pixels, axis=0)
    bg_val = sum(sampled_bg) / 3.0
    print(f"Sampled BG: {sampled_bg}, BG Val: {bg_val}")
    
    threshold = 254.0 if bg_val > 250.0 else (bg_val - 8.0)
    print(f"Threshold: {threshold}")
    
    non_white = gray_np < threshold
    non_white[:5, :] = False
    non_white[-5:, :] = False
    non_white[:, :5] = False
    non_white[:, -5:] = False
    
    coords = np.argwhere(non_white)
    if coords.size > 0:
        ymin = int(coords[:, 0].min())
        ymax = int(coords[:, 0].max())
        xmin = int(coords[:, 1].min())
        xmax = int(coords[:, 1].max())
        print(f"Detected bounds: y:[{ymin}, {ymax}], x:[{xmin}, {xmax}]")
    else:
        print("No bounds detected!")
        
    # Check pixels at the detected ymin and ymax
    if coords.size > 0:
        print(f"Row at y={ymin} (middle 10):", img_np[ymin, W//2 - 5 : W//2 + 5])
        print(f"Row at y={ymax} (middle 10):", img_np[ymax, W//2 - 5 : W//2 + 5])
