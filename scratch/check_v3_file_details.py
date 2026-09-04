import os
import time
from PIL import Image

v3_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v3\artiklar"

files_to_check = ["ellewd02-black.jpg", "1091-black.jpg"]

for f in files_to_check:
    path = os.path.join(v3_dir, f)
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        size = os.path.getsize(path)
        with Image.open(path) as img:
            w, h = img.size
        print(f"File: {f}")
        print(f"  Modified Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))}")
        print(f"  Size: {size} bytes")
        print(f"  Dimensions: {w}x{h}")
    else:
        print(f"File: {f} DOES NOT EXIST in {v3_dir}")
