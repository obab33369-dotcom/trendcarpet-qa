import os
import numpy as np
from PIL import Image

original_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Stol 'Ystad' - Ek (19791-ek)\artiklar\19791-ek.jpg"

with Image.open(original_path) as img:
    img = img.convert('RGB')
    W, H = img.size
    img_np = np.array(img)
    
    row_means = np.mean(img_np, axis=(1, 2))
    
    print("--- Detailed bottom 30 rows ---")
    for y in range(H - 30, H):
        row_min_val = np.min(np.mean(img_np[y, :, :], axis=-1))
        print(f"y={y}: avg={row_means[y]:.1f}, min_pixel_val={row_min_val:.1f}")
