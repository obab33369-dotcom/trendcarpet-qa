import os
from PIL import Image
import numpy as np

orig_path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\turboflow\ftp_upload_cropped_full\artiklar\zoom\1091-white-pigmented_2.jpg"

with Image.open(orig_path) as img:
    W, H = img.size
    img_np = np.array(img).astype(np.float32)
    print(f"Original image size: {W}x{H}")
    
    # Check the region around the top of the chair
    # y from 25% to 45%, x from 40% to 60%
    y_start, y_end = int(0.25 * H), int(0.45 * H)
    x_start, x_end = int(0.40 * W), int(0.60 * W)
    
    region = img_np[y_start:y_end, x_start:x_end, :]
    mean_color = np.mean(region, axis=(0,1))
    min_color = np.min(region, axis=(0,1))
    max_color = np.max(region, axis=(0,1))
    
    print(f"Backrest region (y:{y_start}-{y_end}, x:{x_start}-{x_end}):")
    print(f"  Mean color: {mean_color}")
    print(f"  Min color: {min_color}")
    print(f"  Max color: {max_color}")
    
    # Let's count how many pixels are dark (e.g. < 240) vs very light (> 240)
    gray = 0.299 * region[:,:,0] + 0.587 * region[:,:,1] + 0.114 * region[:,:,2]
    total_pixels = gray.size
    light_pixels = np.sum(gray > 240)
    print(f"  Total pixels in region: {total_pixels}")
    print(f"  Light pixels (>240): {light_pixels} ({light_pixels/total_pixels:.1%})")
    print(f"  Very light pixels (>250): {np.sum(gray > 250)} ({np.sum(gray > 250)/total_pixels:.1%})")
