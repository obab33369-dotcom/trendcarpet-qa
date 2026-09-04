import os
from PIL import Image
import numpy as np

# Load source image
p = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
matched_fn = "3260_kldhngare-alava-vit-1-26U-wonder.webp"
# Find actual filename
files = os.listdir(p)
matched_fn = [f for f in files if "alava-vit" in f and "-1-" in f][0]
img_path = os.path.join(p, matched_fn)

img = Image.open(img_path)

# Let's run the exact logic from run_temporary_topaz_pipeline.py
# 1. load_and_ensure_size
w, h = img.size
max_dim = max(w, h)
if max_dim < 2000:
    scale = 2000.0 / max_dim
    new_w = int(w * scale)
    new_h = int(h * scale)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
else:
    img_resized = img

print("Resized size:", img_resized.size)

# 2. is_white_background
img_rgb = img_resized.convert('RGB')
arr = np.array(img_rgb)
border_pixels = []
border_pixels.extend(arr[0:5, :, :].reshape(-1, 3))
border_pixels.extend(arr[-5:, :, :].reshape(-1, 3))
border_pixels.extend(arr[5:-5, 0:5, :].reshape(-1, 3))
border_pixels.extend(arr[5:-5, -5:, :].reshape(-1, 3))
mean_val = np.mean(border_pixels)
print("Is white background mean_val:", mean_val, "-> Result:", mean_val > 245)

# 3. gray conversion and argwhere < 250
gray = img_resized.convert("L")
arr_gray = np.array(gray)
non_white_coords = np.argwhere(arr_gray < 250)
print("non_white_coords size:", non_white_coords.size)

bbox = None
if non_white_coords.size > 0:
    y_min, x_min = non_white_coords.min(axis=0)
    y_max, x_max = non_white_coords.max(axis=0)
    print("Min coordinates (y_min, x_min):", y_min, x_min)
    print("Max coordinates (y_max, x_max):", y_max, x_max)
    if (x_max - x_min > 5) and (y_max - y_min > 5):
        bbox = (x_min, y_min, x_max, y_max)

print("Computed bbox:", bbox)
if bbox:
    print("Bbox width:", bbox[2] - bbox[0], "height:", bbox[3] - bbox[1])
