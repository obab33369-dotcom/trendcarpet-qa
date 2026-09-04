import os
from PIL import Image
import numpy as np

orig_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Stol 'Ystad' - SvartGrå (19791-black-oak)\artiklar\19791-black-oak.jpg"

if os.path.exists(orig_path):
    with Image.open(orig_path) as img:
        img = img.convert('L')
        img_np = np.array(img)
        print("Original Image black-oak Row 500 columns 0 to 50:")
        print(list(img_np[500, :50]))
else:
    print("Original file not found.")
