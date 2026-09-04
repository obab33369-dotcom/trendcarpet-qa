import os
import sys
from PIL import Image
import numpy as np

# Astrid and Ystad image paths
astrid_img = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\Refoma chair\1 Stol _Astrid_ - Vitpigmenterad\1 Stol _Astrid_ - Vitpigmenterad-01-W.jpg"
ystad_img = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\Refoma chair\15 Stol _Ystad_ - Natur_Svart\15 Stol _Ystad_ - Natur_Svart-01-W.jpg"

def analyze_image_centering(img_path, label):
    print(f"\n=== Analyzing {label} ===")
    with Image.open(img_path) as img:
        img_rgb = img.convert('RGB')
        arr = np.array(img_rgb)
        h, w, _ = arr.shape
        print(f"Size: {w}x{h}")
        
        # Test corners
        patches = [
            arr[10:20, 10:20],
            arr[10:20, -20:-10],
            arr[-20:-10, 10:20],
            arr[-20:-10, -20:-10]
        ]
        means = [np.mean(pat, axis=(0,1)) for pat in patches]
        means.sort(key=lambda c: np.sum(c))
        bg_color = np.mean(means[1:], axis=0)
        
        diff = np.sum(np.abs(arr - bg_color), axis=-1)
        # Using the same threshold as the script (diff < 25)
        mask = (diff < 25) & (arr[:,:,0] > 180) & (arr[:,:,1] > 180) & (arr[:,:,2] > 180)
        
        arr_cleaned = arr.copy()
        arr_cleaned[mask] = [255, 255, 255]
        
        product_pixels = np.any(arr_cleaned < 254, axis=-1)
        coords = np.argwhere(product_pixels)
        
        if coords.size > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            bbox_width = x_max - x_min + 1
            bbox_height = y_max - y_min + 1
            bbox_center_x = (x_min + x_max) / 2
            image_center_x = w / 2
            shift_x = bbox_center_x - image_center_x
            print(f"Bounding Box: x_min={x_min}, x_max={x_max}, y_min={y_min}, y_max={y_max}")
            print(f"Bounding Box Center X: {bbox_center_x} (Image Center X: {image_center_x}, Shift X: {shift_x:.1f}px)")
            
            # Let's count non-white pixels along columns to see if there is a shadow or edge noise
            cols_with_prod = np.sum(product_pixels, axis=0)
            # Find first and last column that has substantial product pixels (e.g. > 10 pixels to ignore noise)
            substantial_cols = np.argwhere(cols_with_prod > 15)
            if substantial_cols.size > 0:
                x_min_sub = substantial_cols.min()
                x_max_sub = substantial_cols.max()
                sub_center_x = (x_min_sub + x_max_sub) / 2
                print(f"Substantial Box (>15px): x_min={x_min_sub}, x_max={x_max_sub}, Width={x_max_sub - x_min_sub + 1}")
                print(f"Substantial Center X: {sub_center_x} (Shift X from Image Center: {sub_center_x - image_center_x:.1f}px)")
                
                # Check the first few columns
                print("Left edge column pixel counts (first 20):", list(cols_with_prod[x_min:x_min+20]))
                print("Right edge column pixel counts (last 20):", list(cols_with_prod[x_max-20:x_max]))
        else:
            print("No product detected")

analyze_image_centering(astrid_img, "Astrid Chair")
analyze_image_centering(ystad_img, "Ystad Chair")
