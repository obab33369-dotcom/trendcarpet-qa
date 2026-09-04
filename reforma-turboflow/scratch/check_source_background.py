import os
from PIL import Image
import numpy as np

img_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\Refoma white background fix\Refoma chair\1 Stol _Astrid_ - Vitpigmenterad\1 Stol _Astrid_ - Vitpigmenterad-01-W.jpg"

if not os.path.exists(img_path):
    print("File not found:", img_path)
else:
    img = Image.open(img_path)
    arr = np.array(img)
    corner = arr[0:10, 0:10]
    print("Top-left 10x10 pixel values:")
    print(corner)
    is_pure_white = np.all(corner == 255)
    print("Is pure white:", is_pure_white)
    img.close()
