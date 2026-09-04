import os
from PIL import Image
import numpy as np

paths = [
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload\artiklar\zoom\1200180_8.jpg",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\temp_raw_images\artiklar\zoom\1200180_8.jpg",
    r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_backup\artiklar\zoom\1200180_8.jpg"
]

for path in paths:
    if os.path.exists(path):
        print("Found file:", path)
        with Image.open(path) as img:
            print("Size:", img.size)
            print("Mode:", img.mode)
            arr = np.array(img)
            # Check if there are black columns
            is_black = np.sum(arr, axis=-1) < 30
            black_cols = np.sum(is_black, axis=0)
            num_black_cols = np.sum(black_cols > 1900)
            print("Number of columns with >1900 black pixels:", num_black_cols)
            if num_black_cols > 0:
                print("First 10 black column indices:", np.where(black_cols > 1900)[0][:10].tolist())
    else:
        print("File not found:", path)
