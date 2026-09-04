import os
from PIL import Image
import numpy as np

path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Fåtölj 'Dion' - SammetRosa (1200180)\artiklar\zoom\1200180_7.jpg"
if os.path.exists(path):
    print("Found file:", path)
    with Image.open(path) as img:
        print("Size:", img.size)
        print("Mode:", img.mode)
        arr = np.array(img)
        print("Array shape:", arr.shape)
        # Check if there are black columns
        is_black = np.sum(arr, axis=-1) < 30
        black_cols = np.sum(is_black, axis=0)
        print("Black pixels per column (first 50 columns):")
        print(black_cols[:50].tolist())
        print("Black pixels per column (last 50 columns):")
        print(black_cols[-50:].tolist())
else:
    print("File not found:", path)
