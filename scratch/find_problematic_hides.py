import os
import cv2
import numpy as np

src_dir = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2"
files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg'))]

print(f"Scanning {len(files)} files to identify the three targets...")

for f in files:
    path = os.path.join(src_dir, f)
    img = cv2.imread(path)
    if img is None:
        continue
    h, w, _ = img.shape
    # Resize to speed up
    small = cv2.resize(img, (200, 200))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    
    # Calculate average brightness of the center (where the cowhide is)
    center = gray[50:150, 50:150]
    mean_val = np.mean(center)
    
    # Calculate percentage of very dark pixels in the center (dark brown/black fur)
    dark_pixels = np.sum(center < 80) / center.size
    
    # Calculate percentage of bright pixels in the center (white fur)
    bright_pixels = np.sum(center > 180) / center.size
    
    # Print metrics for target candidates
    # Mostly white with spots: very high mean, high bright_pixels
    # Brindle: medium mean, low bright_pixels, medium dark_pixels
    # Tricolor: high contrast, mix of dark and bright
    print(f"File: {f} | Size: {w}x{h} | Mean: {mean_val:.1f} | Dark%: {dark_pixels*100:.1f}% | Bright%: {bright_pixels*100:.1f}%")
