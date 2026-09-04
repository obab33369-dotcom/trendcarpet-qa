import os
from PIL import Image
import numpy as np

corr_path = r"c:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\backup_before_correction\1091-white-pigmented_2.jpg"
if not os.path.exists(corr_path):
    corr_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\scratch\test_chair_corrected.jpg"

with Image.open(corr_path) as img:
    W, H = img.size
    img_np = np.array(img).astype(np.float32)
    print(f"Corrected image dimensions: {W}x{H}")
    
    # Let's find the vertical projection of non-white pixels
    # pure white is 255. Let's use a threshold of 250
    non_white = np.mean(img_np, axis=2) < 250
    
    # Project vertically (find rows containing non-white pixels)
    row_has_product = np.any(non_white, axis=1)
    
    rows = np.where(row_has_product)[0]
    if rows.size > 0:
        ymin_px = rows[0]
        ymax_px = rows[-1]
        print(f"Actual product pixel bounds: ymin={ymin_px} ({ymin_px/H:.3f}), ymax={ymax_px} ({ymax_px/H:.3f})")
        print(f"Actual product height pct: {(ymax_px - ymin_px)/H:.3f}")
    else:
        print("No product pixels found under threshold 250!")
