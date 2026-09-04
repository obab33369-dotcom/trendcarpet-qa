import os
from PIL import Image
import numpy as np

topaz_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ\0615_stol-ystad-natur-svart-1-26U-wonder.webp"

if os.path.exists(topaz_path):
    with Image.open(topaz_path) as img:
        img_np = np.array(img.convert('RGB')).astype(np.float32)
        H, W, _ = img_np.shape
        gray = np.mean(img_np, axis=2)
        
        # Check column 28
        print(f"TEST TOPAZ Column 27 (x=27) mean: {np.mean(gray[:, 27])}")
        print(f"TEST TOPAZ Column 28 (x=28) mean: {np.mean(gray[:, 28])}")
        
        # Let's check if there is a vertical cut around x=28.
        # Check y from 1600 to 2200
        col_27 = gray[1600:2200, 27]
        col_28 = gray[1600:2200, 28]
        print(f"Number of white pixels in col 27 (y=1600-2200): {np.sum(col_27 >= 254.8)}")
        print(f"Number of dark pixels in col 28 (y=1600-2200): {np.sum(col_28 < 245)}")
        
        # Check row 1975
        print(f"TEST TOPAZ Row 1974 (y=1974) mean: {np.mean(gray[1974, :])}")
        print(f"TEST TOPAZ Row 1975 (y=1975) mean: {np.mean(gray[1975, :])}")
        
        # Check if row 1975 is a horizontal cut
        row_1974 = gray[1974, 100:1500]
        row_1975 = gray[1975, 100:1500]
        print(f"Number of white pixels in row 1975 (x=100-1500): {np.sum(row_1975 >= 254.8)}")
        print(f"Number of dark pixels in row 1974 (x=100-1500): {np.sum(row_1974 < 245)}")
else:
    print("Topaz image not found.")
