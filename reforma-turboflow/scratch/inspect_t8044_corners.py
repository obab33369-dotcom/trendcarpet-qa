import os
import re
import numpy as np
from PIL import Image

ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")

# Check all dirs for gori or teddy
dirs_to_check = [NEW_WHITE_BG_DIR, TOPAZ_DIR, ORIG_DIR]
found = False

for base_dir in dirs_to_check:
    if not os.path.exists(base_dir):
        continue
    print(f"\nScanning base directory: {base_dir}")
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if "gori" in d.lower() or "teddy" in d.lower() or "t8044" in d.lower():
                dir_path = os.path.join(root, d)
                print(f"Found folder: {dir_path}")
                found = True
                for f in os.listdir(dir_path):
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        img_path = os.path.join(dir_path, f)
                        with Image.open(img_path) as img:
                            w, h = img.size
                            longest = max(w, h)
                            scale_init = 2000.0 / longest
                            img_resized = img.resize((int(w * scale_init), int(h * scale_init)), Image.Resampling.LANCZOS)
                            img_rgb = img_resized.convert('RGB')
                            arr = np.array(img_rgb)
                            patches = [arr[10:25, 10:25], arr[10:25, -25:-10], arr[-25:-10, 10:25], arr[-25:-10, -25:-10]]
                            means = [np.mean(pat, axis=(0,1)) for pat in patches]
                            means.sort(key=lambda c: np.sum(c))
                            bg_color = np.mean(means[1:], axis=0)
                            bg_mean = np.mean(bg_color)
                            grays = [0.299*m[0] + 0.587*m[1] + 0.114*m[2] for m in means[1:]]
                            std_dev = np.std(grays)
                            is_wb = (bg_mean > 200) and (std_dev < 20.0)
                            print(f"  File: {f}")
                            print(f"    bg_mean: {bg_mean:.2f}, std_dev: {std_dev:.2f}, is_wb: {is_wb}")
                            print(f"    bg_color: {bg_color.round(1)}")
