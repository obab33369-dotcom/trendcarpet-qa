import os
from PIL import Image
import numpy as np

src_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\reforma_original_images_by_product\Soffbord 'Prime' L - Valnöt (1310-L-S)\artiklar\zoom\1310-L-S_8.jpg"
out_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\26-06-18-FTP-Remaining\artiklar\zoom\1310-L-S_8.jpg"

if os.path.exists(src_path) and os.path.exists(out_path):
    with Image.open(src_path) as src, Image.open(out_path) as out:
        # Resize source to output dimensions for pixel-level comparison
        src_resized = src.resize(out.size, Image.Resampling.LANCZOS)
        
        arr_src = np.array(src_resized.convert('RGB')).astype(np.float32)
        arr_out = np.array(out.convert('RGB')).astype(np.float32)
        
        diff = np.abs(arr_src - arr_out)
        mean_diff = np.mean(diff)
        max_diff = np.max(diff)
        
        print(f"Mean pixel difference: {mean_diff:.4f}")
        print(f"Max pixel difference: {max_diff:.4f}")
        
        if mean_diff < 5.0:
            print("SUCCESS: The output image is virtually identical to the resized source (no crop applied).")
        else:
            print("WARNING: The output image is DIFFERENT from the resized source! (Crop or composition was applied).")
else:
    print("Files not found")
