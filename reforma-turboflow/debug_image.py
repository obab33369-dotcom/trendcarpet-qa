import os
from PIL import Image
import numpy as np

p = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"
fn = "3260_kldhngare-alava-vit-1-26U-wonder.webp"
# Find actual filename in case of encoding issues
files = os.listdir(p)
matched_fn = [f for f in files if "alava-vit" in f and "-1-" in f][0]
img_path = os.path.join(p, matched_fn)

img = Image.open(img_path)
arr = np.array(img.convert('RGB'))
h, w, _ = arr.shape
print("Image path:", img_path)
print("Image size:", img.size)

# Sample border pixels (5px border)
border_pixels = []
border_pixels.extend(arr[0:5, :, :].reshape(-1, 3))
border_pixels.extend(arr[-5:, :, :].reshape(-1, 3))
border_pixels.extend(arr[5:-5, 0:5, :].reshape(-1, 3))
border_pixels.extend(arr[5:-5, -5:, :].reshape(-1, 3))
border_pixels = np.array(border_pixels)

mean_bg = np.mean(border_pixels, axis=0)
print("Mean BG color:", mean_bg)

# Find unique colors in border
unique_border, counts = np.unique(border_pixels, axis=0, return_counts=True)
idx = np.argsort(-counts)
print("Top 10 border colors and counts:")
for i in range(min(10, len(idx))):
    print(f"Color: {unique_border[idx[i]]}, Count: {counts[idx[i]]}")

# Let's count how many pixels are in different threshold ranges in the whole image
gray = img.convert("L")
gray_arr = np.array(gray)
print("\nGrayscale value distribution in whole image:")
for thresh in [245, 248, 250, 252, 253, 254, 255]:
    below = np.sum(gray_arr < thresh)
    total = gray_arr.size
    print(f"Gray < {thresh}: {below} pixels ({below/total*100:.2f}%)")

# Let's check how many pixels are in different threshold ranges in the border
border_gray = []
border_gray.extend(gray_arr[0:5, :].reshape(-1))
border_gray.extend(gray_arr[-5:, :].reshape(-1))
border_gray.extend(gray_arr[5:-5, 0:5].reshape(-1))
border_gray.extend(gray_arr[5:-5, -5:].reshape(-1))
border_gray = np.array(border_gray)
print("\nGrayscale value distribution in 5px border:")
for thresh in [245, 248, 250, 252, 253, 254, 255]:
    below = np.sum(border_gray < thresh)
    total = border_gray.size
    print(f"Border Gray < {thresh}: {below} pixels ({below/total*100:.2f}%)")
