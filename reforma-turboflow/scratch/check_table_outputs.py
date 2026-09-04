import os
from PIL import Image
import numpy as np

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-18-FTP-Remaining\artiklar\zoom\2507-walnut_1.jpg"

if os.path.exists(img_path):
    with Image.open(img_path) as img:
        arr = np.array(img.convert('RGB'))
        diff = np.sum(np.abs(arr - 255.0), axis=-1)
        non_white = diff > 15
        coords = np.argwhere(non_white)
        if coords.size > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            print(f"Generated image dimensions: {img.size}")
            print(f"Non-white bounding box on generated image: [{x_min}, {y_min}, {x_max}, {y_max}]")
            print(f"Width: {x_max - x_min}, Height: {y_max - y_min}")
            print(f"Width % of canvas: {(x_max - x_min) / img.size[0] * 100:.2f}%")
            print(f"Height % of canvas: {(y_max - y_min) / img.size[1] * 100:.2f}%")
        else:
            print("Generated image is entirely white!")
else:
    print("Generated image not found at:", img_path)
