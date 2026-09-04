import os
import sys
from PIL import Image
import numpy as np

# Let's inspect the curated source file for 1091-white-pigmented slot 1
curated_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\Refoma chair\1 Stol _Astrid_ - Vitpigmenterad\1 Stol _Astrid_ - Vitpigmenterad-01-W.jpg"
original_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Stol 'Astrid' - Vitpigmenterad (1091-white-pigmented)\artiklar\1091-white-pigmented.jpg"

def inspect_image(path, label):
    print(f"\n--- {label} ({path}) ---")
    if not os.path.exists(path):
        print("File not found.")
        return
    with Image.open(path) as img:
        print(f"Size: {img.size}")
        arr = np.array(img.convert('RGB'))
        # Check boundary pixels (outermost 5px) to see if there is non-white
        h, w, _ = arr.shape
        left = arr[:, :5, :]
        right = arr[:, -5:, :]
        top = arr[:5, :, :]
        bottom = arr[-5:, :, :]
        
        non_white_left = np.sum(np.any(left < 250, axis=-1))
        non_white_right = np.sum(np.any(right < 250, axis=-1))
        non_white_top = np.sum(np.any(top < 250, axis=-1))
        non_white_bottom = np.sum(np.any(bottom < 250, axis=-1))
        
        print(f"Non-white boundary pixels (value < 250):")
        print(f"  Left: {non_white_left}")
        print(f"  Right: {non_white_right}")
        print(f"  Top: {non_white_top}")
        print(f"  Bottom: {non_white_bottom}")

inspect_image(curated_path, "Curated source image (White BG Fix)")
inspect_image(original_path, "Original raw image")
