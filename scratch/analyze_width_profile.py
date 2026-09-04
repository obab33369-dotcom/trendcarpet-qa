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

def main():
    session = new_session('u2net')
    path = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures\OneDrive_2026-06-10\Batch 2\AGJM5060.JPG"
    
    img = Image.open(path)
    # NO exif transpose to see raw pixel layout
    img_rgba = remove(img, session=session)
    alpha = np.array(img_rgba.split()[3])
    mask = clean_mask_contours(alpha)
    
    ys, xs = np.where(mask > 0)
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    
    h = y_max - y_min + 1
    w = x_max - x_min + 1
    
    print(f"Mask bounding box: {w}x{h}")
    
    # Divide into 10 rows
    row_h = h / 10.0
    for i in range(10):
        y_start = y_min + int(i * row_h)
        y_end = y_min + int((i + 1) * row_h)
        
        # Find all mask pixels in this vertical band
        band_xs = xs[(ys >= y_start) & (ys < y_end)]
        if len(band_xs) > 0:
            span = band_xs.max() - band_xs.min() + 1
            area = np.sum(mask[y_start:y_end, x_min:x_max+1] > 0)
            print(f"Row {i} (y={y_start} to {y_end}): Max Span = {span}, Pixel Count = {area}")

if __name__ == "__main__":
    main()
