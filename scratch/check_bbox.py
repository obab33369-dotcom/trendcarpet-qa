import os
import numpy as np
from PIL import Image

output_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v2\artiklar"

def measure_product(f):
    p = os.path.join(output_dir, f)
    if not os.path.exists(p):
        print(f"{f} not found")
        return
    with Image.open(p) as img:
        img_np = np.array(img.convert('RGB'))
        H, W, _ = img_np.shape
        # find non-white pixels (< 254)
        non_white = np.mean(img_np, axis=-1) < 254
        coords = np.argwhere(non_white)
        if coords.size > 0:
            ymin, xmin = coords.min(axis=0)
            ymax, xmax = coords.max(axis=0)
            w_pct = (xmax - xmin) / W
            h_pct = (ymax - ymin) / H
            print(f"{f}: size={W}x{H}, product_box={xmax-xmin}x{ymax-ymin} (W:{w_pct*100:.1f}%, H:{h_pct*100:.1f}%), y:[{ymin},{ymax}]")
        else:
            print(f"{f}: No product pixels found!")

measure_product("19791-black-oak.jpg")
measure_product("19791-ek.jpg")
measure_product("19791-white-oak.jpg")
measure_product("19791.jpg")
