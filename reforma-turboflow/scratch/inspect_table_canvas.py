import os
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full")
ZOOM_DIR = os.path.join(FTP_UPLOAD_DIR, "artiklar", "zoom")

files_to_check = ["1311-L-S_1.jpg", "1311-L-S_8.jpg", "97828_1.jpg", "97828_5.jpg"]

for f in files_to_check:
    path = os.path.join(ZOOM_DIR, f)
    if os.path.exists(path):
        with Image.open(path) as img:
            arr = np.array(img.convert('RGB'))
            diff = np.sum(np.abs(arr - 255.0), axis=-1)
            non_white = diff > 10
            coords = np.argwhere(non_white)
            if coords.size > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                w = x_max - x_min
                h = y_max - y_min
                print(f"{f}: size={img.size} | content bbox=[{x_min}, {y_min}, {x_max}, {y_max}] | width={w}, height={h} ({h/2000:.1%})")
            else:
                print(f"{f}: size={img.size} | empty canvas")
    else:
        print(f"{f} not found at {path}")
