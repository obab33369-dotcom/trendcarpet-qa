from PIL import Image
import numpy as np

orig_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\1091-white-pigmented_2.jpg"

with Image.open(orig_path) as img:
    W, H = img.size
    img_np = np.array(img).astype(np.float32)
    print(f"Original image dimensions: {W}x{H}")
    
    non_white = np.mean(img_np, axis=2) < 250
    row_has_product = np.any(non_white, axis=1)
    
    rows = np.where(row_has_product)[0]
    if rows.size > 0:
        ymin_px = rows[0]
        ymax_px = rows[-1]
        print(f"Original product pixel bounds: ymin={ymin_px} ({ymin_px/H:.3f}), ymax={ymax_px} ({ymax_px/H:.3f})")
        print(f"Original product height pct: {(ymax_px - ymin_px)/H:.3f}")
    else:
        print("No product pixels found under threshold 250!")
