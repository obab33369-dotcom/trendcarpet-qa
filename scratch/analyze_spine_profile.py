import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def clean_mask_contours(alpha_np):
    _, thresh = cv2.threshold(alpha_np, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return alpha_np
    largest_contour = max(contours, key=cv2.contourArea)
    clean_mask = np.zeros_like(alpha_np)
    cv2.drawContours(clean_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    return clean_mask

def analyze_spine(filename, session):
    path = os.path.join(r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2", filename)
    img = Image.open(path)
    img_rgba = remove(img, session=session)
    alpha = np.array(img_rgba.split()[3])
    mask = clean_mask_contours(alpha)
    
    ys, xs = np.where(mask > 0)
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    
    x_mid = (x_min + x_max) // 2
    h = y_max - y_min + 1
    
    # We want to check the center line. Let's look at the average mask value in a small horizontal window around x_mid
    # e.g., 5% of the width on each side
    window = max(1, int((x_max - x_min) * 0.03))
    
    spine_values = []
    for y in range(y_min, y_max + 1):
        val = np.mean(mask[y, x_mid - window : x_mid + window + 1]) / 255.0
        spine_values.append(val)
        
    print(f"\n{filename}: Spine profile (top to bottom, sampled at 10 intervals):")
    for i in range(10):
        idx = int(i * (len(spine_values) - 1) / 9)
        print(f"  Pos {i*10}% (y={y_min + idx}): center_fill={spine_values[idx]:.2f}")

if __name__ == "__main__":
    session = new_session('u2net')
    for f in ["AGJM5060.JPG", "CSKG8106.JPG"]:
        analyze_spine(f, session)
