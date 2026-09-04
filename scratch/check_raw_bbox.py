import os
import numpy as np
from PIL import Image

original_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"

def measure_raw(sub_folder, f):
    p = os.path.join(original_dir, sub_folder, "artiklar", f)
    if not os.path.exists(p):
        print(f"{f} not found in {sub_folder}")
        return
    with Image.open(p) as img:
        img_np = np.array(img.convert('RGB'))
        H, W, _ = img_np.shape
        non_white = np.mean(img_np, axis=-1) < 254
        coords = np.argwhere(non_white)
        if coords.size > 0:
            ymin, xmin = coords.min(axis=0)
            ymax, xmax = coords.max(axis=0)
            w_pct = (xmax - xmin) / W
            h_pct = (ymax - ymin) / H
            print(f"RAW {f}: size={W}x{H}, box={xmax-xmin}x{ymax-ymin} (W:{w_pct*100:.1f}%, H:{h_pct*100:.1f}%)")
        else:
            print(f"RAW {f}: No product pixels found!")

measure_raw("Stol 'Ystad' - Ek (19791-ek)", "19791-ek.jpg")
measure_raw("Stol 'Ystad' - SvartGrå (19791-black-oak)", "19791-black-oak.jpg")
measure_raw("Stol 'Ystad' - Vit ekBeige (19791-white-oak)", "19791-white-oak.jpg")
