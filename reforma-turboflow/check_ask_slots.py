import os
import numpy as np
from PIL import Image

topaz_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\TEST TOPAZ"

def analyze_img(path):
    img = Image.open(path)
    img_rgb = img.convert('RGB')
    arr = np.array(img_rgb)
    h, w, _ = arr.shape
    patches = [
        arr[10:25, 10:25],
        arr[10:25, -25:-10],
        arr[-25:-10, 10:25],
        arr[-25:-10, -25:-10]
    ]
    means = [np.mean(pat, axis=(0,1)) for pat in patches]
    means.sort(key=lambda c: np.sum(c))
    bg_color = np.mean(means[1:], axis=0)
    bg_mean = np.mean(bg_color)
    grays = [0.299*m[0] + 0.587*m[1] + 0.114*m[2] for m in means[1:]]
    std_dev = np.std(grays)
    return bg_mean, std_dev, bg_color

print("Analyzing slots for stol-ask-natur:")
for filename in sorted(os.listdir(topaz_dir)):
    if "stol-ask-natur" in filename.lower() and filename.lower().endswith('.webp'):
        path = os.path.join(topaz_dir, filename)
        mean, std, color = analyze_img(path)
        print(f"  File: {filename} -> Mean={mean:.1f}, Std={std:.2f}, Color={color.round(1)}")
