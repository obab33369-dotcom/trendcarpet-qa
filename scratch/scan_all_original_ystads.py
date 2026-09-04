import os
from PIL import Image
import numpy as np

orig_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product"

if os.path.exists(orig_dir):
    folders = [f for f in os.listdir(orig_dir) if "19791" in f]
    print(f"Found {len(folders)} Ystad folders.")
    for folder in sorted(folders):
        folder_path = os.path.join(orig_dir, folder, "artiklar")
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg') and not '_s.' in f.lower()]
            for file in files:
                fp = os.path.join(folder_path, file)
                try:
                    with Image.open(fp) as img:
                        img_np = np.array(img.convert('L'))
                        H, W = img_np.shape
                        non_white = np.where(img_np < 240)
                        if len(non_white[0]) > 0:
                            ymin, xmin = np.min(non_white[0]), np.min(non_white[1])
                            ymax, xmax = np.max(non_white[0]), np.max(non_white[1])
                            print(f"File: {os.path.relpath(fp, orig_dir)}")
                            print(f"  Dims: {W}x{H} | BBox: y=[{ymin}, {ymax}], x=[{xmin}, {xmax}]")
                            print(f"  Left margin: {xmin}px ({xmin/W:.1%}) | Right margin: {W - xmax}px ({(W - xmax)/W:.1%})")
                except Exception as e:
                    print(f"  Error reading {file}: {e}")
