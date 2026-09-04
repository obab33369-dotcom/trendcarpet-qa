import os
import numpy as np
from PIL import Image

def inspect_left_border(p_file):
    if not os.path.exists(p_file):
        print(f"File not found: {p_file}")
        return
    with Image.open(p_file) as img:
        arr = np.array(img.convert('RGB'))
        h, w, _ = arr.shape
        left_col = arr[:, 0, :]
        non_white_indices = np.where(np.any(left_col < 255, axis=-1))[0]
        print(f"\nFile: {os.path.basename(p_file)}")
        print(f"  Total non-white pixels on left column (x=0): {len(non_white_indices)}")
        if len(non_white_indices) > 0:
            print("  First 20 non-white pixel colors on left column:")
            for idx in non_white_indices[:20]:
                print(f"    y={idx}: RGB={list(left_col[idx])}")

inspect_left_border(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v4\artiklar\1200180.jpg")
inspect_left_border(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_test_corrected_v4\artiklar\zoom\1200180_1.jpg")
