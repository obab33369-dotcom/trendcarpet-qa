import os
import numpy as np
from PIL import Image

path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\3315_vinhylla-amaya-low-beige-1-26U-wonder.webp"

if os.path.exists(path):
    img = Image.open(path).convert('RGB')
    arr = np.array(img)
    h, w, _ = arr.shape
    print(f"Image shape: {arr.shape}")
    
    # Check average color in the outer borders (columns/rows 0 to 10)
    print("Outer top row (y=5):", arr[5, :20])
    print("Outer bottom row (y=h-6):", arr[h-6, :20])
    print("Outer left col (x=5):", arr[:20, 5])
    print("Outer right col (x=w-6):", arr[:20, w-6])
    
    # Check if there are columns or rows that are completely non-white
    # Let's count how many pixels are < 254 in the outer 20 pixels
    outer_left = arr[:, :20]
    outer_right = arr[:, -20:]
    outer_top = arr[:20, :]
    outer_bottom = arr[-20:, :]
    
    print("Left border < 254 count:", np.sum(outer_left < 254))
    print("Right border < 254 count:", np.sum(outer_right < 254))
    print("Top border < 254 count:", np.sum(outer_top < 254))
    print("Bottom border < 254 count:", np.sum(outer_bottom < 254))
    
    # Print a small 10x10 patch from top-left corner
    print("Top-left patch:\n", arr[0:10, 0:10, 0])
else:
    print("File not found")
