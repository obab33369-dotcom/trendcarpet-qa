import os
from PIL import Image
import numpy as np

dir_in_out = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-05-in-out"

def analyze_image(filepath):
    try:
        with Image.open(filepath) as img:
            img_small = img.resize((50, 50))
            arr = np.array(img_small)
            if len(arr.shape) == 3:
                avg_rgb = np.mean(arr, axis=(0, 1))
                # Grayscale stats
                gray = img.resize((50, 50)).convert('L')
                arr_g = np.array(gray)
                std = np.std(arr_g)
                return avg_rgb, std
    except Exception as e:
        pass
    return None

files = [f"B59A00{i}.JPG" for i in range(40, 47)]
for f in files:
    path = os.path.join(dir_in_out, f)
    res = analyze_image(path)
    if res:
        rgb, std = res
        print(f"{f} | Avg RGB: ({rgb[0]:.1f}, {rgb[1]:.1f}, {rgb[2]:.1f}) | StdDev: {std:.1f}")
